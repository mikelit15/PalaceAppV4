import sys
import socket
import threading
import random
import json
import time
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,\
    QTextEdit, QGridLayout, QSpacerItem, QSizePolicy)
from PySide6.QtGui import QPixmap, QIcon, QTransform, QPainter
from PySide6.QtCore import Qt, QRect, QObject, Signal
import qdarktheme

# Dark Mode Styling
Dark = qdarktheme.load_stylesheet(
    theme="dark",
    custom_colors={
        "[dark]": {
            "primary": "#0078D4",
            "background": "#202124",
            "border": "#8A8A8A",
            "background>popup": "#252626",
        }
    },
) + """
    QMessageBox QLabel {
        color: #E4E7EB;
    }
    QDialog {
        background-color: #252626;
    }
    QComboBox:disabled {
        background-color: #1A1A1C; 
        border: 1px solid #3B3B3B;
        color: #3B3B3B;  
    }
    QPushButton {
    background-color: #0078D4; 
    color: #FFFFFF;           
    border: 1px solid #8A8A8A; 
    }
    QPushButton:hover {
        background-color: #669df2; 
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #80CFFF, stop:1 #004080);
    }
    QPushButton:pressed {
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                    stop:0 #004080, stop:1 #001B3D);
    }
    QPushButton:disabled {
        background-color: #202124; 
        border: 1px solid #3B3B3B;
        color: #FFFFFF;   
    }
"""

def centerDialog(dialog, parent, name=None):
    offset = 0
    if name == "playerSelectionDialog":
        offset = 100
    elif name == "rulesDialog":
        offset = 225

    if isinstance(parent, QRect):
        # Parent is a QRect (geometry object)
        parentCenterX = parent.center().x()
        parentCenterY = parent.center().y()
    elif isinstance(parent, QWidget):
        # Parent is a QWidget
        parentGeometry = parent.geometry()
        parentCenterX = parentGeometry.center().x()
        parentCenterY = parentGeometry.center().y()
    else:
        # Default to screen center if no parent is provided
        screenGeometry = QApplication.primaryScreen().geometry()
        parentCenterX = screenGeometry.center().x()
        parentCenterY = screenGeometry.center().y()

    dialogGeometry = dialog.geometry()
    dialogCenterX = dialogGeometry.width() // 2
    dialogCenterY = dialogGeometry.height() // 2

    newX = parentCenterX - dialogCenterX
    newY = parentCenterY - dialogCenterY - offset
    dialog.move(newX, newY)

# Constants for card dimensions
CARD_WIDTH = 56
CARD_HEIGHT = 84
BUTTON_WIDTH = 66
BUTTON_HEIGHT = 87

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
VALUES = {'3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,'J': 10, 'Q': 11, 'K': 12, 'A': 13, '2': 14, '10': 15}

### Home Screen ###
class HomeMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Palace")
        self.setWindowIcon(QIcon(r"_internal\palaceData\palace.ico"))
        self.setGeometry(660, 215, 600, 500)
        layout = QVBoxLayout()

        title = QLabel("Palace")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 36px; font-weight: bold;")
        layout.addWidget(title)

        buttonLayout = QVBoxLayout()

        buttonLayout.addWidget(QLabel(""))
        buttonLayout.addWidget(QLabel(""))
        
        playButton = QPushButton("Play")
        playButton.setFixedHeight(40)
        playButton.setFixedWidth(275)
        # playButton.clicked.connect(self.playLocalGame)
        buttonLayout.addWidget(playButton, alignment=Qt.AlignmentFlag.AlignCenter)

        buttonLayout.addWidget(QLabel(""))
        
        onlineButton = QPushButton("Play Online")
        onlineButton.setFixedWidth(225)
        onlineButton.clicked.connect(self.showOnlineMenu)
        buttonLayout.addWidget(onlineButton, alignment=Qt.AlignmentFlag.AlignCenter)

        buttonLayout.addWidget(QLabel(""))
        
        rulesButton = QPushButton("Rules")
        rulesButton.setFixedWidth(225)
        rulesButton.clicked.connect(self.showRules)
        buttonLayout.addWidget(rulesButton, alignment=Qt.AlignmentFlag.AlignCenter)

        buttonLayout.addWidget(QLabel(""))
        
        exitButton = QPushButton("Exit")
        exitButton.setFixedWidth(225)
        exitButton.clicked.connect(QApplication.instance().quit)
        buttonLayout.addWidget(exitButton, alignment=Qt.AlignmentFlag.AlignCenter)
        
        buttonLayout.addWidget(QLabel(""))

        layout.addLayout(buttonLayout)
        self.setLayout(layout)

    def showOnlineMenu(self):
        self.hide()
        self.onlineMenu = OnlineMenu(self)
        self.onlineMenu.show()

    def showRules(self):
        print("Display game rules.")

    def closeEvent(self, event):
        if hasattr(self, 'localGame') and self.localGame:
            self.localGame.close()
        if hasattr(self, 'onlineMenu') and self.onlineMenu:
            self.onlineMenu.close()
        super().closeEvent(event)
    
### Online Menu ###
class OnlineMenu(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.initUI()
        centerDialog(self, parent, "OnlineMenu")

    def initUI(self):
        self.setWindowTitle("Online Menu")
        self.setGeometry(700, 300, 400, 300)
        layout = QVBoxLayout()

        hostButton = QPushButton("Host Game")
        hostButton.clicked.connect(self.hostGame)
        layout.addWidget(hostButton)

        joinButton = QPushButton("Join Game")
        joinButton.clicked.connect(self.joinGame)
        layout.addWidget(joinButton)

        backButton = QPushButton("Back")
        backButton.clicked.connect(self.goBack)
        layout.addWidget(backButton)

        self.setLayout(layout)

    def hostGame(self):
        self.hide()
        self.hostLobby = HostLobby(self)
        self.hostLobby.show()

    def joinGame(self):
        self.hide()
        self.joinLobby = JoinLobby(self)
        self.joinLobby.show()

    def goBack(self):
        self.hide()
        self.parent.show()

### Host Lobby ###
class HostLobby(QWidget):
    updateOtherPlayerHandSignal = Signal(int, list, list, list)
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.server = None
        self.hostGameView = None
        self.clients = {}  # Map client sockets to indices
        self.nextIndex = 2  # Host is always Player 1
        self.numPlayers = None
        self.hostController = None
        self.initUI()
        centerDialog(self, parent, "HostLobby")
        self.startServer()

    def initUI(self):
        self.setWindowTitle("Hosting Lobby")
        self.setGeometry(700, 300, 400, 300)
        layout = QVBoxLayout()

        self.infoLabel = QLabel("Hosting Lobby...\nWaiting for players to join.")
        layout.addWidget(self.infoLabel)

        self.logText = QTextEdit()
        self.logText.setReadOnly(True)
        layout.addWidget(self.logText)

        self.playerCountLabel = QLabel("Players: 1/4")  # Host is Player 1
        layout.addWidget(self.playerCountLabel)

        self.startButton = QPushButton("Start Game")
        self.startButton.setEnabled(False)  # Enabled only when 2+ players
        self.startButton.clicked.connect(self.startGame)
        layout.addWidget(self.startButton)

        backButton = QPushButton("Back")
        backButton.clicked.connect(self.goBack)
        layout.addWidget(backButton)

        self.setLayout(layout)

    def startServer(self):
        if self.server:
            self.shutdownServer()  # Ensure the previous server is closed properly
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(("0.0.0.0", 12345))
        self.server.listen(4)
        self.logText.append("Server started on port 12345.")
        threading.Thread(target=self.acceptConnections, daemon=True).start()

    def acceptConnections(self):
        while self.server:
            try:
                clientSocket, addr = self.server.accept()
                if len(self.clients) < 3:  # Max 4 players (host + 3 clients)
                    index = self.nextIndex
                    self.clients[clientSocket] = index
                    self.nextIndex += 1
                    self.logText.append(f"Player {index} connected from {addr}.")
                    
                    # Notify the client of their player index
                    indexData = json.dumps({"action": "setIndex", "index": index})
                    clientSocket.send(indexData.encode())
                    
                    threading.Thread(target=self.handleClient, args=(clientSocket,), daemon=True).start()
                    self.updatePlayerCount()
                else:
                    clientSocket.send(b"Lobby full.")
                    clientSocket.close()
            except Exception as e:
                self.logText.append(f"Error accepting connections: {e}")
                break

    def handleClient(self, clientSocket):
        index = self.clients[clientSocket]
        try:
            while True:
                message = clientSocket.recv(1024).decode()
                if not message:
                    break  # Client disconnected
                try:
                    data = json.loads(message)  # Parse JSON
                    if data['action'] == 'updateCards':
                        playerIndex = data['playerIndex']
                        handCards = data['handCards']
                        topCards = data['topCards']
                        bottomCards = data['bottomCards']
                        self.hostController.updateOtherPlayerHand(playerIndex, handCards, topCards, bottomCards)
                        self.broadcastToClients('updateCards', data, exclude=clientSocket)
                    elif data['action'] == 'confirmedTopCards':
                        self.hostController.topCardConfirms += 1
                        self.hostController.checkAllPlayersConfirmed()
                    elif data['action'] == 'startMainGame':
                        self.hostController.startMainGame('startMainGame', {})
                        self.broadcastToClients('startMainGame', {})
                    elif data['action'] == 'updateCurrentPlayer':
                        self.hostGameView.updateCurrentPlayer(data['currentPlayer'])
                        self.hostController.currentPlayer = data['currentPlayer']
                        self.broadcastToClients('updateCurrentPlayer', data, exclude=clientSocket)
                    elif data['action'] == 'updateDeck':
                        self.hostController.deck = data['deck']
                        self.hostGameView.deckLabel.setText(f"Draw Deck:\n\n{len(data['deck'])} cards remaining")
                        self.broadcastToClients('updateDeck', data, exclude=clientSocket)
                except json.JSONDecodeError:
                    self.logText.append(f"Received invalid data from Player {index}: {message}")
                    break
        except Exception as e:
            self.logText.append(f"Player {index} disconnected: {e}")
        finally:
            self.clients.pop(clientSocket, None)
            self.nextIndex -= 1
            self.reassignIndices()
            self.updatePlayerCount()
            clientSocket.close()

    def reassignIndices(self):
        """
        Reassign indices after a player disconnects and notify all clients of the updated indices.
        """
        self.logText.append("Reassigning player indices after disconnection.")
        newClients = {}
        newIndex = 2  # Start at 2 since host is Player 1

        for clientSocket in self.clients.keys():
            newClients[clientSocket] = newIndex
            indexData = json.dumps({"action": "setIndex", "index": newIndex})
            clientSocket.send(indexData.encode())
            newIndex += 1

        self.clients = newClients
    
    def updatePlayerCount(self):
        count = len(self.clients) + 1  # Host included
        self.playerCountLabel.setText(f"Players: {count}/4")
        self.startButton.setEnabled(count > 1)  # Enabled only if 2+ players
    
    def broadcastToClients(self, action, data, exclude=None):
        for clientSocket in self.clients.keys():
            if clientSocket != exclude:  # Exclude the specified client
                try:
                    clientSocket.send(json.dumps({"action": action, **data}).encode())
                except Exception as e:
                    self.logText.append(f"Error broadcasting to client: {e}")
        
    def startGame(self):
        suits = ['clubs', 'spades', 'hearts', 'diamonds']
        self.deck = [(rank, suit, False, False) for rank in RANKS for suit in suits]
        random.shuffle(self.deck)

        self.players = []
        playerData = {}

        for i, client in enumerate(list(self.clients.keys()) + [None], start=1):
            bottomCards = [(card[0], card[1], False, True) for card in self.deck[:3]]
            hand = [(card[0], card[1], True, False) for card in self.deck[3:9]]
            self.deck = self.deck[9:]
            topCards = []

            player = {
                'bottomCards': bottomCards,
                'topCards': topCards,
                'hand': hand
            }
            playerData[f'player{i}'] = player

            if client is None:
                # Assign cards to the host
                self.hostCards = hand

        # Prepare payload for clients
        self.numPlayers = len(playerData)
        data = {
            'action': 'deckSync',
            'deck': self.deck,
            'players': playerData,
            'numPlayers': self.numPlayers
        }
        payload = json.dumps(data)
        for client in self.clients.keys():
            try:
                client.send(payload.encode())
            except Exception as e:
                print(f"Error sending data to client: {e}")

        print("Deck and player data synced with all players.")
        print(f"Player Data: {playerData}")

        # Start the host's game view
        self.hide()
        players = data.get("players", {})
        playerKey = f'player1'
        self.hostCards = players.get(playerKey, {}).get('hand', [])
        self.bottomCards = players.get(playerKey, {}).get('bottomCards', [])
        self.hostController = GameController(
            self.deck,
            1,
            self.hostCards,
            self.bottomCards,
            self.numPlayers,
            self.broadcastToClients
        )
        self.hostGameView = GameView(self.hostController, self.geometry(), self.numPlayers)
        self.hostGameView.show()
        self.hostController.startGame()
    
    def shutdownServer(self):
        if self.server:
            self.server.close()
            self.server = None
            print("Server shut down.")
            for client in list(self.clients.keys()):
                client.close()
            self.clients.clear()

    def goBack(self):
        self.shutdownServer()
        self.hide()
        self.parent.show()

    def closeEvent(self, event):
        self.shutdownServer()
        super().closeEvent(event)

### Join Lobby ###
class JoinLobby(QWidget):
    startGameSignal = Signal(int)
    
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.client = None
        self.controller = None
        self.connected = False  # Track connection status
        self.playerIndex = None  # Store the assigned player index
        self.numPlayers = None
        self.initUI()
        centerDialog(self, parent, "JoinLobby")

        # Connect the startGameSignal to the startGame slot
        self.startGameSignal.connect(self.startGame)

    def initUI(self):
        self.setWindowTitle("Join Lobby")
        self.setGeometry(700, 300, 400, 300)
        layout = QVBoxLayout()

        self.infoLabel = QLabel("Enter host address to join lobby:")
        layout.addWidget(self.infoLabel)

        self.addressInput = QLineEdit()
        self.addressInput.setPlaceholderText("Host IP Address")
        layout.addWidget(self.addressInput)

        self.nicknameInput = QLineEdit()
        self.nicknameInput.setPlaceholderText("Enter Nickname")
        layout.addWidget(self.nicknameInput)

        self.logText = QTextEdit()
        self.logText.setReadOnly(True)
        layout.addWidget(self.logText)

        self.joinButton = QPushButton("Join Lobby")
        self.joinButton.clicked.connect(self.joinLobby)
        layout.addWidget(self.joinButton)

        self.backButton = QPushButton("Back")
        self.backButton.clicked.connect(self.goBack)
        layout.addWidget(self.backButton)

        self.setLayout(layout)

    def joinLobby(self):
        hostIP = self.addressInput.text()
        nickname = self.nicknameInput.text()
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((hostIP, 12345))
            self.logText.append("Connected to server.")
            self.connected = True

            # Send a join message to the host
            initialData = {
                'action': 'join',
                'nickname': nickname
            }
            self.client.send(json.dumps(initialData).encode())

            # Start listening to the server
            threading.Thread(target=self.listenToServer, daemon=True).start()
        except Exception as e:
            self.logText.append(f"Failed to connect: {e}")

    def listenToServer(self):
        try:
            while True:
                message = self.client.recv(2048).decode()
                if not message:
                    break
                if message.startswith("{") and message.endswith("}"):  # Check for JSON format
                    data = json.loads(message)  # Deserialize JSON
                    if data.get("action") == "setIndex":
                        self.playerIndex = data.get("index")
                        self.logText.append(f"Assigned Player {self.playerIndex}")
                    elif data.get("action") == "deckSync":
                        self.logText.append("Deck and player data received.")
                        self.processDeckSync(data)
                    elif data['action'] == 'updateCards':
                        playerIndex = data['playerIndex']
                        handCards = data['handCards']
                        topCards = data['topCards']
                        bottomCards = data['bottomCards']
                        self.controller.updateOtherPlayerHand(playerIndex, handCards, topCards, bottomCards)
                    elif data['action'] == 'updateCurrentPlayer':
                        self.controller.currentPlayer = data['currentPlayer']
                        self.gameView.updateCurrentPlayer(data['currentPlayer'])
                    elif data['action'] == 'startMainGame':
                        playerIndex = data['playerIndex']
                        self.controller.startMainGame(playerIndex)
                    elif data['action'] == 'confirmedTopCards':
                        self.controller.topCardConfirms += 1
                        self.controller.checkAllPlayersConfirmed()
                    elif data['action'] == 'updateDeck':
                        self.controller.deck = data['deck']
                        self.gameView.deckLabel.setText(f"Draw Deck:\n\n{len(data['deck'])} cards remaining")

                else:
                    self.logText.append(f"Message from server: {message}")
        except Exception as e:
            self.logText.append(f"Disconnected from server: {e}")
        finally:
            if self.client:
                self.client.close()

    def broadcastUpdate(self, action, data):
        """
        Send a message to the server for relaying to other players.
        """
        if self.client:
            try:
                payload = {
                    'action': action,
                    **data
                }
                self.client.send(json.dumps(payload).encode())
            except Exception as e:
                print(f"Error sending update: {e}")
    
    def confirmTopCards(self):
        if self.controller:
            self.controller.confirmTopCards()
            payload = {'action': 'confirmTopCards', 'playerIndex': self.playerIndex}
            self.broadcastUpdate('confirmTopCards', payload)
    
    def processDeckSync(self, data):
        self.deck = data.get("deck", [])
        players = data.get("players", {})
        playerKey = f'player{self.playerIndex}'
        self.numPlayers = data.get('numPlayers')
        self.handCards = players.get(playerKey, {}).get('hand', [])
        self.bottomCards = players.get(playerKey, {}).get('bottomCards', [])
        self.startGameSignal.emit(self.playerIndex)

    def leaveServer(self):
        if self.client:
            self.client.close()
            self.client = None
        self.connected = False
        self.logText.append("Disconnected from server.")
        self.goBack()

    def goBack(self):
        if self.connected:
            self.leaveServer()
        else:
            self.hide()
            self.parent.show()

    def startGame(self, playerIndex):
        print(f"Starting game as Player {playerIndex}.")
        self.hide()
        self.controller = GameController(
            self.deck,
            self.playerIndex,
            self.handCards,
            self.bottomCards,
            self.numPlayers,
            self.broadcastUpdate
        )
        self.gameView = GameView(self.controller, self.geometry(), self.numPlayers)
        self.gameView.show()
        self.controller.startGame()


class GameView(QWidget):
    def __init__(self, controller, parentCoords, numPlayers):
        super().__init__()
        self.controller = controller
        self.numPlayers = numPlayers
        self.playerIndex = self.controller.playerIndex
        self.selectedCards = []
        self.initUI()
        centerDialog(self, parentCoords, "GameView")
        
        self.controller.updatePlayerHandSignal.connect(self.updateHandCards)
        self.controller.updateTopCardsSignal.connect(self.updateTopCards)
        self.controller.updateBottomCardsSignal.connect(self.updateBottomCards)
        self.controller.updateOtherPlayerCardsSignal.connect(self.updateOtherPlayerCards)
        self.controller.startMainViewSignal.connect(self.startMainView)
        self.controller.selectedCardsChanged.connect(self.updateConfirmButton)
        self.controller.placeButtonStateChanged.connect(self.updatePlaceButton)
        self.controller.updateCardStateSignal.connect(self.updateCardState)
        self.controller.currentPlayerChangedSignal.connect(self.updateCurrentPlayer)
        self.controller.updatePileSignal.connect(self.updatePile)
        
        
    def initUI(self):
        self.setWindowTitle(f'Palace Card Game - Player {self.playerIndex}')
        self.setWindowIcon(QIcon(r"_internal\palaceData\palace.ico"))
        self.setGeometry(450, 75, 900, 900)
        self.layout = QGridLayout()

        # Disconnect Button
        self.disconnectButton = QPushButton("Disconnect")
        self.disconnectButton.setFixedWidth(125)
        self.disconnectButton.clicked.connect(self.controller.disconnect)
        self.layout.addWidget(self.disconnectButton, 0, 0)
        
        self.spacerButton = QLabel()
        self.spacerButton.setFixedWidth(125)
        self.layout.addWidget(self.spacerButton, 0, 10)

        # Center Console
        self.initCenterConsole()

        # Dynamic Layout Adjustment
        if self.numPlayers == 2:
            self.initTwoPlayerLayout()
        elif self.numPlayers == 3:
            self.initThreePlayerLayout()
        elif self.numPlayers == 4:
            self.initFourPlayerLayout()
        
        buttonsTopContainerLayout = QVBoxLayout()
        buttonsLeftContainerLayout = QVBoxLayout()
        buttonsRightContainerLayout = QVBoxLayout()
        buttonsBottomContainerLayout = QVBoxLayout()
        self.confirmButton = QPushButton("Confirm")
        self.confirmButton.setEnabled(False)
        self.confirmButton.setFixedWidth(240)
        self.confirmButton.clicked.connect(self.controller.confirmTopCards)
        self.placeButton = QPushButton("Select A Card")
        self.placeButton.setEnabled(False)
        self.placeButton.setFixedWidth(240)
        self.placeButton.clicked.connect(self.controller.placeCard)
        self.placeButton.setVisible(False)
        
        buttonsTopContainerLayout.addWidget(self.spacerButton, alignment=Qt.AlignmentFlag.AlignCenter)
        buttonsBottomContainerLayout.addWidget(self.confirmButton, alignment=Qt.AlignmentFlag.AlignCenter)
        buttonsBottomContainerLayout.addWidget(self.placeButton, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(buttonsTopContainerLayout, 0, 5, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(buttonsBottomContainerLayout, 12, 5, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(self.layout)

    def initCenterConsole(self):
        """
        Initializes the center console with the deck, pile, and current player information.
        """
        self.deckLabel = QLabel()
        self.deckLabel.setFixedWidth(190)
        self.deckLabel.hide()
        
        self.pileLabel = QLabel("\t\t    Select your 3 Top cards...")

        self.pickUpPileButton = QPushButton("Pick Up Pile")
        self.pickUpPileButton.setFixedWidth(125)
        # self.pickUpPileButton.clicked.connect(self.controller.pickUpPile)
        self.pickUpPileButton.hide()
        
        self.currentPlayerLabel = QLabel("")
        self.currentPlayerLabel.hide()

        spacer = QSpacerItem(60, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        self.consoleLayout = QHBoxLayout()
        self.consoleLayout.addWidget(self.deckLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.consoleLayout.addWidget(self.pileLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.consoleLayout.addItem(spacer)
        self.consoleLayout.addWidget(self.pickUpPileButton, alignment=Qt.AlignmentFlag.AlignCenter)

        self.centerLayout = QVBoxLayout()
        self.centerLayout.addWidget(QLabel(""))
        self.centerLayout.addWidget(self.currentPlayerLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.centerLayout.addLayout(self.consoleLayout)
        self.centerLayout.addWidget(QLabel(""))
        self.centerLayout.addWidget(QLabel(""))

        self.layout.addLayout(self.centerLayout, 6, 5)
    
    def initPlayerAreaTop(self, labelText, position):
        """
        Helper function to initialize a player area (hand, top cards, bottom cards).
        """
        layout = QVBoxLayout()
        handLayout = QHBoxLayout()
        layout.addLayout(handLayout)
        
        handLabelLayout = QLabel(labelText)
        layout.addWidget(handLabelLayout, alignment=Qt.AlignmentFlag.AlignCenter)
            
        topCardsLayout = QHBoxLayout()
        layout.addLayout(topCardsLayout)

        bottomCardsLayout = QHBoxLayout()
        layout.addLayout(bottomCardsLayout)

        for _ in range(3):  # Assume max 3 cards for each area
            handSpacer = QLabel()
            handSpacer.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
            handSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            handLayout.addWidget(handSpacer)

            topSpacer = QLabel()
            topSpacer.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
            topSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            topCardsLayout.addWidget(topSpacer)

            bottomSpacer = QLabel()
            bottomSpacer.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
            bottomSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            bottomCardsLayout.addWidget(bottomSpacer)

        self.layout.addLayout(layout, *position)
        return handLayout, handLabelLayout, topCardsLayout, bottomCardsLayout
    
    def initPlayerAreaBot(self, labelText, position):
        """
        Helper function to initialize a player area (hand, top cards, bottom cards).
        """
        layout = QVBoxLayout()
        
        bottomCardsLayout = QHBoxLayout()
        layout.addLayout(bottomCardsLayout)
        
        topCardsLayout = QHBoxLayout()
        layout.addLayout(topCardsLayout)
        
        handLabelLayout = QLabel(labelText)
        layout.addWidget(handLabelLayout, alignment=Qt.AlignmentFlag.AlignCenter)
        
        handLayout = QHBoxLayout()
        layout.addLayout(handLayout)

        for _ in range(3):  # Assume max 3 cards for each area
            handSpacer = QLabel()
            handSpacer.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
            handSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            handLayout.addWidget(handSpacer)

            topSpacer = QLabel()
            topSpacer.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
            topSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            topCardsLayout.addWidget(topSpacer)

            bottomSpacer = QLabel()
            bottomSpacer.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
            bottomSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            bottomCardsLayout.addWidget(bottomSpacer)

        self.layout.addLayout(layout, *position)
        return handLayout, handLabelLayout, topCardsLayout, bottomCardsLayout

    def initPlayerAreaLeft(self, labelText, position):
        """
        Helper function to initialize a player area (hand, top cards, bottom cards).
        """
        layout = QHBoxLayout()
        
        handLayout = QVBoxLayout()
        layout.addLayout(handLayout)
        
        handLabelLayout = QLabel(labelText)
        font = self.currentPlayerLabel.font()
        font.setPointSize(9) 
        handLabelLayout.setFont(font)
        handLabelLayout.setFixedHeight(190)
        handLabelLayout.setFixedWidth(25)
        pixmap = QPixmap(handLabelLayout.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.white)
        painter.translate(pixmap.width(), 0)
        painter.rotate(90)
        painter.drawText(0, 0, handLabelLayout.height(), handLabelLayout.width(), Qt.AlignmentFlag.AlignCenter, handLabelLayout.text())
        painter.end()
        handLabelLayout.setPixmap(pixmap)
        layout.addWidget(handLabelLayout, alignment=Qt.AlignmentFlag.AlignCenter)
        
        topCardsLayout = QVBoxLayout()
        layout.addLayout(topCardsLayout)
        
        bottomCardsLayout = QVBoxLayout()
        layout.addLayout(bottomCardsLayout)

        for _ in range(3):  # Assume max 3 cards for each area
            handSpacer = QLabel()
            handSpacer.setFixedSize(CARD_HEIGHT, CARD_WIDTH)
            handSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            handLayout.addWidget(handSpacer)

            topSpacer = QLabel()
            topSpacer.setFixedSize(CARD_HEIGHT, CARD_WIDTH)
            topSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            topCardsLayout.addWidget(topSpacer)

            bottomSpacer = QLabel()
            bottomSpacer.setFixedSize(CARD_HEIGHT, CARD_WIDTH)
            bottomSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            bottomCardsLayout.addWidget(bottomSpacer)

        self.layout.addLayout(layout, *position)
        return handLayout, handLabelLayout, topCardsLayout, bottomCardsLayout
    
    def initPlayerAreaRight(self, labelText, position):
        """
        Helper function to initialize a player area (hand, top cards, bottom cards).
        """
        layout = QHBoxLayout()
        
        bottomCardsLayout = QVBoxLayout()
        layout.addLayout(bottomCardsLayout)
        
        topCardsLayout = QVBoxLayout()
        layout.addLayout(topCardsLayout)
        
        handLabelLayout = QLabel(labelText)
        font = self.currentPlayerLabel.font()
        font.setPointSize(9) 
        handLabelLayout.setFont(font)
        handLabelLayout.setFixedHeight(190)
        handLabelLayout.setFixedWidth(25)
        pixmap = QPixmap(handLabelLayout.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)
        painter.setFont(font)
        painter.setPen(Qt.GlobalColor.white)
        painter.translate(0, pixmap.height())
        painter.rotate(-90)
        painter.drawText(0, 0, handLabelLayout.height(), handLabelLayout.width(), Qt.AlignmentFlag.AlignCenter, handLabelLayout.text())
        painter.end()
        handLabelLayout.setPixmap(pixmap)
        layout.addWidget(handLabelLayout, alignment=Qt.AlignmentFlag.AlignCenter)
        
        handLayout = QVBoxLayout()
        layout.addLayout(handLayout)

        for _ in range(3):  # Assume max 3 cards for each area
            handSpacer = QLabel()
            handSpacer.setFixedSize(CARD_HEIGHT, CARD_WIDTH)
            handSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            handLayout.addWidget(handSpacer)

            topSpacer = QLabel()
            topSpacer.setFixedSize(CARD_HEIGHT, CARD_WIDTH)
            topSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            topCardsLayout.addWidget(topSpacer)

            bottomSpacer = QLabel()
            bottomSpacer.setFixedSize(CARD_HEIGHT, CARD_WIDTH)
            bottomSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            bottomCardsLayout.addWidget(bottomSpacer)

        self.layout.addLayout(layout, *position)
        return handLayout, handLabelLayout, topCardsLayout, bottomCardsLayout

    def initTwoPlayerLayout(self):
        """
        Initializes the layout for a two-player game.
        """
        if self.playerIndex == 1:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 5))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 2's Hand", (1, 5))
        else:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 5))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 1's Hand", (1, 5))

    def initThreePlayerLayout(self):
        """
        Initializes the layout for a three-player game.
        """
        if self.playerIndex == 1:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 2's Hand", (6, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 3's Hand", (1, 5))
        elif self.playerIndex == 2:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 3's Hand", (6, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaBot("Player 1's Hand", (1, 5))
        elif self.playerIndex == 3:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 1's Hand", (6, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 2's Hand", (1, 5))

    def initFourPlayerLayout(self):
        """
        Initializes the layout for a four-player game.
        """
        if self.playerIndex == 1:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (10, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 2's Hand", (5, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 3's Hand", (0, 5))
            self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom = self.initPlayerAreaRight("Player 4's Hand", (5, 10))
        elif self.playerIndex == 2:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (10, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 3's Hand", (5, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 4's Hand", (0, 5))
            self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom = self.initPlayerAreaRight("Player 1's Hand", (5, 10))
        elif self.playerIndex == 3:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (10, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 4's Hand", (5, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 1's Hand", (0, 5))
            self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom = self.initPlayerAreaRight("Player 2's Hand", (5, 10))
        elif self.playerIndex == 4:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (10, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 1's Hand", (5, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 2's Hand", (0, 5))
            self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom = self.initPlayerAreaRight("Player 3's Hand", (5, 10))
    
    def updateHandCards(self):
        """
        Update the current player's hand cards display (face up).
        """
        # Clear player hand cards layout
        while self.playerHand.count():
            item = self.playerHand.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Add player hand cards
        for idx, card in enumerate(self.controller.handCards):
            button = QLabel()
            button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            button.setStyleSheet("border: 2px solid transparent; background-color: transparent;")
            if card:
                pixmap = QPixmap(fr"_internal\palaceData\cards\{card[0].lower()}_of_{card[1].lower()}.png").scaled(
                    CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                button.setPixmap(pixmap)
                button.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Add mouse press event for card selection
                button.mousePressEvent = lambda event, idx=idx, btn=button: self.controller.prepareCardPlacement(idx, btn)
            self.playerHand.addWidget(button)
            
    def updatePile(self):
        """
        Updates the pile display with the top card.
        """
        if self.controller.pile:
            topCard = self.controller.pile[-1]  # Get the top card from the pile
            pixmap = QPixmap(fr"_internal\palaceData\cards\{topCard[0].lower()}_of_{topCard[1].lower()}.png").scaled(
                CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.pileLabel.setPixmap(pixmap)
        else:
            self.pileLabel.setText("Pile: Empty")
    
    def updateTopCards(self):
        """
        Update the current player's top cards display (face up).
        """
        # Clear top cards layout
        while self.playerTop.count():
            item = self.playerTop.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Add top cards
        for card in self.controller.topCards:
            button = QLabel()
            button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            pixmap = QPixmap(fr"_internal\palaceData\cards\{card[0].lower()}_of_{card[1].lower()}.png").scaled(
                CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            button.setPixmap(pixmap)
            button.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.playerTop.addWidget(button)

    def updateBottomCards(self):
        """
        Update the current player's bottom cards display (face down).
        """
        # Clear bottom cards layout
        while self.playerBottom.count():
            item = self.playerBottom.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        # Add bottom cards (face down)
        for _ in range(3):
            button = QLabel()
            button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            button.setStyleSheet("border: 2px solid transparent; background-color: transparent;")
            pixmap = QPixmap(fr"_internal\palaceData\cards\back.png").scaled(
                CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            button.setPixmap(pixmap)
            button.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.playerBottom.addWidget(button)

    def updateOtherPlayerCards(self, playerIndex, handCards, topCards, bottomCards):
        # Mapping based on self.playerIndex
        layoutMap = {
            'hand': {},
            'top': {},
            'bottom': {}
        }

        if self.numPlayers == 2:
            if self.playerIndex == 1:
                layoutMap['hand'] = {2: self.topHand}
                layoutMap['top'] = {2: self.topTop}
                layoutMap['bottom'] = {2: self.topBottom}
            elif self.playerIndex == 2:
                layoutMap['hand'] = {1: self.topHand}
                layoutMap['top'] = {1: self.topTop}
                layoutMap['bottom'] = {1: self.topBottom}
        elif self.numPlayers == 3:
            if self.playerIndex == 1:
                layoutMap['hand'] = {2: self.leftHand, 3: self.topHand}
                layoutMap['top'] = {2: self.leftTop, 3: self.topTop}
                layoutMap['bottom'] = {2: self.leftBottom, 3: self.topBottom}
            elif self.playerIndex == 2:
                layoutMap['hand'] = {3: self.leftHand, 1: self.topHand}
                layoutMap['top'] = {3: self.leftTop, 1: self.topTop}
                layoutMap['bottom'] = {3: self.leftBottom, 1: self.topBottom}
            elif self.playerIndex == 3:
                layoutMap['hand'] = {1: self.leftHand, 2: self.topHand}
                layoutMap['top'] = {1: self.leftTop, 2: self.topTop}
                layoutMap['bottom'] = {1: self.leftBottom, 2: self.topBottom}
        elif self.numPlayers == 4:
            if self.playerIndex == 1:
                layoutMap['hand'] = {2: self.leftHand, 3: self.topHand, 4: self.rightHand}
                layoutMap['top'] = {2: self.leftTop, 3: self.topTop, 4: self.rightTop}
                layoutMap['bottom'] = {2: self.leftBottom, 3: self.topBottom, 4: self.rightBottom}
            elif self.playerIndex == 2:
                layoutMap['hand'] = {3: self.leftHand, 4: self.topHand, 1: self.rightHand}
                layoutMap['top'] = {3: self.leftTop, 4: self.topTop, 1: self.rightTop}
                layoutMap['bottom'] = {3: self.leftBottom, 4: self.topBottom, 1: self.rightBottom}
            elif self.playerIndex == 3:
                layoutMap['hand'] = {4: self.leftHand, 1: self.topHand, 2: self.rightHand}
                layoutMap['top'] = {4: self.leftTop, 1: self.topTop, 2: self.rightTop}
                layoutMap['bottom'] = {4: self.leftBottom, 1: self.topBottom, 2: self.rightBottom}
            elif self.playerIndex == 4:
                layoutMap['hand'] = {1: self.leftHand, 2: self.topHand, 3: self.rightHand}
                layoutMap['top'] = {1: self.leftTop, 2: self.topTop, 3: self.rightTop}
                layoutMap['bottom'] = {1: self.leftBottom, 2: self.topBottom, 3: self.rightBottom}

        # Update layouts for hand, top, and bottom cards
        for cardType, cards, layout in zip(
            ['hand', 'top', 'bottom'],
            [handCards, topCards, bottomCards],
            [layoutMap['hand'].get(playerIndex), layoutMap['top'].get(playerIndex), layoutMap['bottom'].get(playerIndex)]
        ):
            if not layout:
                continue  # Invalid playerIndex for the current view

            # Clear the existing layout
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()

            # Add the new cards to the layout
            for card in cards:
                button = QLabel()
                rotate = False
                rotatedDimensions = (BUTTON_HEIGHT, BUTTON_WIDTH)
                standardDimensions = (BUTTON_WIDTH, BUTTON_HEIGHT)
                pixmapDimensions = (CARD_WIDTH, CARD_HEIGHT)
                
                # Determine layout properties
                if layout in [getattr(self, 'leftHand', None), getattr(self, 'rightHand', None),
                            getattr(self, 'leftTop', None), getattr(self, 'rightTop', None),
                            getattr(self, 'leftBottom', None), getattr(self, 'rightBottom', None)]:
                    button.setFixedSize(*rotatedDimensions)
                    rotate = True
                else:
                    button.setFixedSize(*standardDimensions)

                # Load the card image
                if cardType == 'bottom':  # Bottom cards (face down)
                    pixmap = QPixmap(fr"_internal\palaceData\cards\back.png").scaled(
                        *pixmapDimensions, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                    )
                else:  # Top and hand cards (face up)
                    pixmap = QPixmap(fr"_internal\palaceData\cards\{card[0].lower()}_of_{card[1].lower()}.png").scaled(
                        *pixmapDimensions, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                    )

                # Apply rotation if necessary
                if rotate:
                    rotationAngle = 90 if layout in [getattr(self, 'leftHand', None), getattr(self, 'leftTop', None), getattr(self, 'leftBottom', None)] else -90
                    transform = QTransform().rotate(rotationAngle)
                    pixmap = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation).scaled(CARD_HEIGHT, CARD_WIDTH, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

                # Set pixmap and alignment
                button.setPixmap(pixmap)
                button.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(button)
    
    def updateConfirmButton(self, selectedCount):
        """
        Enable the confirm button only when exactly 3 cards are selected.
        """
        self.confirmButton.setEnabled(selectedCount == 3)
    
    def updatePlaceButton(self, isEnabled, text):
        self.placeButton.setEnabled(isEnabled)
        self.placeButton.setText(text)
    
    def updatePile(self, pile):
        """
        Update the pile view with the top card.
        """
        if pile:
            topCard = pile[-1]
            pixmap = QPixmap(fr"_internal\palaceData\cards\{topCard[0].lower()}_of_{topCard[1].lower()}.png").scaled(
                CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.pileLabel.setPixmap(pixmap)
        else:
            self.pileLabel.setText("Pile: Empty")
    
    def updateCurrentPlayer(self, currentPlayer):
        """
        Update the UI for the current player.
        """
        self.currentPlayerLabel.setText(f"Current Player: {currentPlayer}")
        isCurrentPlayer = currentPlayer == self.playerIndex
        self.setPlayerHandEnabled(isCurrentPlayer)
        self.placeButton.setEnabled(False)
        if isCurrentPlayer:
            self.placeButton.setText("Select A Card")
        else:
            self.placeButton.setText(f"Player {currentPlayer}'s Turn...")

    
    def updateCardState(self, cardIndex, isEnabled):
        widget = self.playerHand.itemAt(cardIndex).widget()
        if widget:
            widget.setEnabled(isEnabled)
    
    def setPlayerHandEnabled(self, enabled):
        for i in range(self.playerHand.count()):
            widget = self.playerHand.itemAt(i).widget()
            if widget:
                widget.setEnabled(enabled)
    
    def startMainView(self):
        """
        Transition to the main game phase by displaying the center console.
        """
        # Remove confirm button
        self.confirmButton.hide()
        self.placeButton.show()
        self.deckLabel.show()
        self.deckLabel.setText(f"Draw Deck:\n\n{len(self.controller.deck)} cards remaining")
        self.pickUpPileButton.show()
        self.pileLabel.setText("Pile: Empty")
        self.pileLabel.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
        self.currentPlayerLabel.setText(f"Current Player: {self.controller.currentPlayer}")
        self.currentPlayerLabel.show()
        
        if self.controller.currentPlayer == self.controller.playerIndex:
            self.setPlayerHandEnabled(True)
        else:
            self.setPlayerHandEnabled(False)
            
class GameController(QObject):
    selectedCardsChanged = Signal(int)
    updatePlayerHandSignal = Signal(list)
    updateTopCardsSignal = Signal(list)
    updateBottomCardsSignal = Signal(list)
    updateOtherPlayerCardsSignal = Signal(int, list, list, list)
    startMainViewSignal = Signal()
    placeButtonStateChanged = Signal(bool, str)   
    updateCardStateSignal = Signal(int, bool)
    currentPlayerChangedSignal = Signal(int)
    updatePileSignal = Signal(list)

    topCardSelectionPhase = True

    def __init__(self, deck, playerIndex, handCards, bottomCards, numPlayers, broadcastUpdate):
        super().__init__()
        self.deck = deck
        self.playerIndex = playerIndex
        self.numPlayers = numPlayers
        self.selectedCards = []  
        self.topCards = []
        self.pile = []
        self.handCards = handCards  
        self.bottomCards = bottomCards 
        self.broadcastUpdate = broadcastUpdate
        self.topCardConfirms = 0
        self.currentPlayer = None
        
        self.allPlayerCards = {
            self.playerIndex: {
                'handCards': self.handCards,
                'topCards': self.topCards,
                'bottomCards': self.bottomCards,
            }
        }

    def startGame(self):
        self.updatePlayerHandSignal.emit(self.handCards)
        
    def prepareCardPlacement(self, cardIndex, cardLabel):
        """
        Handle selection and deselection of cards for placement.
        """
        card = self.handCards[cardIndex]

        if self.topCardSelectionPhase:
            if (cardIndex, card) in self.selectedCards:
                # Deselect the card
                self.selectedCards.remove((cardIndex, card))
                cardLabel.setStyleSheet("border: 2px solid transparent; background-color: transparent;")
            elif len(self.selectedCards) < 3:
                # Select the card if fewer than 3 cards are selected
                self.selectedCards.append((cardIndex, card))
                cardLabel.setStyleSheet("border: 2px solid blue; background-color: transparent;")

            # Emit signal to update the confirm button state
            self.selectedCardsChanged.emit(len(self.selectedCards))
        else:
            if (card, cardLabel) in self.selectedCards:
                # Deselect the card
                self.selectedCards.remove((card, cardLabel))
                cardLabel.setStyleSheet("border: 0px solid black; background-color: transparent;")
            else:
                # Select the card
                self.selectedCards.append((card, cardLabel))
                cardLabel.setStyleSheet("border: 2px solid blue; background-color: transparent;")

            selectedCardRank = card[0]

            # Enable or disable other cards based on the selected card's rank
            for i, handCard in enumerate(self.handCards):
                isEnabled = not self.selectedCards or handCard[0] == selectedCardRank
                self.updateCardStateSignal.emit(i, isEnabled)

            # Emit signal to update the place button state
            if self.selectedCards:
                self.placeButtonStateChanged.emit(True, "Place")
            else:
                self.placeButtonStateChanged.emit(False, "Select A Card")

    def placeCard(self):
        """
        Places the selected cards onto the pile and handles the game loop logic.
        """
        if not self.selectedCards:
            print("No cards selected to place.")
            return

        # Add selected cards to the pile
        for card, label in self.selectedCards:
            self.pile.append(card)

        # Clear selected cards and update hand
        self.selectedCards.clear()
        self.handCards = [card for card in self.handCards if card not in self.pile]
        self.updatePlayerHandSignal.emit(self.handCards)

        # Update the pile view
        self.updatePileSignal.emit(self.pile)

        # Draw a card if hand has fewer than 3 cards
        if len(self.handCards) < 3 and self.deck:
            newCard = self.deck.pop(0)
            self.handCards.append(newCard)
            self.updatePlayerHandSignal.emit(self.handCards)
            
        self.broadcastUpdate('updateDeck', {self.deck})

        # Rotate the turn to the next player
        self.rotateTurn()
    
    def rotateTurn(self):
        """
        Handle turn rotation logic based on the number of players.
        """
        self.currentPlayer = (self.currentPlayer % self.numPlayers) + 1
        self.currentPlayerChangedSignal.emit(self.currentPlayer)
        self.broadcastUpdate('updateCurrentPlayer', {'currentPlayer': self.currentPlayer})
        print(self.currentPlayer)
    
    def confirmTopCards(self):
        # Move selected cards to top cards
        for index, card in self.selectedCards:
            self.topCards.append(card)
            self.handCards[index] = None

        self.handCards = [card for card in self.handCards if card is not None]
        self.selectedCards.clear()

        self.topCardSelectionPhase = False
        self.updatePlayerHandSignal.emit(self.handCards)
        self.updateTopCardsSignal.emit(self.topCards)
        self.updateBottomCardsSignal.emit(self.bottomCards)

        # Notify the host about confirmation
        self.topCardConfirms += 1
        self.broadcastCards()
        self.broadcastUpdate('confirmedTopCards', {})
        if self.playerIndex == 1:
            self.checkAllPlayersConfirmed()
    
    def checkAllPlayersConfirmed(self):        
        if self.topCardConfirms == self.numPlayers:
            if self.playerIndex == 1:
                highestPlayer, rankTotals = self.calculateRankTotals()
                print(f"Rank totals for top cards: {rankTotals}")
                print(f"Player {highestPlayer} has the highest rank total.")
                self.startMainGame(highestPlayer)
            self.broadcastUpdate('startMainGame', {"playerIndex": highestPlayer})
    
    def drawCard(self, newCard):
        """
        Add a new card to the player's hand and broadcast the update.
        """
        self.handCards.append(newCard)
        self.updatePlayerHandSignal.emit(self.handCards)
        self.broadcastCards()
    
    def broadcastCards(self):
        """
        Broadcast the current player's handCards to the host for relaying.
        """
        payload = {
            'playerIndex': self.playerIndex,
            'handCards': self.handCards,
            'topCards': self.topCards,
            'bottomCards': self.bottomCards
        }
        self.broadcastUpdate('updateCards', payload)
        self.allPlayerCards[self.playerIndex] = {
            'handCards': self.handCards,
            'topCards': self.topCards,
            'bottomCards': self.bottomCards,
        }
    
    def updateOtherPlayerHand(self, playerIndex, handCards, topCards, bottomCards):
        """
        Update the hand cards of another player.
        """
        self.allPlayerCards[playerIndex] = {
            'handCards': handCards,
            'topCards': topCards,
            'bottomCards': bottomCards,
        }
        if playerIndex != self.playerIndex:  # Ensure it's not updating its own hand
            self.updateOtherPlayerCardsSignal.emit(playerIndex, handCards, topCards, bottomCards)
    
    def calculateRankTotals(self):
        """
        Calculate the rank totals for each player's top cards and determine the player with the highest total.
        """
        rankTotals = {}
        for playerIndex, cards in self.allPlayerCards.items():
            topCards = cards.get('topCards', [])
            total = sum(VALUES[card[0]] for card in topCards)  # Calculate total rank values
            rankTotals[playerIndex] = total

        # Find the player with the highest total
        highestPlayer = max(rankTotals, key=rankTotals.get)
        return highestPlayer, rankTotals

    def startMainGame(self, highestPlayer):
        """
        Transition to the main game phase, calculate rank totals, and identify the player with the highest rank.
        """
        self.currentPlayer = highestPlayer
        # Notify all players about the rank totals and highest player
        self.startMainViewSignal.emit()
        
    
### Main Application ###
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(Dark)
    homeMenu = HomeMenu()
    def onExit():
        # Ensure all resources are cleaned up
        if hasattr(homeMenu, 'localGame') and homeMenu.localGame:
            homeMenu.localGame.close()
        if hasattr(homeMenu, 'onlineMenu') and homeMenu.onlineMenu:
            homeMenu.onlineMenu.close()

    app.aboutToQuit.connect(onExit)  # Ensure cleanup on app exit
    homeMenu.show()
    sys.exit(app.exec())
