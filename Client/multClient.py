# Skrivet av Felix Söderman
# Designad av Felix Söderman & Carl Nordengren
import socket
import time
from enum import Enum
import curses

class GameState(Enum):
	QuitInQueue = 0
	NotStarted = 1
	isRunning = 2
	isOver = 3
	Error = 4

TIMEOUT = 1 # seconds
class connManager():
	def __init__(self,clientSocket,address):
		self.clientSocket = clientSocket
		self.address = address
		self.segDig = 0
		self.status = GameState.NotStarted
		self.result = ""
		self.output = ""
		self.keybinds ={
			"0":"0",
			"b":"b",
			"w":"w",
			"a":"a",
			"s":"s",
			"d":"d",
			"q":"q",
			"e":"e",
			"p":"p",
			"x":"x",
			" ":" "
		}
		clientSocket.settimeout(TIMEOUT)

	def getResult(self):
		if self.result == "1":
			return "Congrats you won!!!"
		elif self.result == "0":
			return "You lost, Better luck next time"
		else:
			raise(ValueError("Error: invalid result")) 

	def sendRequest(self,data):
		attemtps = 0
		while True:
			try:
				self.sendData(self.clientSocket,self.address,self.keybinds[data]) # Send one keypress
				data = self.clientSocket.recvfrom(4096)[0].decode() # Recive 0 or 1 depending on if the game is over.
				self.clientSocket.settimeout(TIMEOUT)
				break
			except socket.error:
				#No answer (This means packet was lost on its way there (or reply was lost). Resend with same segDig)
				attemtps += 1
				self.clientSocket.settimeout(attemtps*2) # Timeoutes are 1,2,4,8 sek
				if(attemtps > 3):
					raise(TimeoutError("Connection lost after 3 retransmissions"))
				continue

		if(data[-1] != str(self.segDig)):
			# Old respose => Ignore
			return
		self.segDig = (self.segDig + 1) % 10 # 0,1,2,3,4,5,6,7,8,9
		status = data[0]
		data = data[1:-1]
			
		# Game State Update
		if(status == "0"): # Two players have not yet connected please wait
			self.status = GameState.NotStarted
		elif(status == "1"): # Game is running
			self.status = GameState.isRunning
			self.output = self.parseNewData(data)
		elif(status == "2"): # Game is over
			self.status = GameState.isOver
			self.result = data[0]
		elif(status == "3"): # Left in the queue
			self.status = GameState.QuitInQueue
		else: #Not a valid value for header field
			self.status = GameState.Error
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

	def recvPlayerData(self,output,data):
		# Player
		playerx = int(data[:2])
		playery = int(data[2:4])
		output[playery][playerx] = str("P")

		# Player health
		health = data[4]
		# Player loaded
		loaded = data[5]
		# Player ammo
		ammo = str(int(data[6:8])) # This can remove padded zeros
		return output,int(health),int(loaded),int(ammo)

	def recvItemData(self,output,data):
		#Ammo
		amountOfAmmo = int(data[0])
		data = data[1:]
		for _ in range(amountOfAmmo):
			x = int(data[:2])
			y = int(data[2:4])
			data = data[4:]
			output[y][x] = "A"
		#Health
		amountOfHealth = int(data[0])
		data = data[1:]
		for _ in range(amountOfHealth):
			x = int(data[:2])
			y = int(data[2:4])
			data = data[4:]
			try:
				output[y][x] = "H"
			except IndexError as e:
				raise(IndexError("X="+str(x)+" Y="+str(y)+" "+str(e)))

		# Vertical Projectiles 
		amountOfVertShots = int(data[:2])
		data = data[2:]
		for _ in range(amountOfVertShots):
			x = int(data[:2])
			y = int(data[2:4])
			data = data[4:]
			output[y][x] = "|"

		# Horizontal Projectiles 
		amountOfHoriShots = int(data[:2])			
		data = data[2:]
		for _ in range(amountOfHoriShots):
			x = int(data[:2])
			y = int(data[2:4])
			data = data[4:]
			output[y][x] = "-"

		if(data != ""):
			raise(ValueError("DATA NOT EMPTY AFTER READING ALL"+data))
		return output

	def generateGUI(self,health:int,loaded:int,ammo:int,sizeY,output):
		#Adding GUI with health and Ammo 
		output[sizeY-2][1] = "A"# "🔫"
		output[sizeY-2][2] = ":"
		output[sizeY-2][3] = str(loaded)
		output[sizeY-2][4] = "/"
		if(ammo <= 9):
			output[sizeY-2][5] = str(ammo)		
			output[sizeY-2][6] = " "
		else:
			output[sizeY-2][5] = str(ammo//10)
			output[sizeY-2][6] = str(ammo%10)
		output[sizeY-2][8] = "♡"
		output[sizeY-2][10] = ":"
		output[sizeY-2][11] = str(health)
		#output[sizeY-2][11] = "/"
		#output[sizeY-2][12] = "3"
		return output

	def parseNewData(self,data):
		sizeX = 40
		sizeY = 22
		output = self.generateMap(sizeX,sizeY)
		output,health,loaded,ammo = self.recvPlayerData(output,data[:8])
		data = data[8:]
		
		# Opponant 
		opponentx = int(data[:2])
		opponenty = int(data[2:4])
		data = data[4:]
		
		output[opponenty][opponentx] = str("O")
		output = self.recvItemData(output,data)
		output = self.generateGUI(health,loaded,ammo,sizeY,output)

		string = ""
		for row in output:
			string += "".join(row) + "\n"
		return string

	def sendData(self,clientSocket,address,data):
		clientSocket.sendto(str.encode(data+str(self.segDig)),address)

FRAMEDELAY = 17
def updateScreen(screen,t_ms,connMann):
	screen.erase()
	try:
		screen.addstr(connMann.output)
	except:
		# Will crash if curses cant print to screen (This can happen when resizing the window to small for example)
		connMann.sendRequest("p") # Send kill me to the server.
	delay = max(FRAMEDELAY - (int(time.time() * 1000) - t_ms),0)
	curses.napms(delay)
	screen.refresh()

def filterKeyPress(Key):
	if(Key != -1 and chr(Key).lower() in ["w","a","s","d","e","q","p"," "]):
		return chr(Key).lower()
	else:
		return "b"

def gameLoop(screen,clientSocket,address):
	curses.cbreak()   # Turn off cbreak mode
	curses.echo(False)		 # Turn echo back on
	curses.curs_set(False)	# Turn cursor back on
	#screen.addstr("Press q...")
	screen.nodelay(True)
	manager = connManager(clientSocket,address)
	while True:
		if manager.status == GameState.QuitInQueue:
			screen.erase()
			screen.addstr("\n You left the queue\n")
			screen.refresh()
			curses.napms(5000)
			curses.endwin()
			return

		#Game has not started yet	
		if manager.status == GameState.NotStarted:
			screen.erase()
			screen.addstr("Waiting for another player or another game to end")
			screen.refresh()
			
			c = screen.getch() # Get keypress from player
			manager.sendRequest(filterKeyPress(c))
			
			curses.napms(500)
			continue

		# Game is running
		elif manager.status == GameState.isRunning:
			t_ms = int(time.time() * 1000)
			#Game is running
			
			c = screen.getch() # Get keypress from player
			manager.sendRequest(filterKeyPress(c))
			
			updateScreen(screen,t_ms,manager)
			
		# Game is over
		elif manager.status == GameState.isOver:
			# The game is over no more need to send packets
			break

	#Game is over present the winner to the client
	screen.erase()
	screen.addstr("\n"+manager.getResult()+"\n")
	screen.refresh()
	curses.napms(5000)
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
	defaultPORT = 5555

	useDefault = input("Do you want to use default host and port(" + defaultIP + ":" + str(defaultPORT) + ")?(Y/n): ")
	useDefault = "Y"
	host = getHost(useDefault,defaultIP)
	port = getPort(useDefault,defaultPORT)
	address = (host,port)

	clientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
	#clientSocket.settimeout(5)
	print("Connected")
	curses.wrapper(gameLoop,clientSocket,address)
	clientSocket.close()
	print("Disconnected")
main()

#