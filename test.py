numPlayers = 4
currentPlayer = 4

clockwise = False

if clockwise:
    currentPlayer = (currentPlayer % numPlayers) + 1
else:
    currentPlayer = (currentPlayer - 2) % numPlayers + 1
    
print(currentPlayer)