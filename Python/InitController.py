import web3
from web3 import Web3
from web3.contract import ConciseContract
from solc import compile_source
from SolContracts import contract_source_code
from Crypto.PublicKey import RSA
import os.path

class Controller:
	def __init__(self, name):
		print('initializing connection to Blockchain...')

		#Make connection and get sol compiled code
		web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:7545"))
		compiled_sol = compile_source(contract_source_code) # Compiled source code
		contract_interface = compiled_sol['<stdin>:Root']
		permission_interface = compiled_sol['<stdin>:GetPermission']
		data_interface = compiled_sol['<stdin>:HashedData']
		cert_interface = compiled_sol['<stdin>:Certificate']

		#Take basic info for initialization
		account = input('Please enter Ganache Account: ')
		Blockchain_Address = input('Please enter the address of the root contract: ')

		#Handling 2048 bits RSA Key Pair
		psswd = '9592bbc15e5347e284724844d0699454b42ce456bc0eda514a6ad8ad87397544'
		KeyFile = name + 'RSAKey.bin'
		if os.path.exists(KeyFile) == False:
			key = RSA.generate(1024)
			encryptedKey = key.export_key(passphrase=psswd, pkcs=8,
			                              protection="scryptAndAES128-CBC")
			publicSavedKey = key.publickey().export_key()
			publickeyOutput = open('Public'+KeyFile, "wb")
			publickeyOutput.write(publicSavedKey)
			output = open(KeyFile, "wb")
			output.write(encryptedKey)
		else:
			encodedKey = open(KeyFile, "rb").read()
			key = RSA.import_key(encodedKey, passphrase=psswd)
		self.Public_Key = key.publickey().export_key()
		self.Private_Key = key#key#.export_key()

		#Connect to deploted contracts
		web3.eth.defaultAccount = web3.eth.accounts[int(account)]
		address = Web3.toChecksumAddress(Blockchain_Address)
		rootContract = web3.eth.contract(address, abi=contract_interface['abi'])
		self.root = ConciseContract(rootContract)
		readAddress = self.root.GetReadAddress()
		raddress = Web3.toChecksumAddress(readAddress)
		readContract = web3.eth.contract(raddress, abi=permission_interface['abi'])
		self.read = ConciseContract(readContract)
		writeAddress = self.root.GetWriteAddress()
		waddress = Web3.toChecksumAddress(writeAddress)
		writeContract = web3.eth.contract(waddress, abi=permission_interface['abi'])
		self.write = ConciseContract(writeContract)
		dataAddress = self.root.GetGlobalDataAddress()
		daddress = Web3.toChecksumAddress(dataAddress)
		dataContract = web3.eth.contract(daddress, abi=data_interface['abi'])
		self.dataMem = ConciseContract(dataContract)
		certAddress = self.root.GetCertificateAddress()
		caddress = Web3.toChecksumAddress(certAddress)
		certContract = web3.eth.contract(caddress, abi=cert_interface['abi'])
		self.cert = ConciseContract(certContract)