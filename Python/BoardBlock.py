from InitController import Controller
from Alarm import Alarm

#Specfic Device Handler
#controller = Controller('Alarm')
#print(controller.Public_Key)
#alarm = Alarm(8, "/dev/ttyS0")
#alarm.Buzz(5)
controller = Controller('root')
controller.root.AddCertificate(0, '''-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+Ui9OqPGeGv69JyJUhWPHLX7y\n1zBOyTzJEGWP0/9kxJriJ22vOF45aVcUoVIr3y2zaVN2eOVyIZkYLCAj1schwMTx\nRGCKHARJaUjRFTiwY0aQPNgD71qlYF5zjhUdiURUec9QMmxCYprNRxw3+xSZLPoG\nM+U59J8OLmjd3ZLojwIDAQAB\n-----END PUBLIC KEY-----''', 'CLient', 'MAC2', '{}', '0xe0A5b153B342Bd4085890077b780DBCe2cF01741')

#jsonString = read.ReadAllPermissions("MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAuwoFqMNYnSpuZcPSxDYP\nrrPvId2MhCupN5ntcU2nsRILdryaz6meONkBMQgOBXgEba9Ex+PgSKG2mJ8iPFvS\nbvmEJyWCBi++ClxO28R8X2C/Pi0fN6Bq3KajVyZT4GT8/PcQCnEmtgcUzrNQ0Rht\npOjyPYqZ6Y0oNbR0MAorPTdDLJ8RWV9H1evWBx9UkCIFhe1GcTis7omDuMEEEqRw\nG2PdUA8GI/toP4URVZM4E3U9cJ72xduDKlkLyWwBj1dvMi6F7xLWQT19Dwpu/f9G\n/mpVkhqrPTnYCBW4DnwPqjOt12Ox04jc0vPIWZccp4EZh9TMg/tX/Cb3X3qkjAGN\nAwIDAQAC")
'''-----BEGIN PUBLIC KEY-----MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCiCLw70kEFL71yrWopewKxAWCd\n1RiIljr16HhCgG48e2cb+Lupt5t7vv8YnMZrdYEvgtxc/edrqZyttbvGBY5BYED+\nfwLfInr1iOq6mpzBW8YZIHIrkiPnPyHhBn4mJSfoYM4MoGt2IgC7AvQToGL0pUUk\n6NOomXXx562kT7mPRQIDAQAB\n-----END PUBLIC KEY-----'''
#Data = json.loads(jsonString)
#print(Data['testing2']['READ'])


#0x921b017a6336e21cb4ad2dc21024cae26a120b44
#'0x3446f1acaa336ecccfcc5391e94d6235fd8372a0'
#print(Web3.toText(hexstr = Web3.toHex(root.GetAccountDetails(0, 0, transact={'from': web3.eth.accounts[0]}))))
#print(root.GetAccountDetails(0, 0))