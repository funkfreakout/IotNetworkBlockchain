pragma solidity ^0.4.0;

import "./Root.sol";
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