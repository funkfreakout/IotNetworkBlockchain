pragma solidity ^0.4.0;

import "./Root.sol";
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
	uint private CertificateCount = 1;

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