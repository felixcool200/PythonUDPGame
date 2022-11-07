# Skrivet av Felix Söderman
# Designad av Felix Söderman & Carl Nordengren
import socket
import time
from enum import Enum
import random

# TODO
# Check for collision with crates
BG = " "
sizeX = 40
sizeY = 22
class Direction(Enum):
	North = 1
	East = 2
	South = 3
	West = 4

class Player():
	def __init__(self,playerID,address):
		self.ID = playerID
		if(playerID == 0):
			self.x = 19 #(40-2)/2
			self.y = 2
		else:
			self.x = 19
			self.y = 17 #20-3
		self.address = address
		self.latestInput = ""
		self.lastsegDigit = None
		self.lastPacketRecived = int(time.time() * 1000)
		self.disconnected = False
		self.loaded = 3
		self.ammo = 3
		self.health = 3
		self.dir = Direction.North
		self.looking = False
		self.quit = False
		
	def move(self,dx,dy):
		if (not isInWall(self.x + dx,self.y + dy)):
			self.y += dy
			self.x += dx

	def hit(self,shot):
		self.health -= shot.damage
		if(self.health <= 0):
			self.quit = True

	def update(self,data,world):
		if(data == "w"):
			#print("Moving player" + str(self.ID) + " upwards")
			self.dir = Direction.North
			self.move(0,-1)
		elif(data == "a"):
			#print("Moving player" + str(self.ID) + " left")
			self.dir = Direction.West
			self.move(-1,0)
		elif(data == "s"):
			#print("Moving player" + str(self.ID) + " down")
			self.dir = Direction.South
			self.move(0,1)
		elif(data == "d"):
			#print("Moving player" + str(self.ID) + " right")
			self.dir = Direction.East
			self.move(1,0)
		elif(data == "e"):
			#print("Using pickup from player" + str(self.ID))
			self.checkItemNearby()
		elif(data == "q"):
			#print("Using reload from player" + str(self.ID))
			self.reload()
		elif(data == " "):
			#print("Shooting from player" + str(self.ID))
			self.shoot(world)
		elif(data == "p"):
			self.quit = True
			print("Player" + str(self.ID) + " gave up")
		elif(data == "b"):
			# Do nothing since this is a update world message
			pass
		else:
			return 
		if(data != "e"):
			self.looking = False
		#print("pos: ", self.x,self.y)

	def shoot(self,world):
		if(self.loaded >= 1):
			world.listOfShots.append(Shot(self.x,self.y,self.dir,self.ID))
			self.loaded -= 1	

	def reload(self):
		if(self.ammo > 0 and self.loaded < 3):
			toload = min(self.ammo,3-self.loaded)
			self.ammo -= toload
			self.loaded += toload

	def checkItemNearby(self):
		self.looking = True

	def addAbility(self,ability):
		if(ability == "ammo"):
			if(self.ammo < 93):
				self.ammo += 6
			else:
				self.ammo == 99
		elif(ability == "health"):
			if(self.health < 9):
				self.health += 1

class Shot():
	def __init__(self,x,y,direction,ID,damage=1):
		self.x = x
		self.y = y
		self.dir = direction
		self.damage = damage
		self.shotByID = ID

	def collision(self,sizeX, sizeY,p):
		# Player
		if(self.x == p.x and self.y == p.y):
			return True
		
		# Barrier
		if((self.y == 4 or self.y == 15) and self.x in range(17,22)):
			return True

		#Border
		if(self.x == 0 or self.y == 0):
			return True
		if(self.x == sizeX or self.y == sizeY):
			return True

		return False

	def move(self):
		if(self.dir == Direction.North):
			self.y -= 1
		if(self.dir == Direction.West):
			self.x -= 1
		if(self.dir == Direction.South): 
			self.y += 1
		if(self.dir == Direction.East):
			self.x += 1

class Item:
	def __init__(self,x,y,icon,ability):
		self.x = x
		self.y = y
		self.icon = icon
		self.ability = ability

	def inrange(self,x,y):
		if(abs(self.x - x) == 1 and abs(self.y - y) == 0):
			return True
		elif(abs(self.x - x) == 0 and abs(self.y - y) == 1):
			return True
		return False

class GameLogic():
	def __init__(self):
		self.players = [None,None]
		self.firstPlayersTurn = False
		self.listOfItems = []
		self.listOfShots =  []
	
	def worldInformation(self,players,ID):
		output = ""
		# Player
		output += str("%02d" % (players[ID].x, ))
		output += str("%02d" % (players[ID].y, ))

		# player health
		output += str(players[ID].health)
		# player loaded
		output += str(players[ID].loaded)
		# player ammo
		output += str("%02d" % (players[ID].ammo, ))

		# Opponant
		OpponantID = (ID+1) % 2
		output += str("%02d" % (players[OpponantID].x, ))
		output += str("%02d" % (players[OpponantID].y, ))

		# Ammo
		output += str(len([x for x in self.listOfItems if x.icon == "A"]))
		for item in self.listOfItems:
			if(item.icon == "A"):
				output += str("%02d" % (item.x, ))
				output += str("%02d" % (item.y, ))

		# Health
		output += str(len([x for x in self.listOfItems if x.icon == "H"])) 
		for item in self.listOfItems:
			if(item.icon == "H"):
				output += str("%02d" % (item.x, ))
				output += str("%02d" % (item.y, ))

		# Vertical Projectiles
		VertList = [x for x in self.listOfShots if x.dir in [Direction.North,Direction.South]]
		output += str("%02d" % (len(VertList), ))
		for shot in VertList:
			output += str("%02d" % (shot.x, ))
			output += str("%02d" % (shot.y, ))
		# Horizontal Projectiles 
		
		HoriList = [x for x in self.listOfShots if x.dir in [Direction.East,Direction.West]]
		output += str("%02d" % (len(HoriList), ))
		for shot in HoriList:
			output += str("%02d" % (shot.x, ))
			output += str("%02d" % (shot.y, ))
		return output

	def isFree(self,x,y):
		# Shots
		for i in self.listOfShots:
			if(i.x == x and i.y == y):
				return False
		
		# Items 
		for i in self.listOfItems:
			if(i.x == x and i.y == y):
				return False
		
		# Players
		for i in self.players:
			if(i.x == x and i.y == y):
				return False
		
		# Walls
		if(isInWall(x,y)):
			return False
		
		return True

	def update(self,key:str,ID:int) -> bool:

		# Game is not over it just hasn't begun	
		if(not self.twoPlayersConnected()):
			return

		# The game is over
		if(self.players[0].quit or self.players[1].quit):
			return

		# Send the keybind to the player
		self.players[ID].update(key,self)
		
		self.checkForPlayerPickup()
		self.updateBullets(ID) 
		self.tryToGenerateCrate()

	def checkForPlayerPickup(self) -> None:
		for player in self.players:
			if(player.looking == True):
				for item in self.listOfItems:
					if(item.inrange(player.x,player.y)):
						player.addAbility(item.ability)
						self.listOfItems.remove(item)
				player.looking = False

	def updateBullets(self,ID:int) -> None:
		for shot in self.listOfShots:
			if(shot.shotByID == ID):
				shot.move()
				if(shot.collision(sizeX-1, sizeY-3, self.players[(ID + 1) % 2])):
					for player in self.players:
						if((shot.x,shot.y) == (player.x,player.y)):
							player.hit(shot)
							print("Player " + str(player.ID) + " shot health:" + str(player.health)) 
					self.listOfShots.remove(shot)

	def tryToGenerateCrate(self) -> None:
		if (len(self.listOfItems) <= 9 and random.randint(0,300) == 1):
			sgn = lambda x : (x > 0) - (x < 0)
			dropType = ("health","ammo")[sgn(random.randint(0,5))] # This makes ammo 5 times more likley
			icon = dropType[0].upper()
			x,y = 0,0
			tries = 0
			while tries <= 10:
				y = random.randint(7,sizeY-1-9)
				x = random.randint(0,sizeX-1)
				if(self.isFree(x,y)):
					break
				tries += 1
			else: # Only called of tries > 10
				return
			print("New item at: " + str(x) + ", " + str(y) + " type: " + str(dropType))
			self.listOfItems.append(Item(x,y,icon,dropType))

	def twoPlayersConnected(self):
		return (self.players[0] != None and self.players[1] != None)
	
	def playersDisconnected(self):
		return self.players[0].disconnected == True and self.players[1].disconnected == True

	def running(self):
		if(not (None in self.players)):
			return (self.players[0].quit == False and self.players[1].quit == False)
		return False

def isInWall(x,y):
	
	# Barrier
	if((y == 4 or y == 15) and x in range(17,22)):
		return True

	#Border
	if(x <= 0 or y <= 0):
		return True
	if(x >= sizeX-1 or y >= sizeY-3):
		return True

	return False	

def getResponseString(world:GameLogic,playerID:int) -> str:
	# Generate a response payload for a client
	# 0 => Waiting for another player
	# 1 => Game is running (followed by game data)
	# 2 => Game has ended (followed by result)
	reply = ""
	if(not world.twoPlayersConnected()):
		return "0"

	if(world.running()):
		reply = "1"
		reply += world.worldInformation(world.players,playerID)
	else:
		reply += "2"
		if(world.players[playerID].quit): # If playerID lost/surrenderd send lost (0)
			reply += "0"
		else: # If the other player lost/surrenderd send won (1)
			reply += "1"
	return reply


def checkPlayerID(world,address):
	if(world.players[0] == None):
		print("Player 0 Connected")
		world.players[0] = Player(0,address)
		return 0
	elif(world.players[0].address != address and world.players[1] == None):
		print("Player 1 Connected")
		world.players[1] = Player(1,address)
		return 0
	else:
		if(world.players[0].address == address):
			return 0
		elif(world.players[1].address == address):
			return 1
		else:
			print(f"Game is running. Player att {address} in queue")
			return None

def sendString(socket,address, string):
	#print("Sending:",string,"to",str(address))
	socket.sendto(str.encode(string), address)

TIMEOUT_MS = 10*1000 # 10 seconds
def handleRequest(world,key,address,segDig):
	# Check for timeout
	t_ms = int(time.time() * 1000)
	for playerID in range(len(world.players)):
		if(world.players[playerID] == None):
			continue
		elif(t_ms - world.players[playerID].lastPacketRecived >= TIMEOUT_MS):
			# Player has hade a timeout. That player lost
			print(f"==================== TIMEOUT FOR PLAYER {playerID} ====================")
			world.players[playerID].disconnected = True 
	
	# Set playerID
	playerID = checkPlayerID(world,address)
	if(playerID == None):
		#Server full. Send waiting for other player until the server is available
		if(key == "p"):
			print("Player in queue left the game")
			return "3"
		return "0"

	#Change latest recived packet from Player
	world.players[playerID].lastPacketRecived = int(time.time() * 1000)

	# See if the client ask for new packet
	if((world.players[playerID].lastsegDigit == '9' and segDig != '0') and\
		(world.players[playerID].lastsegDigit != None and chr(ord(world.players[playerID].lastsegDigit)+1) != segDig)):
		# Resend latest world (The button has already beed registerd but packet lost on the way)
		print("Same segDigit for player",playerID)
		return getResponseString(world,playerID)


	# Update latest recived message
	world.players[playerID].lastsegDigit = segDig
	
	if(key != "b"):
		world.players[playerID].latestInput = key
	
	# Check what players turn it is and update the world
	currentInput = world.players[playerID].latestInput
	if (world.firstPlayersTurn and playerID == 0) or (not world.firstPlayersTurn and playerID == 1):
		world.update(currentInput,playerID)
		world.players[playerID].latestInput = None
		world.firstPlayersTurn = not world.firstPlayersTurn
	elif (world.firstPlayersTurn == False and playerID == 0) and (world.firstPlayersTurn == True and playerID == 1):
		print(f"Player {playerID}, not your turn (saving keystroke).")
	return getResponseString(world,playerID)

def main():
	serverSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
	host = ''
	port = 5555

	#Try to open a connection
	try:
		serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		serverSocket.bind((host, port))
	except socket.error as e:
		print(str(e))

	world = GameLogic()
	while(True):
		message, address = serverSocket.recvfrom(3)
		message = message.decode()
		key, segDig = message
		output = handleRequest(world,key,address, segDig)
		sendString(serverSocket,address,output + segDig)
		# If Both players have timeout (could be from reciving result respose)
		if(world.playersDisconnected()):
			world = GameLogic()
			print("Server reset for next game")
main()