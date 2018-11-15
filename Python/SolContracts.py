contract_source_code = '''
pragma solidity ^0.4.0;

library strings {
    struct slice {
        uint _len;
        uint _ptr;
    }

    function memcpy(uint dest, uint src, uint len) private pure {
        // Copy word-length chunks while possible
        for(; len >= 32; len -= 32) {
            assembly {
                mstore(dest, mload(src))
            }
            dest += 32;
            src += 32;
        }

        // Copy remaining bytes
        uint mask = 256 ** (32 - len) - 1;
        assembly {
            let srcpart := and(mload(src), not(mask))
            let destpart := and(mload(dest), mask)
            mstore(dest, or(destpart, srcpart))
        }
    }

    /*
     * @dev Returns a slice containing the entire string.
     * @param self The string to make a slice from.
     * @return A newly allocated slice containing the entire string.
     */
    function toSlice(string self) internal pure returns (slice) {
        uint ptr;
        assembly {
            ptr := add(self, 0x20)
        }
        return slice(bytes(self).length, ptr);
    }

    /*
     * @dev Returns the length of a null-terminated bytes32 string.
     * @param self The value to find the length of.
     * @return The length of the string, from 0 to 32.
     */
    function len(bytes32 self) internal pure returns (uint) {
        uint ret;
        if (self == 0)
            return 0;
        if (self & 0xffffffffffffffffffffffffffffffff == 0) {
            ret += 16;
            self = bytes32(uint(self) / 0x100000000000000000000000000000000);
        }
        if (self & 0xffffffffffffffff == 0) {
            ret += 8;
            self = bytes32(uint(self) / 0x10000000000000000);
        }
        if (self & 0xffffffff == 0) {
            ret += 4;
            self = bytes32(uint(self) / 0x100000000);
        }
        if (self & 0xffff == 0) {
            ret += 2;
            self = bytes32(uint(self) / 0x10000);
        }
        if (self & 0xff == 0) {
            ret += 1;
        }
        return 32 - ret;
    }

    /*
     * @dev Returns a slice containing the entire bytes32, interpreted as a
     *      null-terminated utf-8 string.
     * @param self The bytes32 value to convert to a slice.
     * @return A new slice containing the value of the input argument up to the
     *         first null.
     */
    function toSliceB32(bytes32 self) internal pure returns (slice ret) {
        // Allocate space for `self` in memory, copy it there, and point ret at it
        assembly {
            let ptr := mload(0x40)
            mstore(0x40, add(ptr, 0x20))
            mstore(ptr, self)
            mstore(add(ret, 0x20), ptr)
        }
        ret._len = len(self);
    }

    /*
     * @dev Returns a new slice containing the same data as the current slice.
     * @param self The slice to copy.
     * @return A new slice containing the same data as `self`.
     */
    function copy(slice self) internal pure returns (slice) {
        return slice(self._len, self._ptr);
    }

    /*
     * @dev Copies a slice to a new string.
     * @param self The slice to copy.
     * @return A newly allocated string containing the slice's text.
     */
    function toString(slice self) internal pure returns (string) {
        string memory ret = new string(self._len);
        uint retptr;
        assembly { retptr := add(ret, 32) }

        memcpy(retptr, self._ptr, self._len);
        return ret;
    }

    /*
     * @dev Returns the length in runes of the slice. Note that this operation
     *      takes time proportional to the length of the slice; avoid using it
     *      in loops, and call `slice.empty()` if you only need to know whether
     *      the slice is empty or not.
     * @param self The slice to operate on.
     * @return The length of the slice in runes.
     */
    function len(slice self) internal pure returns (uint l) {
        // Starting at ptr-31 means the LSB will be the byte we care about
        uint ptr = self._ptr - 31;
        uint end = ptr + self._len;
        for (l = 0; ptr < end; l++) {
            uint8 b;
            assembly { b := and(mload(ptr), 0xFF) }
            if (b < 0x80) {
                ptr += 1;
            } else if(b < 0xE0) {
                ptr += 2;
            } else if(b < 0xF0) {
                ptr += 3;
            } else if(b < 0xF8) {
                ptr += 4;
            } else if(b < 0xFC) {
                ptr += 5;
            } else {
                ptr += 6;
            }
        }
    }

    /*
     * @dev Returns true if the slice is empty (has a length of 0).
     * @param self The slice to operate on.
     * @return True if the slice is empty, False otherwise.
     */
    function empty(slice self) internal pure returns (bool) {
        return self._len == 0;
    }

    /*
     * @dev Returns a positive number if `other` comes lexicographically after
     *      `self`, a negative number if it comes before, or zero if the
     *      contents of the two slices are equal. Comparison is done per-rune,
     *      on unicode codepoints.
     * @param self The first slice to compare.
     * @param other The second slice to compare.
     * @return The result of the comparison.
     */
    function compare(slice self, slice other) internal pure returns (int) {
        uint shortest = self._len;
        if (other._len < self._len)
            shortest = other._len;

        uint selfptr = self._ptr;
        uint otherptr = other._ptr;
        for (uint idx = 0; idx < shortest; idx += 32) {
            uint a;
            uint b;
            assembly {
                a := mload(selfptr)
                b := mload(otherptr)
            }
            if (a != b) {
                // Mask out irrelevant bytes and check again
                uint256 mask = uint256(-1); // 0xffff...
                if(shortest < 32) {
                  mask = ~(2 ** (8 * (32 - shortest + idx)) - 1);
                }
                uint256 diff = (a & mask) - (b & mask);
                if (diff != 0)
                    return int(diff);
            }
            selfptr += 32;
            otherptr += 32;
        }
        return int(self._len) - int(other._len);
    }

    /*
     * @dev Returns true if the two slices contain the same text.
     * @param self The first slice to compare.
     * @param self The second slice to compare.
     * @return True if the slices are equal, false otherwise.
     */
    function equals(slice self, slice other) internal pure returns (bool) {
        return compare(self, other) == 0;
    }

    /*
     * @dev Extracts the first rune in the slice into `rune`, advancing the
     *      slice to point to the next rune and returning `self`.
     * @param self The slice to operate on.
     * @param rune The slice that will contain the first rune.
     * @return `rune`.
     */
    function nextRune(slice self, slice rune) internal pure returns (slice) {
        rune._ptr = self._ptr;

        if (self._len == 0) {
            rune._len = 0;
            return rune;
        }

        uint l;
        uint b;
        // Load the first byte of the rune into the LSBs of b
        assembly { b := and(mload(sub(mload(add(self, 32)), 31)), 0xFF) }
        if (b < 0x80) {
            l = 1;
        } else if(b < 0xE0) {
            l = 2;
        } else if(b < 0xF0) {
            l = 3;
        } else {
            l = 4;
        }

        // Check for truncated codepoints
        if (l > self._len) {
            rune._len = self._len;
            self._ptr += self._len;
            self._len = 0;
            return rune;
        }

        self._ptr += l;
        self._len -= l;
        rune._len = l;
        return rune;
    }

    /*
     * @dev Returns the first rune in the slice, advancing the slice to point
     *      to the next rune.
     * @param self The slice to operate on.
     * @return A slice containing only the first rune from `self`.
     */
    function nextRune(slice self) internal pure returns (slice ret) {
        nextRune(self, ret);
    }

    /*
     * @dev Returns the number of the first codepoint in the slice.
     * @param self The slice to operate on.
     * @return The number of the first codepoint in the slice.
     */
    function ord(slice self) internal pure returns (uint ret) {
        if (self._len == 0) {
            return 0;
        }

        uint word;
        uint length;
        uint divisor = 2 ** 248;

        // Load the rune into the MSBs of b
        assembly { word:= mload(mload(add(self, 32))) }
        uint b = word / divisor;
        if (b < 0x80) {
            ret = b;
            length = 1;
        } else if(b < 0xE0) {
            ret = b & 0x1F;
            length = 2;
        } else if(b < 0xF0) {
            ret = b & 0x0F;
            length = 3;
        } else {
            ret = b & 0x07;
            length = 4;
        }

        // Check for truncated codepoints
        if (length > self._len) {
            return 0;
        }

        for (uint i = 1; i < length; i++) {
            divisor = divisor / 256;
            b = (word / divisor) & 0xFF;
            if (b & 0xC0 != 0x80) {
                // Invalid UTF-8 sequence
                return 0;
            }
            ret = (ret * 64) | (b & 0x3F);
        }

        return ret;
    }

    /*
     * @dev Returns the keccak-256 hash of the slice.
     * @param self The slice to hash.
     * @return The hash of the slice.
     */
    function keccak(slice self) internal pure returns (bytes32 ret) {
        assembly {
            ret := keccak256(mload(add(self, 32)), mload(self))
        }
    }

    /*
     * @dev Returns true if `self` starts with `needle`.
     * @param self The slice to operate on.
     * @param needle The slice to search for.
     * @return True if the slice starts with the provided text, false otherwise.
     */
    function startsWith(slice self, slice needle) internal pure returns (bool) {
        if (self._len < needle._len) {
            return false;
        }

        if (self._ptr == needle._ptr) {
            return true;
        }

        bool equal;
        assembly {
            let length := mload(needle)
            let selfptr := mload(add(self, 0x20))
            let needleptr := mload(add(needle, 0x20))
            equal := eq(keccak256(selfptr, length), keccak256(needleptr, length))
        }
        return equal;
    }

    /*
     * @dev If `self` starts with `needle`, `needle` is removed from the
     *      beginning of `self`. Otherwise, `self` is unmodified.
     * @param self The slice to operate on.
     * @param needle The slice to search for.
     * @return `self`
     */
    function beyond(slice self, slice needle) internal pure returns (slice) {
        if (self._len < needle._len) {
            return self;
        }

        bool equal = true;
        if (self._ptr != needle._ptr) {
            assembly {
                let length := mload(needle)
                let selfptr := mload(add(self, 0x20))
                let needleptr := mload(add(needle, 0x20))
                equal := eq(sha3(selfptr, length), sha3(needleptr, length))
            }
        }

        if (equal) {
            self._len -= needle._len;
            self._ptr += needle._len;
        }

        return self;
    }

    /*
     * @dev Returns true if the slice ends with `needle`.
     * @param self The slice to operate on.
     * @param needle The slice to search for.
     * @return True if the slice starts with the provided text, false otherwise.
     */
    function endsWith(slice self, slice needle) internal pure returns (bool) {
        if (self._len < needle._len) {
            return false;
        }

        uint selfptr = self._ptr + self._len - needle._len;

        if (selfptr == needle._ptr) {
            return true;
        }

        bool equal;
        assembly {
            let length := mload(needle)
            let needleptr := mload(add(needle, 0x20))
            equal := eq(keccak256(selfptr, length), keccak256(needleptr, length))
        }

        return equal;
    }

    /*
     * @dev If `self` ends with `needle`, `needle` is removed from the
     *      end of `self`. Otherwise, `self` is unmodified.
     * @param self The slice to operate on.
     * @param needle The slice to search for.
     * @return `self`
     */
    function until(slice self, slice needle) internal pure returns (slice) {
        if (self._len < needle._len) {
            return self;
        }

        uint selfptr = self._ptr + self._len - needle._len;
        bool equal = true;
        if (selfptr != needle._ptr) {
            assembly {
                let length := mload(needle)
                let needleptr := mload(add(needle, 0x20))
                equal := eq(keccak256(selfptr, length), keccak256(needleptr, length))
            }
        }

        if (equal) {
            self._len -= needle._len;
        }

        return self;
    }

    event log_bytemask(bytes32 mask);

    // Returns the memory address of the first byte of the first occurrence of
    // `needle` in `self`, or the first byte after `self` if not found.
    function findPtr(uint selflen, uint selfptr, uint needlelen, uint needleptr) private pure returns (uint) {
        uint ptr = selfptr;
        uint idx;

        if (needlelen <= selflen) {
            if (needlelen <= 32) {
                bytes32 mask = bytes32(~(2 ** (8 * (32 - needlelen)) - 1));

                bytes32 needledata;
                assembly { needledata := and(mload(needleptr), mask) }

                uint end = selfptr + selflen - needlelen;
                bytes32 ptrdata;
                assembly { ptrdata := and(mload(ptr), mask) }

                while (ptrdata != needledata) {
                    if (ptr >= end)
                        return selfptr + selflen;
                    ptr++;
                    assembly { ptrdata := and(mload(ptr), mask) }
                }
                return ptr;
            } else {
                // For long needles, use hashing
                bytes32 hash;
                assembly { hash := sha3(needleptr, needlelen) }

                for (idx = 0; idx <= selflen - needlelen; idx++) {
                    bytes32 testHash;
                    assembly { testHash := sha3(ptr, needlelen) }
                    if (hash == testHash)
                        return ptr;
                    ptr += 1;
                }
            }
        }
        return selfptr + selflen;
    }

    // Returns the memory address of the first byte after the last occurrence of
    // `needle` in `self`, or the address of `self` if not found.
    function rfindPtr(uint selflen, uint selfptr, uint needlelen, uint needleptr) private pure returns (uint) {
        uint ptr;

        if (needlelen <= selflen) {
            if (needlelen <= 32) {
                bytes32 mask = bytes32(~(2 ** (8 * (32 - needlelen)) - 1));

                bytes32 needledata;
                assembly { needledata := and(mload(needleptr), mask) }

                ptr = selfptr + selflen - needlelen;
                bytes32 ptrdata;
                assembly { ptrdata := and(mload(ptr), mask) }

                while (ptrdata != needledata) {
                    if (ptr <= selfptr)
                        return selfptr;
                    ptr--;
                    assembly { ptrdata := and(mload(ptr), mask) }
                }
                return ptr + needlelen;
            } else {
                // For long needles, use hashing
                bytes32 hash;
                assembly { hash := sha3(needleptr, needlelen) }
                ptr = selfptr + (selflen - needlelen);
                while (ptr >= selfptr) {
                    bytes32 testHash;
                    assembly { testHash := sha3(ptr, needlelen) }
                    if (hash == testHash)
                        return ptr + needlelen;
                    ptr -= 1;
                }
            }
        }
        return selfptr;
    }

    /*
     * @dev Modifies `self` to contain everything from the first occurrence of
     *      `needle` to the end of the slice. `self` is set to the empty slice
     *      if `needle` is not found.
     * @param self The slice to search and modify.
     * @param needle The text to search for.
     * @return `self`.
     */
    function find(slice self, slice needle) internal pure returns (slice) {
        uint ptr = findPtr(self._len, self._ptr, needle._len, needle._ptr);
        self._len -= ptr - self._ptr;
        self._ptr = ptr;
        return self;
    }

    /*
     * @dev Modifies `self` to contain the part of the string from the start of
     *      `self` to the end of the first occurrence of `needle`. If `needle`
     *      is not found, `self` is set to the empty slice.
     * @param self The slice to search and modify.
     * @param needle The text to search for.
     * @return `self`.
     */
    function rfind(slice self, slice needle) internal pure returns (slice) {
        uint ptr = rfindPtr(self._len, self._ptr, needle._len, needle._ptr);
        self._len = ptr - self._ptr;
        return self;
    }

    /*
     * @dev Splits the slice, setting `self` to everything after the first
     *      occurrence of `needle`, and `token` to everything before it. If
     *      `needle` does not occur in `self`, `self` is set to the empty slice,
     *      and `token` is set to the entirety of `self`.
     * @param self The slice to split.
     * @param needle The text to search for in `self`.
     * @param token An output parameter to which the first token is written.
     * @return `token`.
     */
    function split(slice self, slice needle, slice token) internal pure returns (slice) {
        uint ptr = findPtr(self._len, self._ptr, needle._len, needle._ptr);
        token._ptr = self._ptr;
        token._len = ptr - self._ptr;
        if (ptr == self._ptr + self._len) {
            // Not found
            self._len = 0;
        } else {
            self._len -= token._len + needle._len;
            self._ptr = ptr + needle._len;
        }
        return token;
    }

    /*
     * @dev Splits the slice, setting `self` to everything after the first
     *      occurrence of `needle`, and returning everything before it. If
     *      `needle` does not occur in `self`, `self` is set to the empty slice,
     *      and the entirety of `self` is returned.
     * @param self The slice to split.
     * @param needle The text to search for in `self`.
     * @return The part of `self` up to the first occurrence of `delim`.
     */
    function split(slice self, slice needle) internal pure returns (slice token) {
        split(self, needle, token);
    }

    /*
     * @dev Splits the slice, setting `self` to everything before the last
     *      occurrence of `needle`, and `token` to everything after it. If
     *      `needle` does not occur in `self`, `self` is set to the empty slice,
     *      and `token` is set to the entirety of `self`.
     * @param self The slice to split.
     * @param needle The text to search for in `self`.
     * @param token An output parameter to which the first token is written.
     * @return `token`.
     */
    function rsplit(slice self, slice needle, slice token) internal pure returns (slice) {
        uint ptr = rfindPtr(self._len, self._ptr, needle._len, needle._ptr);
        token._ptr = ptr;
        token._len = self._len - (ptr - self._ptr);
        if (ptr == self._ptr) {
            // Not found
            self._len = 0;
        } else {
            self._len -= token._len + needle._len;
        }
        return token;
    }

    /*
     * @dev Splits the slice, setting `self` to everything before the last
     *      occurrence of `needle`, and returning everything after it. If
     *      `needle` does not occur in `self`, `self` is set to the empty slice,
     *      and the entirety of `self` is returned.
     * @param self The slice to split.
     * @param needle The text to search for in `self`.
     * @return The part of `self` after the last occurrence of `delim`.
     */
    function rsplit(slice self, slice needle) internal pure returns (slice token) {
        rsplit(self, needle, token);
    }

    /*
     * @dev Counts the number of nonoverlapping occurrences of `needle` in `self`.
     * @param self The slice to search.
     * @param needle The text to search for in `self`.
     * @return The number of occurrences of `needle` found in `self`.
     */
    function count(slice self, slice needle) internal pure returns (uint cnt) {
        uint ptr = findPtr(self._len, self._ptr, needle._len, needle._ptr) + needle._len;
        while (ptr <= self._ptr + self._len) {
            cnt++;
            ptr = findPtr(self._len - (ptr - self._ptr), ptr, needle._len, needle._ptr) + needle._len;
        }
    }

    /*
     * @dev Returns True if `self` contains `needle`.
     * @param self The slice to search.
     * @param needle The text to search for in `self`.
     * @return True if `needle` is found in `self`, false otherwise.
     */
    function contains(slice self, slice needle) internal pure returns (bool) {
        return rfindPtr(self._len, self._ptr, needle._len, needle._ptr) != self._ptr;
    }

    /*
     * @dev Returns a newly allocated string containing the concatenation of
     *      `self` and `other`.
     * @param self The first slice to concatenate.
     * @param other The second slice to concatenate.
     * @return The concatenation of the two strings.
     */
    function concat(slice self, slice other) internal pure returns (string) {
        string memory ret = new string(self._len + other._len);
        uint retptr;
        assembly { retptr := add(ret, 32) }
        memcpy(retptr, self._ptr, self._len);
        memcpy(retptr + self._len, other._ptr, other._len);
        return ret;
    }

    /*
     * @dev Joins an array of slices, using `self` as a delimiter, returning a
     *      newly allocated string.
     * @param self The delimiter to use.
     * @param parts A list of slices to join.
     * @return A newly allocated string containing all the slices in `parts`,
     *         joined with `self`.
     */
    function join(slice self, slice[] parts) internal pure returns (string) {
        if (parts.length == 0)
            return "";

        uint length = self._len * (parts.length - 1);
        for(uint i = 0; i < parts.length; i++)
            length += parts[i]._len;

        string memory ret = new string(length);
        uint retptr;
        assembly { retptr := add(ret, 32) }

        for(i = 0; i < parts.length; i++) {
            memcpy(retptr, parts[i]._ptr, parts[i]._len);
            retptr += parts[i]._len;
            if (i < parts.length - 1) {
                memcpy(retptr, self._ptr, self._len);
                retptr += self._len;
            }
        }

        return ret;
    }
}

contract InternalGatewayDevice{
    uint private GatewayId;
    string private PublicKey;
    string private Arbitrary_Data;//JSON Data
    address private Owner;
    Root private RootContract;
    
    struct Node {
        uint Id;
        string DeviceName;
        string MAC;
        string PublicKey;
        string NodeData;//JSON Data
    }
    
    //An InternalGatewayDevice is reponsible for being the gateway between devices
    //not connected to the blockchain and the blockchain itself
    mapping(uint => Node) private Nodes;
    uint private NumberOfNodes;
    
    event NodeAdded(uint _id);
    
    constructor(uint _id, string _publicKey, string _data, address _owner) public payable {
        GatewayId = _id;
        PublicKey = _publicKey;
        Arbitrary_Data = _data;
        Owner = _owner;
        RootContract = Root(msg.sender);
    }
    
    //Only the root contract can add nodes to this contract
    function AddNode(string _deviceName, string _mac, string _publicKey, string _data) public returns (uint){
        require (address(RootContract) == msg.sender);//can only be done through the root contract
        Nodes[NumberOfNodes] = Node(
            NumberOfNodes, _deviceName, _mac, _publicKey, _data);
        emit NodeAdded(NumberOfNodes);//Send event that a node has been added with its Id
        NumberOfNodes++;
        return NumberOfNodes - 1;
    }
    
    //Get the details of a specfic node within this contract
    function GetNodeDetails(uint _id) public constant returns (uint, string, string, string, string){
        require(_id < NumberOfNodes);
        require(Owner == msg.sender || address(RootContract) == msg.sender);
        return (Nodes[_id].Id, 
            Nodes[_id].DeviceName, 
            Nodes[_id].MAC, 
            Nodes[_id].PublicKey,
            Nodes[_id].NodeData);
    }

    //Get Number of Nodes
    function GetNodeCount() public constant returns(uint) {
        require(Owner == msg.sender || address(RootContract) == msg.sender);
        return NumberOfNodes;
    }
    
    //Get the details of this contract
    function GetDetails() public constant returns (string, string, address){
        require(Owner == msg.sender || address(RootContract) == msg.sender);
        return (PublicKey, Arbitrary_Data, Owner);
    }
    
    //A node can request to join this segmented network and be involved in the blockchain
    //through the InternalGatewayDevice. The request is sent to the root contract and
    //waits for approval
    function RequestToJoin(string _deviceName, string _mac, string _publicKey, string _data) public {
        RootContract.RequestToJoinGateway(GatewayId, _deviceName, _mac, _publicKey, _data);
    }
}

contract GetPermission {
    using strings for *;
    Root private RootContract;
    
    struct PermissionData {
        bool Active;//Permissions might be switched off or "deleted"
        uint Id;
        string PublicKey;
        string Arbitrary_Data;//JSON String {} for all get Permissions
    }
    
    struct DevicePermissions {
        bool Active;//Permissions might be switched off or deleted
        mapping (string => PermissionData) Permissions;
        mapping (uint => PermissionData) Devices;//keep track of all devices in a sequential manner
        uint DevicesCount;
    }
    
    //The public key of each device is used as the key to map to its permissions
    mapping(string => DevicePermissions) private GetPermissions;
    
    constructor() public payable {
        RootContract = Root(msg.sender);
    }
    
    modifier IsOwner() {
        require (address(RootContract) == msg.sender);
        _;
    }
    
    //Anyone can call this function to read permissions of one node to another
    //returns the data of only the requested node
    function ReadPermissionNodeToSelf(string _nodePublicKey, string _selfPublicKey) public constant returns (string){
        require(GetPermissions[_nodePublicKey].Active == true);
        require(GetPermissions[_nodePublicKey].Permissions[_selfPublicKey].Active == true);
        return GetPermissions[_nodePublicKey].Permissions[_selfPublicKey].Arbitrary_Data;
    }
    
    function GetCountOfActivePermissions(string _nodePublicKey) private constant returns (uint){
        uint count = 0;
        for (uint i=0; i < GetPermissions[_nodePublicKey].DevicesCount; i++){
            if (GetPermissions[_nodePublicKey].Devices[i].Active == true){
                count++;
            }
        }
        return count;
    }
    
    //Anyone can call this function to read permissions of one node to another
    //returns all data related to the input public key
    function ReadAllPermissions(string _nodePublicKey) public constant returns (string){
        require(GetPermissions[_nodePublicKey].Active == true);
        uint count = GetCountOfActivePermissions(_nodePublicKey);
        string memory PermissionsData = "{";
        if (count == 0) return PermissionsData;
        uint addCount = 0;
        for (uint i=0; i < GetPermissions[_nodePublicKey].DevicesCount; i++){
            if (GetPermissions[_nodePublicKey].Devices[i].Active == true){
                PermissionsData = PermissionsData.toSlice().concat(GetPermissions[_nodePublicKey].Devices[i].PublicKey.toSlice());
                PermissionsData = PermissionsData.toSlice().concat(":".toSlice());
                PermissionsData = PermissionsData.toSlice().concat(GetPermissions[_nodePublicKey].Devices[i].Arbitrary_Data.toSlice());
                addCount++;
                if (addCount == count) break;//we found all active permissions
                else PermissionsData = PermissionsData.toSlice().concat(",".toSlice());
            }
        }
        PermissionsData = PermissionsData.toSlice().concat("}".toSlice());
        return PermissionsData;
    }
    
    //Can only be called by the root address
    //Is only executed to add a new device to permission list
    //Can only be done through root contract
    function AddPermission(string _nodePublicKey,string _targetPublicKey, string _data) IsOwner public {
        require(GetPermissions[_nodePublicKey].Active == false);
        PermissionData memory PD = PermissionData(true, 0, _targetPublicKey, _data);
        DevicePermissions memory DP = DevicePermissions({Active: true, DevicesCount: 1});
        GetPermissions[_nodePublicKey] = DP;
        GetPermissions[_nodePublicKey].Permissions[_targetPublicKey] = PD;
        GetPermissions[_nodePublicKey].Devices[0] = PD;
    }
    
    //check if input is not an empty string
    function DoesPermissionExist(string _data) private pure returns (bool){
        string memory empty = "";
        return keccak256(_data) == keccak256(empty);
    }
    
    //Update one of the permissions in the Permissioned device
    //Can only be done through Root contract
    //Can also be used to add a permission to the Permissioned device
    function UpdatePermission(string _nodePublicKey,string _targetPublicKey, string _data, bool _active) IsOwner public {
        require(GetPermissions[_nodePublicKey].Active == true);
        if (DoesPermissionExist(GetPermissions[_nodePublicKey].Permissions[_targetPublicKey].Arbitrary_Data)){
            PermissionData memory PD = PermissionData(_active,
                GetPermissions[_nodePublicKey].DevicesCount,
                _targetPublicKey, 
                _data);
            GetPermissions[_nodePublicKey].Permissions[_targetPublicKey] = PD;
            GetPermissions[_nodePublicKey].Devices[GetPermissions[_nodePublicKey].DevicesCount] = PD;
            GetPermissions[_nodePublicKey].DevicesCount++;
        }
        else{
            uint deviceId = GetPermissions[_nodePublicKey].Permissions[_targetPublicKey].Id;
            PD = PermissionData(_active,
                deviceId,
                _targetPublicKey, 
                _data);
            GetPermissions[_nodePublicKey].Permissions[_targetPublicKey] = PD;
            GetPermissions[_nodePublicKey].Devices[deviceId] = PD;
        }
    }
    
    //Turn a permissioned device on or off
    //Can only be done through Root contract
    function SwitchActiveDevice(string _nodePublicKey) IsOwner public {
        require(GetPermissions[_nodePublicKey].DevicesCount > 0);
        GetPermissions[_nodePublicKey].Active = !GetPermissions[_nodePublicKey].Active;
    }
}

contract Certificate {
    Root private RootContract;

    struct CertificateArray {
        bool Active;
        uint CertificateId;
        address IssuedBy;
        string PublicKey;
        string DeviceName;
        string MAC;
        string ArbitraryData;
    }

    mapping(uint => CertificateArray) private Certificates;
    uint private CertificateCount;

    constructor() public payable {
        RootContract = Root(msg.sender);
    }

    modifier IsOwner() {
        require (address(RootContract) == msg.sender);
        _;
    }

    function AddCertificate(address IssuedBy, string PublicKey, string DeviceName, string MAC, string ArbitraryData) IsOwner public returns (uint) {
        Certificates[CertificateCount] = CertificateArray(true,
            CertificateCount,
            IssuedBy,
            PublicKey,
            DeviceName,
            MAC,
            ArbitraryData);
        CertificateCount++;
        return CertificateCount - 1;
    }

    function DeActivateCertificate(uint CertificateId) IsOwner public {
        require(CertificateId <= CertificateCount);
        Certificates[CertificateCount].Active = false;
    }

    function GetCertificate(uint _Id) public constant returns (address, string, string, string, string) {
        require(Certificates[_Id].Active == true);
        return (Certificates[_Id].IssuedBy, Certificates[_Id].PublicKey, Certificates[_Id].DeviceName, Certificates[_Id].MAC, Certificates[_Id].ArbitraryData);
    }
}

contract Root {
    //root account
    address private Owner;
    string private PublicKey;
    
    struct AuthorizedAccountTier1 {
        uint Id;
        string PublicKey;
        string DeviceName;
        address Address;
    }
    
    //accounts with next tier access which have major control on the blockchain
    //these accounts can register new devices to the blockchain, but cannot add
    //other account. This can only be done through the owner
    mapping(uint => AuthorizedAccountTier1) private AuthorizedAccountsTier1;
    InternalGatewayDevice[] private InternalGatewayDevices;//might need to be changed to mapping
    mapping(address => uint) private CertificatesMapping;
    uint private TierOneAccountsCount;
    
    //Initialise GetPermission contracts
    //Command: 0 -> Read
    //Command: 1 -> Write
    GetPermission private Read;
    GetPermission private Write;

    HashedData public GlobalData;
    Certificate private Certificates;
    
    //events that allows listeners to dynamically react to changes
    event RequestedToJoinGateway(
        uint _id, string _deviceName, string _mac, string _publicKey, string _data);
    event RequestedToJoinAsGateway(
        string _publicKey, string _data, address _owner);
    event InternalGatewayAdded(uint _senderId, string _publicKey, string _data, 
        address _owner, uint _gatewayId);
    event TierOneAccountAdded(string _publicKey, string _deviceName, address _address, uint _id);
    event NodeAddedToGateway(uint _senderId, uint _deviceId, string _deviceName, 
        string _mac, string _publicKey, string _data, uint _nodeId, address _owner);
    
    constructor(string _publicKey) public payable {
        //executed once to whoever first called this contract is now the owner
        Owner = msg.sender;
        PublicKey = _publicKey;
        //Initialise Read and Write
        Read = GetPermission(CreateReadContract());//new GetPermission();
        Write = GetPermission(CreateWriteContract());//new GetPermission();
        //Initialise Global data
        GlobalData = new HashedData();
        //Initialise Certificate contract
        Certificates = new Certificate();
        //add itself to the authorized accounts
        AddTierOneAccount(PublicKey, "Root", Owner);
    }

    function CreateReadContract() private returns(address) {
        GetPermission readContract = new GetPermission();
        return readContract;
    }

    function CreateWriteContract() private returns(address) {
        GetPermission writeContract = new GetPermission();
        return writeContract;
    }

    //Can be called by any entity
    //returns the address of the read permission contract
    function GetReadAddress() public constant returns (address) {
        return address(Read);
    }
    
    //Can be called by any entity
    //returns the address of the write permission contract
    function GetWriteAddress() public constant returns (address) {
        return address(Write);
    }

    //Can be called by any entity
    //returns the address of the Global data contract
    function GetGlobalDataAddress() public constant returns (address) {
        return address(GlobalData);
    }

    //Can be called by any entity
    //returns the address of the Certificate contract
    function GetCertificateAddress() public constant returns (address) {
        return address(Certificates);
    }

    //Can be called by anyone
    //returns the certificate id belonging to the entity that called this method
    function GetCertificateId() public constant returns (uint) {
        require(CertificatesMapping[msg.sender] != 0);
        return CertificatesMapping[msg.sender];
    }
    
    //can only be executed by an authorized account
    //_command specifies on what the switch should be done ex. whether read or write
    //Changes the activity of a permission
    function SwitchActiveDevice(uint _senderId, string _nodePublicKey, uint _command ) public {
        require(_senderId < TierOneAccountsCount);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        if (_command == 0) { Read.SwitchActiveDevice(_nodePublicKey); }
        else if (_command == 1) {Write.SwitchActiveDevice(_nodePublicKey); }
        else { 
            //More commands might be added in the future 
        }
    }
    
    //can only be executed by an authorized account
    //Adds a new permission depending on the _command input
    function AddPermission(uint _senderId, string _nodePublicKey,string _targetPublicKey,
        string _data, uint _command) public {
        require(_senderId < TierOneAccountsCount);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        if (_command == 0) { Read.AddPermission(_nodePublicKey, _targetPublicKey, _data); }
        else if (_command == 1) { Write.AddPermission(_nodePublicKey, _targetPublicKey, _data); }
        else {
            //More commands might be added in the future 
        }
    }
    
    //can only be executed by an authorized account
    //Update a current permission by adding a new device to the permission or
    //updating the data of an existing device that exists within that permission
    function UpdatePermission(uint _senderId, string _nodePublicKey,string _targetPublicKey, 
        string _data, bool _active, uint _command) public {
        require(_senderId < TierOneAccountsCount);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        if (_command == 0) { Read.UpdatePermission(_nodePublicKey, _targetPublicKey, _data, _active); }
        else if (_command == 1) { Write.UpdatePermission(_nodePublicKey, _targetPublicKey, _data, _active); }
        else {
            //More commands might be added in the future 
        }
    }

    //Adds a new Certificate
    function AddCertificate(uint _senderId, string PublicKey, string DeviceName, 
        string MAC, string ArbitraryData, address CertHolder) public {
        require(_senderId < TierOneAccountsCount);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        uint CertId = Certificates.AddCertificate(msg.sender, PublicKey, DeviceName, MAC, ArbitraryData);
        CertificatesMapping[CertHolder] = CertId;
    }

    //Disables a Certificate
    function DisableCertificate(uint _senderId, uint CertificateId) public {
        require(_senderId < TierOneAccountsCount);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        Certificates.DeActivateCertificate(CertificateId);
    }
    
    //Takes an Id and returns the details of the device that exists within the blockchain
    //Only authorized accounts can access this method, and only valid id can be accessed
    //and returned back
    function GetAccountDetails(uint _id, uint _senderId) public constant returns (uint, string, string, address){
        require(_id < TierOneAccountsCount);
        require(_senderId < TierOneAccountsCount);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        return (AuthorizedAccountsTier1[_id].Id, 
            AuthorizedAccountsTier1[_id].PublicKey, 
            AuthorizedAccountsTier1[_id].DeviceName, 
            AuthorizedAccountsTier1[_id].Address);
    }
    
    //Owner adds a device to the blockchain with all the required information
    //The device can now access data on the blockchain depending on its level
    //of authorization
    function AddTierOneAccount(string _publicKey, string _deviceName, address _address) public returns (uint){
        require(Owner == msg.sender);
        AuthorizedAccountsTier1[TierOneAccountsCount] = AuthorizedAccountTier1(
            TierOneAccountsCount, _publicKey, _deviceName, _address);
        TierOneAccountsCount++;
        emit TierOneAccountAdded(_publicKey, _deviceName, _address, TierOneAccountsCount - 1);
        return TierOneAccountsCount - 1;
    }
    
    //Can only be done by an authorized account
    //Adds a new device that is reponsible for handling nodes not connected to the blockchain
    function AddInternalGateway(uint _senderId, string _publicKey, string _data, address _owner) public returns (uint){
        require(_senderId < TierOneAccountsCount);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        InternalGatewayDevice device = new InternalGatewayDevice(InternalGatewayDevices.length,
                                            _publicKey,
                                            _data,
                                            _owner);
        InternalGatewayDevices.push(device);
        emit InternalGatewayAdded(_senderId, _publicKey, _data, _owner, InternalGatewayDevices.length - 1);
        return InternalGatewayDevices.length - 1;
    }
    
    //Can only be done through an authorized account
    //takes a specfic internal gateway and adds a new device that is not connected to the blockchain to it
    function AddNodeToGateway(uint _senderId, uint _deviceId, string _deviceName, 
        string _mac, string _publicKey, string _data) public returns (uint){
        require(_senderId < TierOneAccountsCount);
        require(_deviceId < InternalGatewayDevices.length);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        uint NodeId = InternalGatewayDevices[_deviceId].AddNode(_deviceName, _mac, _publicKey, _data);
        emit NodeAddedToGateway(_senderId, _deviceId, _deviceName, _mac, _publicKey, _data, NodeId, address(InternalGatewayDevices[_deviceId]));
        return NodeId;
    }
    
    //Can only be done by an authorized account
    //Gets the details of a specific gateway that exists in the blockchain
    function GetGatewayDetails(uint _id, uint _senderId) public constant returns (string, string, address) {
        require(_senderId < TierOneAccountsCount);
        require(_id < InternalGatewayDevices.length);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        return InternalGatewayDevices[_id].GetDetails();
    }

    function GetGatewayNodeDetails(uint _id, uint _nodeId, uint _senderId) public constant returns (uint, string, string, string, string) {
        require(_senderId < TierOneAccountsCount);
        require(_id < InternalGatewayDevices.length);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        return InternalGatewayDevices[_id].GetNodeDetails(_nodeId);
    }

    //return number of Gateways
    function GatewaysCount(uint _senderId) public constant returns (uint) {
        require(_senderId < TierOneAccountsCount);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        return InternalGatewayDevices.length;
    }

    //Get number of nodes in a gateway
    function GatwayNodeCount(uint _id, uint _senderId) public constant returns (uint) {
        require(_senderId < TierOneAccountsCount);
        require(AuthorizedAccountsTier1[_senderId].Address == msg.sender);
        require(_id < InternalGatewayDevices.length);
        return InternalGatewayDevices[_id].GetNodeCount();
    }

    //Number of Tier one accounts
    function TierOneCount() public constant returns (uint) {
        require(Owner == msg.sender);
        return TierOneAccountsCount;
    }
    
    //can only be done by an InternalGatewayDevice and must always refer to itself or
    //function will be rejected. Sends an event that a node want to be added
    function RequestToJoinGateway(uint _id, string _deviceName, string _mac, string _publicKey, string _data) public{
        require(_id < InternalGatewayDevices.length);
        require(address(InternalGatewayDevices[_id]) == msg.sender);
        emit RequestedToJoinGateway(_id, _deviceName, _mac, _publicKey, _data);
    }
    
    //Outer devices can use this method to request to join the network
    function RequestToJoinAsGateway(string _publicKey, string _data) public{
        emit RequestedToJoinAsGateway(_publicKey, _data, msg.sender);
    }
}

contract HashedData {
    //Data would be encrypted with the private key and then hashed.
    //Using the mapped data we can get the public key and decrypt the data
    struct MappedData {
        bool Exists;
        uint Writer_Id;
        string Writer_Type;
        string Arbitrary_Data; //JSON data
    }
    
    //maps the blockchain data to the hash of the original data outside the blockchain
    mapping(bytes32 => MappedData) Data;
    
    //Uses input hash to connect it to the input data
    function InsertHashData(bytes32 _hash, uint _writer_Id, string _writer_Type, string _data) public {
        Data[_hash] = MappedData(
            true, _writer_Id, _writer_Type, _data);
    }
    
    //Uses input hash to retrieve data related to that hash that is stored in the blockchain
    function GetHashData(bytes32 _hash) public constant returns (uint, string, string){
        require(Data[_hash].Exists == true);
        return (Data[_hash].Writer_Id, Data[_hash].Writer_Type, Data[_hash].Arbitrary_Data);
    }
}
'''
