# Felix Söderman
import socket
import curses

class connManager():
	def __init__(self):
		self.inputBuffer = []
		self.isRunning = True
		self.result = "None"
		#self.playerID = playerID
		self.output = "Welcome Player:"

	def getWinner(self):
		if self.result == "1":
			return "Congrats you won"
		elif self.result == "0":
			return "Better luck next time"
		elif self.result == None:
			return "ITS NONE"
		return "HOW DID YOU GET HERE WAT????: " + str(self.result)

	def recvNewData(self,clientSocket):
		self.sendData(clientSocket) # Send one keyboard command
		data = clientSocket.recv(1).decode() # Recive 0 or 1 depending on if the game is over.
		if data == "1":
			self.output = self.parseNewData(clientSocket)
		elif data == "0":
			self.result = clientSocket.recv(1).decode()
			self.isRunning = False
		else:
			self.isRunning = False
			raise(ValueError("Not read correctly:" + str(data)))

	def generateMap(self,sizeX,sizeY):
		BG = " "
		output = []
		for i in range(sizeY):
			row = []
			row.extend(sizeX*BG)
			output.append(row)

		# Add barriers
		for i in range(5):
			output[4][17+i] = "%"	
			output[sizeY-3-4][17+i] = "%"	

		# Add Boarders
		for i in range(sizeX):
			output[0][i] = "%"	
			output[sizeY-3][i] = "%"	
			output[sizeY-1][i] = "%"	
		for i in range(sizeY):
			output[i][0] = "%"	
			output[i][sizeX-1] = "%"	

		return output

	def recvPlayerData(self,clientSocket,output):
		# Player
		playerx = int(clientSocket.recv(2).decode())
		playery = int(clientSocket.recv(2).decode())
		output[playery][playerx] = str("P")

		# Player health
		health = clientSocket.recv(1).decode()
		# Player loaded
		loaded = clientSocket.recv(1).decode()
		# Player ammo
		ammo = str(int(clientSocket.recv(2).decode()))
		return output,health,loaded,ammo

	def recvItemData(self,clientSocket,output):
		#Ammo
		amountOfAmmo = int(clientSocket.recv(1).decode())
		for _ in range(amountOfAmmo):
			x = int(clientSocket.recv(2).decode())
			y = int(clientSocket.recv(2).decode())
			output[y][x] = "A"

		#Health
		amountOfHealth = int(clientSocket.recv(1).decode())
		for _ in range(amountOfHealth):
			x = int(clientSocket.recv(2).decode())
			y = int(clientSocket.recv(2).decode())
			output[y][x] = "H"

		#Projectiles
		amountOfShots = int(clientSocket.recv(1).decode())
		for _ in range(amountOfShots):
			x = int(clientSocket.recv(2).decode())
			y = int(clientSocket.recv(2).decode())
			dir = clientSocket.recv(1).decode()
			if(dir == "n"):
				output[y][x] = "|"
			else:
				output[y][x] = "-"
		return output

	def generateGUI(self,health,loaded,ammo,sizeX,sizeY,output):
		#Adding GUI with health and Ammo 
		output[sizeY-2][1] = "A"# "🔫"
		output[sizeY-2][2] = ":"
		output[sizeY-2][3] = str(loaded)
		output[sizeY-2][4] = "/"
		output[sizeY-2][5] = str(ammo)

		output[sizeY-2][7] = "♡"
		output[sizeY-2][8] = ":"
		output[sizeY-2][9] = str(health)
		output[sizeY-2][10] = "/"
		output[sizeY-2][11] = "3"
		return output

	def parseNewData(self,clientSocket):
		sizeX = 40
		sizeY = 22
		output = self.generateMap(sizeX,sizeY)

		output,health,loaded,ammo = self.recvPlayerData(clientSocket,output)
		# Opponant 
		opponentx = int(clientSocket.recv(2).decode())
		opponenty = int(clientSocket.recv(2).decode())
		output[opponenty][opponentx] = str("O")
	
		output = self.recvItemData(clientSocket,output)
		
		output = self.generateGUI(health,loaded,ammo,sizeX,sizeY,output)

		string = ""
		for row in output:
			string += "".join(row) + "\n"
		return string

	def sendData(self,clientSocket):
		if(len(self.inputBuffer) >= 1):
			clientSocket.send(str.encode(self.inputBuffer[0]))
			self.inputBuffer = self.inputBuffer[1:]
		else:
			clientSocket.send(str.encode("0"))
	
	def addToBuffer(self,cmd):
		if(len(self.inputBuffer) > 2):
			self.inputBuffer = self.inputBuffer[1:]
			raise(ValueError("List to long"))
		if(cmd == "w"):
			self.inputBuffer.append("w")
		if(cmd == "a"):
			self.inputBuffer.append("a")
		if(cmd == "s"):
			self.inputBuffer.append("s")
		if(cmd == "d"):
			self.inputBuffer.append("d")
		if(cmd == "q"):
			self.inputBuffer.append("q")
		if(cmd == "e"):
			self.inputBuffer.append("e")
		if(cmd == " "):
			self.inputBuffer.append(" ")
		if(cmd == "p"):
			self.inputBuffer.append("p")

def updateScreen(screen,string):
	try:
		screen.addstr(string)
	except:
		return False
	screen.refresh()
	screen.erase()
	curses.napms(100)

def gameLoop(screen,clientSocket):
	curses.cbreak()   # Turn off cbreak mode
	curses.echo(False)		 # Turn echo back on
	curses.curs_set(False)	# Turn cursor back on
	#screen.addstr("Press q...")
	screen.nodelay(True)
	manager = connManager()
	
	screen.addstr("Waiting for another player")
	screen.refresh()
	clientSocket.settimeout(None)
	data = clientSocket.recv(1).decode()
	if(data != "g"):
		raise(ValueError("ERROR at wait:"+str(data)))
	clientSocket.settimeout(5)

	screen.erase()
	screen.refresh()
	while True:
		if(not manager.isRunning):
			clientSocket.send(str.encode("done"))
			data = clientSocket.recv(1024).decode()
			if(data == "killed"):
				break
			continue
		c = screen.getch() 
		try:
			if(chr(c).lower() in ["w","a","s","d","e","q","p"," "]):
				manager.addToBuffer(chr(c).lower())
		except ValueError: # catches when chr(c) isn't defined(no key is pressed)
			pass
		manager.recvNewData(clientSocket)
		if (updateScreen(screen,manager.output)):
			manager.isRunning = False
	screen.erase()
	screen.addstr("\n"+manager.getWinner()+"\n")
	screen.refresh()
	curses.napms(1000)
	curses.endwin()

def getHost(useDefault,default):
	if(useDefault.lower() == "n"):
		return input("Please enter the host(IPv4 address in dotted decimal (xxx.xxx.xxx.xxx): ")
	return default

def getPort(useDefault,default):
	if(useDefault.lower() == "n"):
		return int(input("Please enter the port(0-65535): "))
	return default

def main():
	
	defaultIP = "0.0.0.0"
	defaultPORT = 18888

	#useDefault = input("Do you want to use default host and port(" + defaultIP + ":" + str(defaultPORT) + ")?(Y/n): ")
	useDefault = "Y"
	host = getHost(useDefault,defaultIP)
	port = getPort(useDefault,defaultPORT)
	clientSocket = socket.socket()
	print('Connecting')
	try:
		clientSocket.connect((host, port))
	except socket.error as e:
		print(str(e))
	clientSocket.settimeout(5)
	print("Connected")
	curses.wrapper(gameLoop,clientSocket)
	clientSocket.close()
	print("Disconnected")
main()
