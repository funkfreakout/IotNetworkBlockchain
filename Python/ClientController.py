import socket
from InitController import Controller
import re
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
import ast

regex = r"([=])"
tagRegex = r"/Tag="
nonceRegex = r"/Nonce="

def InitConnection(hostAddress, serverPort, controller):
	HOST = hostAddress
	PORT = serverPort
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.connect((HOST, PORT))
	certId = controller.root.GetCertificateId()
	s.sendall(str.encode('CertificateId='+str(certId)))
	data = s.recv(2048)
	dataString = data.decode('utf-8')
	regex = r"([=])"
	if re.search(regex, dataString):
		match = re.search(regex, dataString)
		if dataString[0:match.start()] == 'SESSION_KEY':
			msgToDec = dataString[match.start()+1:]
			cipher_rsa = PKCS1_OAEP.new(controller.Private_Key)
			sKey = cipher_rsa.decrypt(ast.literal_eval(str(msgToDec)))
			return s, sKey
		else: return 0
	else: return 0


controller = Controller('Client')
s, session_key = InitConnection('', 50103, controller)
while 1:
	cipher_aes = AES.new(session_key, AES.MODE_EAX)
	value = input('Please enter the number of Buzzes required: ')
	if value.upper() == 'END':
		s.sendall(str.encode('END=END'))
		data = s.recv(2048)
		print ('Received', data.decode('utf-8'))
		break
	value = 'Buzz='+value
	value = value.encode('utf-8')
	ciphertext, tag = cipher_aes.encrypt_and_digest(value)
	s.sendall(str.encode('ENCRYPTEDCALL=') + str.encode(str(ciphertext)) + str.encode('/Tag=') + str.encode(str(tag)) + str.encode('/Nonce=') + str.encode(str(cipher_aes.nonce)))
	data = s.recv(2048)
	dataString = data.decode('utf-8')
	if re.search(regex, dataString):
		match = re.search(regex, dataString)
		if dataString[0:match.start()] == 'ENCRYPTEDCALL':
			if re.search(tagRegex, dataString):
				if re.search(nonceRegex, dataString):
					nonceMatch = re.search(nonceRegex, dataString)
					nonce = dataString[nonceMatch.start()+7:]
				else: 
					print('ERROR=MissingEncryptionNonce')
				try:
					tagMatch = re.search(tagRegex, dataString)
					encyptedMsg = dataString[match.start()+1:tagMatch.start()]
					tag = dataString[tagMatch.start()+5:nonceMatch.start()]
					cipher_aes = AES.new(session_key, AES.MODE_EAX, ast.literal_eval(nonce))
					decryptedMsg = cipher_aes.decrypt_and_verify(ast.literal_eval(encyptedMsg), ast.literal_eval(tag))
					decryptedMsg = decryptedMsg.decode('utf-8')
					if re.search(regex, decryptedMsg):
						callMatch = re.search(regex, decryptedMsg)
						if decryptedMsg[0:callMatch.start()] == 'Action':
							value = decryptedMsg[callMatch.start()+1:]
							print('Received Action: ', value)
						else: print('ERROR=InvalidCallCommand')
				except Exception as e:
					print(e)
					print('ERROR=DecryptionFailed')
			else: print('ERROR=MissingEncryptionTag')
		else:
			print ('Received', dataString)
	else:
		print('IncorrectCallFormat')
s.close()