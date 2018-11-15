import socket
from InitController import Controller
from PermissionAlarm import PermissionedAlarm
from _thread import *
import re
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES, PKCS1_OAEP
import string
import random
import ast
import json

def AlarmConConnection(s, alarm, controller):
	session_key = ''
	PublicKey = ''
	SelfKey = ''
	regex = r"([=])"
	tagRegex = r"/Tag="
	nonceRegex = r"/Nonce="
	while 1:
		try:
		    data = s.recv(2048)
		    if not data: break
		    dataString = data.decode('utf-8')
		    if re.search(regex, dataString):
		    	match = re.search(regex, dataString)
		    	if dataString[0:match.start()] == 'CertificateId':
		    		certId = dataString[match.start()+1:]
		    		PublicKey = controller.cert.GetCertificate(int(certId))[1]
			    	SelfKey = open("PublicAlarmRSAKey.bin").read()
		    		session_key = get_random_bytes(16)

		    		cipher_rsa = PKCS1_OAEP.new(RSA.importKey(PublicKey))
		    		encKey = cipher_rsa.encrypt(session_key)
		    		s.sendall(str.encode('SESSION_KEY=')+str.encode(str(encKey)))
		    	elif dataString[0:match.start()] == 'ENCRYPTEDCALL':
		    		if re.search(tagRegex, dataString):
		    			if re.search(nonceRegex, dataString):
		    				nonceMatch = re.search(nonceRegex, dataString)
		    				nonce = dataString[nonceMatch.start()+7:]
		    			else: 
		    				s.sendall(str.encode('ERROR=MissingEncryptionNonce'))
		    				continue
		    			try:
		    				tagMatch = re.search(tagRegex, dataString)
		    				encyptedMsg = dataString[match.start()+1:tagMatch.start()]
			    			tag = dataString[tagMatch.start()+5:nonceMatch.start()]
			    			cipher_aes = AES.new(session_key, AES.MODE_EAX, ast.literal_eval(nonce))
			    			decryptedMsg = cipher_aes.decrypt_and_verify(ast.literal_eval(encyptedMsg), ast.literal_eval(tag))
			    			decryptedMsg = decryptedMsg.decode('utf-8')
			    			if re.search(regex, decryptedMsg):
			    				callMatch = re.search(regex, decryptedMsg)
			    				if decryptedMsg[0:callMatch.start()] == 'Buzz':
			    					value = decryptedMsg[callMatch.start()+1:]
			    					try: intValue = int(value)
			    					except:
			    						s.sendall(str.encode('ERROR=IncorrectBuzzValue'))
			    						continue

			    					try:
			    						#print(controller.write.ReadAllPermissions(PublicKey))
			    						#permissions = controller.write.ReadPermissionNodeToSelf(PublicKey, '''-----BEGIN PUBLIC KEY-----MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCiCLw70kEFL71yrWopewKxAWCd\n1RiIljr16HhCgG48e2cb+Lupt5t7vv8YnMZrdYEvgtxc/edrqZyttbvGBY5BYED+\nfwLfInr1iOq6mpzBW8YZIHIrkiPnPyHhBn4mJSfoYM4MoGt2IgC7AvQToGL0pUUk\n6NOomXXx562kT7mPRQIDAQAB\n-----END PUBLIC KEY-----''')
			    						permissions = controller.write.ReadPermissionNodeToSelf(PublicKey, SelfKey)
			    						permission = json.loads(permissions)
			    					except:
			    						s.sendall(str.encode('ERROR=AccessDeniedDueToMissingPermissions'))
			    						continue
			    					try:
			    						MIN = permission['MIN']
			    						MAX = permission['MAX']
			    						if intValue < MIN or intValue > MAX:
			    							s.sendall(str.encode('ERROR=AccessDenied'))
			    							continue
			    					except:
			    						s.sendall(str.encode('ERROR=InvalidPermissionData'))
			    						continue

			    					cipher_aes = AES.new(session_key, AES.MODE_EAX)
			    					sendValue='Action=Buzzing'
			    					sendValue=sendValue.encode('utf-8')
			    					ciphertext, tag = cipher_aes.encrypt_and_digest(sendValue)
			    					s.sendall(str.encode('ENCRYPTEDCALL=') + str.encode(str(ciphertext)) + str.encode('/Tag=') + str.encode(str(tag)) + str.encode('/Nonce=') + str.encode(str(cipher_aes.nonce)))
			    					alarm.Buzz(intValue)
			    				else: s.sendall(str.encode('ERROR=InvalidCallCommand'))
			    		except Exception as e:
			    			print(e)
			    			s.sendall(str.encode('ERROR=DecryptionFailed'))
			    			break
		    		else: s.sendall(str.encode('ERROR=MissingEncryptionTag'))
		    	elif dataString[0:match.start()] == 'END':
		    		s.sendall(str.encode('Action=ENDCONNECTION'))
		    		break
		    	else:
		    		s.sendall(str.encode('ERROR=InvalidCommand'))
		    else:
		    	s.sendall(str.encode('ERROR=InvalidCall'))
		except Exception as e:
			print(e)
			s.sendall(str.encode('ERROR=ConnectionFailed'))
			break
	s.close()

def ServerController(hostAddress, serverPort, alarm, controller):
	HOST = hostAddress
	PORT = serverPort
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)#socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.bind((HOST, PORT))
	s.listen(1)

	while 1:
		conn, addr = s.accept()
		print ('Connected by', addr)
		start_new_thread(AlarmConConnection, (conn, alarm, controller, ))

controller = Controller('Alarm')
alarm = PermissionedAlarm(8, "/dev/ttyS0")
ServerController('', 50103, alarm, controller)