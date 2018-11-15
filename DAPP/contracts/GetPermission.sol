pragma solidity ^0.4.0;

import "./Root.sol";
import "./strings.sol";//Open-Source library
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
        string memory PermissionsData = '{"';
        if (count == 0) return PermissionsData;
        uint addCount = 0;
        for (uint i=0; i < GetPermissions[_nodePublicKey].DevicesCount; i++){
            if (GetPermissions[_nodePublicKey].Devices[i].Active == true){
                PermissionsData = PermissionsData.toSlice().concat(GetPermissions[_nodePublicKey].Devices[i].PublicKey.toSlice());
                PermissionsData = PermissionsData.toSlice().concat('":'.toSlice());
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