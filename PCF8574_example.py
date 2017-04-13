#!/usr/bin/python

import smbus
import time
import optparse
import re
class PCF8574(object):

	# open i2c bus
	bus = smbus.SMBus(1)

	# Open and read last state (so cli can keep track of state or if object is destroyed)
	try:
		with open('/tmp/i2cplay', 'rb') as statelogfile:
			statelog = statelogfile.read()

	#If there is no log file, create one
	except:
		with open('/tmp/i2cplay', 'wb') as statelogfile:
			statelog = ''

	# create a new object with the address of ic, state can be specified or logged state will be used
	def __init__(self, address, state=statelog):

		#If is state from log file extract the state for object's address with a regular expression, if state for object's addres isn't in log set state to 0
		if type(state) == str:
			try:
				state = int(re.findall(r'%s=(\d+)' % address, state)[0])
			except:
				state = 0

		#Address of IC
		self.address = address
		#Var to track state of ic
		self.state = state

	#Function to write state of object to logfile
	def writelog(self):
		#Check if objects address is already in logfile and replace with new state
		if re.findall(r'%s=(\d+)' % self.address, self.statelog):
			newstatelog = re.sub(r'%s=\d+' % self.address, '%s=%s' % (self.address, self.state), self.statelog)
			with open('/tmp/i2cplay', 'wb') as statelogfile:
				statelogfile.write(newstatelog)

		#If object's address is not in the logfile append address and state to log
		else:
			with open('/tmp/i2cplay', 'a') as statelogfile:
				statelogfile.write('%s=%s\n' % (self.address, self.state))


	#Function to write all 8 ports open
	def writeall(self):
		self.bus.write_byte(self.address, 255)
		self.state = 255
		self.writelog()
		return self.state

	#Function to close all ports
	def closeall(self):
		self.bus.write_byte(self.address, 0)
		self.state = 0
		self.writelog()
		return self.state

	#Function to changes individual port on or off
	def portchange(self, port, mode):
		#Ensure valid arguements are passed if not raise an exception
		if not port in [0,1,2,3,4,5,6,7]:
			raise Exception, 'Port number must be an integar between 0-7'
		if not mode in [True,False]:
			raise Exception, 'Mode must be True or False'

		#set port to position in bit representation
		if port == 0:
			port = 7
		elif port == 1:
			port = 6
		elif port == 2:
			port = 5
		elif port == 3:
			port = 4
		elif port == 4:
			port = 3
		elif port == 5:
			port = 2
		elif port == 6:
			port = 1
		elif port == 7:
			port = 0

		#get a 1 bit binary representation of current state
		binstatelist = list(bin(self.state)[2:].zfill(8))

		#replace binary digit for port which is changing state
		if mode == True:
			binstatelist[port] = '1'
		if mode == False:
			binstatelist[port] = '0'

		#Convert binary list to string
		binstate = ''.join(binstatelist)

		#Convert binary string to int
		self.state = int(binstate, 2)

		#Update IC to new state
		self.bus.write_byte(self.address, self.state)
		self.writelog()
		return self.state

	#Function to control different chaser effects
	def chaser(self, mode, duration=0.25):
		#Print message to user
		print 'Press Ctrl + C to stop the chaser'

		# Check a valid mode argument is specified, raise an exception if not
		if not mode in ['left', 'right' , 'bounce']:
			raise Exception, 'Mode must "left", "right" or "bounce"'
		#Check a valid duration is specified, raise an exception if not
		if not type(duration) is float and not type(duration) is int:
			raise Exception, 'Duration must be an whole or decimal number'

		#Function to chase outputs right
		def chase_right():
			#Initial byte to write
			y = 1
			# Loop the amount of port available (8)
			for x in range(0,8):
				#Activate port
				self.bus.write_byte(self.address, y)
				#Shift Byte one position
				y = y << 1
				#Leave port open for time specified
				time.sleep(duration)

		#Function to chase outputs left
		def chase_left():
			#Initial byte to write
			y = 128
			# Loop the amount of port available (8)
			for x in range(0,8):
				#Activate port
				self.bus.write_byte(self.address, y)
				#Shift Byte one position
				y = y >> 1
				#Leave port open for time specified
				time.sleep(duration)

		#Function to bounce outputs
		def bounce():
			y = 1
			# Loop 7 ports, port 8 will be on the return loop
			for x in range(0,7):
				#Activate port
				self.bus.write_byte(self.address, y)
				#Shift Byte one position
				y = y << 1
				#Leave port open for time specified
				time.sleep(duration)
			y = 128
			# Loop 7 ports back, port 1 is controlled on first loop
			for x in range(0,7):
				#Activate port
				self.bus.write_byte(self.address, y)
				#Shift Byte one position
				y = y >> 1
				#Leave port open for time specified
				time.sleep(duration)

		#Make infinate loop whist running chaser
		x = True
		while x == True:
			try:
				if mode == 'left':
					chase_left()
				elif mode == 'right':
					chase_right()
				elif mode == 'bounce':
					bounce()

			#If the user stops the chaser close all ports and break loop
			except KeyboardInterrupt:
				x = False
				self.bus.write_byte(self.address, 0)
				self.state = 0
				self.writelog()
				return self.state
# Create a commandline interface
def main():
	#Create option parser object
	p = optparse.OptionParser(description='Control PCF8574 8 bit IO expander via i2c bus',
		prog='i2cplay',
		version='i2cplay 1.0')

	#Create various options to control object
	p.add_option('--address', '-a', default=56, help= 'Set binary address of i2c device with a decimal representation [default: %default]')
	p.add_option('--function', '-f', default='writeall', choices=['writeall', 'closeall', 'portchange', 'chase_right', 'chase_left', 'bounce'], help="Specify what function you would like to perform. choices=['writeall', 'closeall', 'portchange', 'chase_right', 'chase_left', 'bounce']")
	p.add_option('--port', '-p', default=0, choices=['0','1','2','3','4','5','6','7'], help='Specify port number when switching ports (0-7)')
	p.add_option('--mode', '-m', default=True, help='When changing a port on or off specify True or False')
	p.add_option('--duration', '-d', default=0.25, help='When using functions that cycle switching ports (chaser, bounce etc) specify how long the port is on for' )

	#Parse options and arguments when script is run
	options, arguements = p.parse_args()

	#create the PCF8574 object
	obj = PCF8574(int(options.address))

	#Run the function specified by the user
	if options.function == 'writeall':
		obj.writeall()
	elif options.function == 'closeall':
		obj.closeall()
	elif options.function == 'chase_right':
		obj.chaser('right', float(options.duration))
	elif options.function  == 'chase_left':
		obj.chaser('left', float(options.duration))
	elif options.function  == 'bounce':
		obj.chaser('bounce', float(options.duration))
	elif options.function == 'portchange':
		if options.mode == 'True':
			mode = True
		else:
			mode = False
		obj.portchange(int(options.port), mode)

#Initialises the main function when script is initiated
if __name__ == '__main__':
	main()