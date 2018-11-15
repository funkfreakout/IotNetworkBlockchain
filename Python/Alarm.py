from pyfirmata import Arduino, util
import time

class Alarm:

	def __init__(self, pin, port):
		print('initializing Alarm...')
		self.pin = pin
		self.board = Arduino(port)

	def Buzz(self, count):
		print('Buzzing ' + str(count) + ' times')
		for x in range(count):
			self.board.digital[self.pin].write(1)
			time.sleep(0.2)
			self.board.digital[self.pin].write(0)
			time.sleep(0.2)