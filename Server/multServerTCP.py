# Felix Söderman
import socket
#import os
import _thread
import random

"""
p1x p1y p2x p2y
player health
player loaded
player ammo
N = len(shots)
shot1x shot1y
...
shotNx shotNy

L = len(Ammo)
ammo1x ammo1y
...
ammoLx ammoLy

G = len(Health)
health1x health1y
...
healthGx healthGy
"""
BG = " "

class Player():
	def __init__(self,playerID,x,y):
		self.ID = playerID
		self.x = x
		self.y = y
		self.loaded = 3
		self.ammo = 3
		self.dir = "North"
		self.health = 3
		self.looking = False
		self.quit = False
		
	def move(self,dx,dy):
		if (not world.getCollision(self.x + dx,self.y + dy)):
			self.y += dy
			self.x += dx

	def hit(self,shot):
		self.health -= shot.damage
		if(self.health <= 0):
			self.quit = True

	def update(self,data):
		if(data == "w"):
			#print("Moving player" + str(self.ID) + " upwards")
			self.dir = "North"
			self.move(0,-1)
		elif(data == "a"):
			#print("Moving player" + str(self.ID) + " left")
			self.dir = "West"
			self.move(-1,0)
		elif(data == "s"):
			#print("Moving player" + str(self.ID) + " down")
			self.dir = "South"
			self.move(0,1)
		elif(data == "d"):
			#print("Moving player" + str(self.ID) + " right")
			self.dir = "East"
			self.move(1,0)
		elif(data == "e"):
			#print("Using pickup from player" + str(self.ID))
			self.checkItemNearby()
		elif(data == "q"):
			#print("Using reload from player" + str(self.ID))
			self.reload()
		elif(data == " "):
			#print("Shooting from player" + str(self.ID))
			self.shoot()
		elif(data == "p"):
			print("Player" + str(self.ID) + " gave up")
		else:
			return
		#print("pos: ", self.x,self.y)

	def shoot(self):
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
		if(self.dir == "North"):
			self.y -= 1
		if(self.dir == "West"):
			self.x -= 1
		if(self.dir == "South"): 
			self.y += 1
		if(self.dir == "East"):
			self.x += 1
		return False

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
		self.listOfItems = []
		self.listOfShots =  []
		self.output = None
		self.sizeX = 40
		self.sizeY = 22
	
	def __str__(self):
		output = ""
		for row in self.output:
			output += "".join(row) + "\n"
		return output

	
	def worldInformation(self,players,ID):
		output = ""

		# Player
		output += str("%02d" % (players[ID - 1].x, ))
		output += str("%02d" % (players[ID - 1].y, ))

		# player health
		output += str(players[ID - 1].health)
		# player loaded
		output += str(players[ID - 1].loaded)
		# player ammo
		output += str("%02d" % (players[ID - 1].ammo, ))

		# Opponant
		OpponantID = ID % 2
		output += str("%02d" % (players[OpponantID].x, ))
		output += str("%02d" % (players[OpponantID].y, ))

		# Ammo
		output += str(len([x for x in self.listOfItems if x.icon == "A"]))  # When using only 'if', put 'for' in the beginning
		for item in self.listOfItems:
			if(item.icon == "A"):
				output += str("%02d" % (item.x, ))
				output += str("%02d" % (item.y, ))

		# Health
		output += str(len([x for x in self.listOfItems if x.icon == "H"]))  # When using only 'if', put 'for' in the beginning
		for item in self.listOfItems:
			if(item.icon == "H"):
				output += str("%02d" % (item.x, ))
				output += str("%02d" % (item.y, ))

		# Projectiles
		output += str(len(self.listOfShots))
		for shot in self.listOfShots:
			output += str("%02d" % (shot.x, ))
			output += str("%02d" % (shot.y, ))
			if(shot.dir in ["North","South"]):
				output += "n"
			else:
				output += "w"
		return output

	def getCollision(self,x,y):
		if (x >= 0 and x < self.sizeX):
			if(y >= 0 and y < self.sizeY):
				return self.output[y][x] != BG
		return True

	def update(self,data,ID):	
		if(not self.twoPlayersConnected()):
			return
	
		self.players[ID-1].update(data)
		for player in self.players:
			if(player.looking == True):
				for item in self.listOfItems:
					if(item.inrange(player.x,player.y)):
						player.addAbility(item.ability)
						self.listOfItems.remove(item)
			player.looking = False

		for shot in self.listOfShots:
			if(shot.shotByID == ID):
				shot.move()
				if(shot.collision(self.sizeX-1, self.sizeY-3, world.players[ID % 2])):
					for player in self.players:
						if(self.output[shot.y][shot.x] == str(player.ID)):
							player.hit(shot)
							print("Player " + str(player.ID) + " shot health:" + str(player.health)) 
					self.listOfShots.remove(shot)
		
		if (len(self.listOfItems) <= 9 and random.randint(0,300) == 1):
			dropType = ("ammo","health")[random.randint(0,1)]			
			icon = dropType[0].upper()
			x,y = 0,0
			tries = 0
			while self.output[y][x] != BG and tries <= 10:
				y = random.randint(7,self.sizeY-1-9)
				x = random.randint(0,self.sizeX-1)
				tries += 1
			if tries <= 10:
				print("New item at: " + str(x) + ", " + str(y) + " type: " + str(dropType))
				self.listOfItems.append(Item(x,y,icon,dropType))
	
		self.genBoard()

	def twoPlayersConnected(self):
		return (self.players[0] != None and self.players[1] != None)
	
	def genBoard(self):
		self.output = []
		for i in range(self.sizeY):
			row = []
			row.extend(self.sizeX*BG)
			self.output.append(row)

		# Add barriers
		for i in range(5):
			self.output[4][17+i] = "%"	
			self.output[self.sizeY-3-4][17+i] = "%"	

		# Add Boarders
		for i in range(self.sizeX):
			self.output[0][i] = "%"	
			self.output[self.sizeY-3][i] = "%"	
			self.output[self.sizeY-1][i] = "%"	
		for i in range(self.sizeY):
			self.output[i][0] = "%"	
			self.output[i][self.sizeX-1] = "%"	

		for item in self.listOfItems:
			self.output[item.y][item.x] = str(item.icon)
		for player in self.players:
			self.output[player.y][player.x] = str(player.ID)
		
		for shot in self.listOfShots:
			if(shot.dir in ["North","South"]):
				self.output[shot.y][shot.x] = "|"
			else:
				self.output[shot.y][shot.x] = "-"
	
	def running(self):
		if(not (None in self.players)):
			return (self.players[0].quit == False and self.players[1].quit == False)
		return False

world = GameLogic()

def threadedClient(connection,playerID):
	global world 
	#data = connection.recv(2048).decode()
	#playerID = int(str(data[1])) #Fromat p1 or p2
	# If two players are already playing
	if(world.players[playerID-1] != None):
		#connection.send(str.encode('error'+str(playerID)))
		connection.close()
		return
	x,y = 0,0
	if(playerID == 1):
		x = 19 #(40-2)/2
		y = 2
	else:
		x = 19
		y = 20-3
	world.players[playerID-1] = Player(playerID,x,y)
	#connection.send(str.encode('ok'))
	print("Player", playerID,"Connected")
	#Wait for the other player
	while(not world.twoPlayersConnected()):
		continue
	connection.sendall(str.encode("g")) #Send go
	
	while True:
		data = connection.recv(2048).decode()
		if(data == "done"):
			print("sent killed to player " + str(playerID))
			connection.sendall(str.encode("killed"))
			break
		if(not world.running() or not world.twoPlayersConnected()):
			print("sent gameover to player " + str(playerID))
			reply = "0"
			if(world.players[playerID-1].quit):
				reply += "0"
			else:
				reply += "1"  
			connection.sendall(str.encode(reply))
		else:
			world.update(data,playerID)
			#reply = str(world)
			if(data == "p"):
				reply = "0"
				world.players[playerID-1].quit = True
				#world.running()
				reply += "0"
			else:
				reply = "1"
				reply += world.worldInformation(world.players,playerID)
				#reply += addGUIforPlayer(world.output,playerID)
			print("Reply is:", reply)
			connection.sendall(str.encode(reply))
		#if not data:
			#break
	#Reset if both players are disconnectred
	world.players[playerID-1] = None
	if(world.players == [None,None]):
		world = GameLogic()
	connection.close()
	_thread.exit()


"""
def addGUIforPlayer(worldMap,ID):
	output = worldMap.copy()
	loaded = world.players[ID -1].loaded
	ammo = world.players[ID -1].ammo
	health = world.players[ID -1].health
	#Adding GUI with health and Ammo 
	output[world.sizeY-2][1] = "A"# "🔫"
	output[world.sizeY-2][2] = ":"
	output[world.sizeY-2][3] = str(loaded)
	output[world.sizeY-2][4] = "/"
	output[world.sizeY-2][5] = str(ammo)
	
	output[world.sizeY-2][7] = "♡"
	output[world.sizeY-2][8] = ":"
	output[world.sizeY-2][9] = str(health)
	output[world.sizeY-2][10] = "/"
	output[world.sizeY-2][11] = "3"
	string = ""
	for row in output:
		string += "".join(row) + "\n"
	return string
"""
def main():
	serverSocket = socket.socket()
	host = ''
	port = 18888
	player1Inputs = []
	player2Inputs = []

	try:
		serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		serverSocket.bind((host, port))
	except socket.error as e:
		print(str(e))

	serverSocket.listen(5)
	try:
		while True:
			client, address = serverSocket.accept()
			print('Connected to: ' + address[0] + ':' + str(address[1]))
			print('Thread Number: ' + str(_thread._count()+1))
			_thread.start_new_thread(threadedClient, (client, int(_thread._count()+1), ))
	except KeyboardInterrupt:
		serverSocket.close()

main()

#UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)