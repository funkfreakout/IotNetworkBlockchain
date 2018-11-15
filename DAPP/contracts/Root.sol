pragma solidity ^0.4.0;

import "./InternalGatewayDevice.sol";
import "./GetPermission.sol";
import "./HashedData.sol";
import "./Certificate.sol";
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