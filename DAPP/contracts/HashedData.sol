pragma solidity ^0.4.0;

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