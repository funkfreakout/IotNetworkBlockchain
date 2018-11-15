from Alarm import Alarm

class PermissionedAlarm(Alarm):

	Min_Number_of_Buzzing = "Number"
	Max_Number_of_Buzzing = "Number"
	
	def __init__(self, pin, ArduinoPort):
		Alarm.__init__(self, pin, ArduinoPort)

	def FetchPermissionTable():
		table = {}
		table['Min_Number_of_Buzzing'] = Min_Number_of_Buzzing
		table['Max_Number_of_Buzzing'] = Max_Number_of_Buzzing
		return table

