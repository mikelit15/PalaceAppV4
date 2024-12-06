import sys
import socket
import threading
import random
import json
import time
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,\
    QTextEdit, QGridLayout, QFrame, QSpacerItem, QSizePolicy)
from PySide6.QtGui import QPixmap, QIcon, QTransform, QPainter, QFontMetrics
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
VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}

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
        self.next_index = 2  # Host is always Player 1
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
                client_socket, addr = self.server.accept()
                if len(self.clients) < 3:  # Max 4 players (host + 3 clients)
                    index = self.next_index
                    self.clients[client_socket] = index
                    self.next_index += 1
                    self.logText.append(f"Player {index} connected from {addr}.")
                    
                    # Notify the client of their player index
                    index_data = json.dumps({"action": "setIndex", "index": index})
                    client_socket.send(index_data.encode())
                    
                    threading.Thread(target=self.handleClient, args=(client_socket,), daemon=True).start()
                    self.updatePlayerCount()
                else:
                    client_socket.send(b"Lobby full.")
                    client_socket.close()
            except Exception as e:
                self.logText.append(f"Error accepting connections: {e}")
                break

    def handleClient(self, client_socket):
        index = self.clients[client_socket]
        try:
            while True:
                message = client_socket.recv(1024).decode()
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
                        self.broadcastToClients('updateCards', data, exclude=client_socket)
                    elif data['action'] == 'confirmedTopCards':
                        self.hostController.topCardConfirms += 1
                        self.hostController.checkAllPlayersConfirmed()
                    elif data['action'] == 'startMainGame':
                        self.hostController.startMainGame()
                except json.JSONDecodeError:
                    self.logText.append(f"Received invalid data from Player {index}: {message}")
                    break
        except Exception as e:
            self.logText.append(f"Player {index} disconnected: {e}")
        finally:
            self.clients.pop(client_socket, None)
            self.next_index -= 1
            self.reassignIndices()
            self.updatePlayerCount()
            client_socket.close()

    def reassignIndices(self):
        """
        Reassign indices after a player disconnects and notify all clients of the updated indices.
        """
        self.logText.append("Reassigning player indices after disconnection.")
        new_clients = {}
        new_index = 2  # Start at 2 since host is Player 1

        for client_socket in self.clients.keys():
            new_clients[client_socket] = new_index
            index_data = json.dumps({"action": "setIndex", "index": new_index})
            client_socket.send(index_data.encode())
            new_index += 1

        self.clients = new_clients
    
    def updatePlayerCount(self):
        count = len(self.clients) + 1  # Host included
        self.playerCountLabel.setText(f"Players: {count}/4")
        self.startButton.setEnabled(count > 1)  # Enabled only if 2+ players
    
    def broadcastToClients(self, action, data, exclude=None):
        for client_socket in self.clients.keys():
            if client_socket != exclude:  # Exclude the specified client
                try:
                    client_socket.send(json.dumps({"action": action, **data}).encode())
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
        player_key = f'player1'
        self.hostCards = players.get(player_key, {}).get('hand', [])
        self.bottomCards = players.get(player_key, {}).get('bottomCards', [])
        self.hostController = GameController(
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
        self.player_index = None  # Store the assigned player index
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
        host_ip = self.addressInput.text()
        nickname = self.nicknameInput.text()
        try:
            self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client.connect((host_ip, 12345))
            self.logText.append("Connected to server.")
            self.connected = True

            # Send a join message to the host
            initial_data = {
                'action': 'join',
                'nickname': nickname
            }
            self.client.send(json.dumps(initial_data).encode())

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
                        self.player_index = data.get("index")
                        self.logText.append(f"Assigned Player {self.player_index}")
                    elif data.get("action") == "deckSync":
                        self.logText.append("Deck and player data received.")
                        self.processDeckSync(data)
                    elif data['action'] == 'updateCards':
                        playerIndex = data['playerIndex']
                        handCards = data['handCards']
                        topCards = data['topCards']
                        bottomCards = data['bottomCards']
                        self.controller.updateOtherPlayerHand(playerIndex, handCards, topCards, bottomCards)
                    elif data['action'] == 'startMainGame':
                        self.controller.startMainGame()
                    elif data['action'] == 'confirmedTopCards':
                        self.controller.topCardConfirms += 1
                        self.controller.checkAllPlayersConfirmed()
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
            payload = {'action': 'confirmTopCards', 'playerIndex': self.player_index}
            self.broadcastUpdate('confirmTopCards', payload)
    
    def processDeckSync(self, data):
        self.deck = data.get("deck", [])
        players = data.get("players", {})
        player_key = f'player{self.player_index}'
        self.numPlayers = data.get('numPlayers')
        self.handCards = players.get(player_key, {}).get('hand', [])
        self.bottomCards = players.get(player_key, {}).get('bottomCards', [])
        self.startGameSignal.emit(self.player_index)

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

    def startGame(self, player_index):
        print(f"Starting game as Player {player_index}.")
        self.hide()
        self.controller = GameController(
            self.player_index,
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
        self.num_players = numPlayers
        self.player_index = self.controller.player_index
        self.initUI()
        centerDialog(self, parentCoords, "GameView")
        
        self.controller.updatePlayerHandSignal.connect(self.updateHandCards)
        self.controller.updateTopCardsSignal.connect(self.updateTopCards)
        self.controller.updateBottomCardsSignal.connect(self.updateBottomCards)
        self.controller.updateOtherPlayerCardsSignal.connect(self.updateOtherPlayerCards)
        self.controller.startMainViewSignal.connect(self.startMainView)
        self.controller.selectedCardsChanged.connect(self.updateConfirmButton)
        
    def initUI(self):
        self.setWindowTitle(f'Palace Card Game - Player {self.player_index}')
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
        if self.num_players == 2:
            self.initTwoPlayerLayout()
        elif self.num_players == 3:
            self.initThreePlayerLayout()
        elif self.num_players == 4:
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
        # self.placeButton.clicked.connect(self.controller.placeCard)
        self.placeButton.setVisible(False)
        
        buttonsTopContainerLayout.addWidget(self.spacerButton, alignment=Qt.AlignmentFlag.AlignCenter)
        buttonsBottomContainerLayout.addWidget(self.confirmButton, alignment=Qt.AlignmentFlag.AlignCenter)
        # buttonsBottomContainerLayout.addWidget(self.placeButton, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(buttonsTopContainerLayout, 0, 5, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(buttonsBottomContainerLayout, 12, 5, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(self.layout)

    def initCenterConsole(self):
        """
        Initializes the center console with the deck, pile, and current player information.
        """
        self.deckLabel = QLabel("Deck")
        self.deckLabel.setFixedWidth(100)
        self.deckLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.deckLabel.hide()
        
        self.pileLabel = QLabel("\t     Select your 3 Top cards...")
        self.pileLabel.setFixedWidth(100)
        self.pileLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.pickUpPileButton = QPushButton("Pick Up Pile")
        self.pickUpPileButton.setFixedWidth(125)
        # self.pickUpPileButton.clicked.connect(self.controller.pickUpPile)
        self.pickUpPileButton.hide()

        spacer = QSpacerItem(60, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        self.consoleLayout = QHBoxLayout()
        self.consoleLayout.addWidget(self.deckLabel, alignment=Qt.AlignmentFlag.AlignLeft)
        self.consoleLayout.addWidget(self.pileLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.consoleLayout.addItem(spacer)
        self.consoleLayout.addWidget(self.pickUpPileButton, alignment=Qt.AlignmentFlag.AlignRight)

        self.centerContainer = QWidget()
        self.centerContainer.setLayout(self.consoleLayout)
        self.centerContainer.setFixedWidth(500)

        self.currentPlayerLabel = QLabel("")
        self.currentPlayerLabel.hide()
        self.centerLayout = QVBoxLayout()
        self.centerLayout.addWidget(QLabel(""))
        self.centerLayout.addWidget(self.currentPlayerLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.centerLayout.addWidget(self.centerContainer, alignment=Qt.AlignmentFlag.AlignCenter)
        self.centerLayout.addWidget(QLabel(""))
        self.centerLayout.addWidget(QLabel(""))

        self.layout.addLayout(self.centerLayout, 6, 5, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def initPlayerAreaTop(self, label_text, position):
        """
        Helper function to initialize a player area (hand, top cards, bottom cards).
        """
        layout = QVBoxLayout()
        handLayout = QHBoxLayout()
        layout.addLayout(handLayout)
        
        handLabelLayout = QLabel(label_text)
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
    
    def initPlayerAreaBot(self, label_text, position):
        """
        Helper function to initialize a player area (hand, top cards, bottom cards).
        """
        layout = QVBoxLayout()
        
        bottomCardsLayout = QHBoxLayout()
        layout.addLayout(bottomCardsLayout)
        
        topCardsLayout = QHBoxLayout()
        layout.addLayout(topCardsLayout)
        
        handLabelLayout = QLabel(label_text)
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

    def initPlayerAreaLeft(self, label_text, position):
        """
        Helper function to initialize a player area (hand, top cards, bottom cards).
        """
        layout = QHBoxLayout()
        
        handLayout = QVBoxLayout()
        layout.addLayout(handLayout)
        
        handLabelLayout = QLabel(label_text)
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
    
    def initPlayerAreaRight(self, label_text, position):
        """
        Helper function to initialize a player area (hand, top cards, bottom cards).
        """
        layout = QHBoxLayout()
        
        bottomCardsLayout = QVBoxLayout()
        layout.addLayout(bottomCardsLayout)
        
        topCardsLayout = QVBoxLayout()
        layout.addLayout(topCardsLayout)
        
        handLabelLayout = QLabel(label_text)
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
        if self.player_index == 1:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 5))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 2's Hand", (1, 5))
        else:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 5))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 1's Hand", (1, 5))

    def initThreePlayerLayout(self):
        """
        Initializes the layout for a three-player game.
        """
        if self.player_index == 1:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 2's Hand", (6, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 3's Hand", (1, 5))
        elif self.player_index == 2:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 3's Hand", (6, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaBot("Player 1's Hand", (1, 5))
        elif self.player_index == 3:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 1's Hand", (6, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 2's Hand", (1, 5))

    def initFourPlayerLayout(self):
        """
        Initializes the layout for a four-player game.
        """
        if self.player_index == 1:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (10, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 2's Hand", (5, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 3's Hand", (0, 5))
            self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom = self.initPlayerAreaRight("Player 4's Hand", (5, 10))
        elif self.player_index == 2:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (10, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 3's Hand", (5, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 4's Hand", (0, 5))
            self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom = self.initPlayerAreaRight("Player 1's Hand", (5, 10))
        elif self.player_index == 3:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (10, 5))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft("Player 4's Hand", (5, 0))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop("Player 1's Hand", (0, 5))
            self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom = self.initPlayerAreaRight("Player 2's Hand", (5, 10))
        elif self.player_index == 4:
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
        # Mapping based on self.player_index
        layout_map = {
            'hand': {},
            'top': {},
            'bottom': {}
        }

        if self.num_players == 2:
            if self.player_index == 1:
                layout_map['hand'] = {2: self.topHand}
                layout_map['top'] = {2: self.topTop}
                layout_map['bottom'] = {2: self.topBottom}
            elif self.player_index == 2:
                layout_map['hand'] = {1: self.topHand}
                layout_map['top'] = {1: self.topTop}
                layout_map['bottom'] = {1: self.topBottom}
        elif self.num_players == 3:
            if self.player_index == 1:
                layout_map['hand'] = {2: self.leftHand, 3: self.topHand}
                layout_map['top'] = {2: self.leftTop, 3: self.topTop}
                layout_map['bottom'] = {2: self.leftBottom, 3: self.topBottom}
            elif self.player_index == 2:
                layout_map['hand'] = {3: self.leftHand, 1: self.topHand}
                layout_map['top'] = {3: self.leftTop, 1: self.topTop}
                layout_map['bottom'] = {3: self.leftBottom, 1: self.topBottom}
            elif self.player_index == 3:
                layout_map['hand'] = {1: self.leftHand, 2: self.topHand}
                layout_map['top'] = {1: self.leftTop, 2: self.topTop}
                layout_map['bottom'] = {1: self.leftBottom, 2: self.topBottom}
        elif self.num_players == 4:
            if self.player_index == 1:
                layout_map['hand'] = {2: self.leftHand, 3: self.topHand, 4: self.rightHand}
                layout_map['top'] = {2: self.leftTop, 3: self.topTop, 4: self.rightTop}
                layout_map['bottom'] = {2: self.leftBottom, 3: self.topBottom, 4: self.rightBottom}
            elif self.player_index == 2:
                layout_map['hand'] = {3: self.leftHand, 4: self.topHand, 1: self.rightHand}
                layout_map['top'] = {3: self.leftTop, 4: self.topTop, 1: self.rightTop}
                layout_map['bottom'] = {3: self.leftBottom, 4: self.topBottom, 1: self.rightBottom}
            elif self.player_index == 3:
                layout_map['hand'] = {4: self.leftHand, 1: self.topHand, 2: self.rightHand}
                layout_map['top'] = {4: self.leftTop, 1: self.topTop, 2: self.rightTop}
                layout_map['bottom'] = {4: self.leftBottom, 1: self.topBottom, 2: self.rightBottom}
            elif self.player_index == 4:
                layout_map['hand'] = {1: self.leftHand, 2: self.topHand, 3: self.rightHand}
                layout_map['top'] = {1: self.leftTop, 2: self.topTop, 3: self.rightTop}
                layout_map['bottom'] = {1: self.leftBottom, 2: self.topBottom, 3: self.rightBottom}

        # Update layouts for hand, top, and bottom cards
        for cardType, cards, layout in zip(
            ['hand', 'top', 'bottom'],
            [handCards, topCards, bottomCards],
            [layout_map['hand'].get(playerIndex), layout_map['top'].get(playerIndex), layout_map['bottom'].get(playerIndex)]
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
                rotated_dimensions = (BUTTON_HEIGHT, BUTTON_WIDTH)
                standard_dimensions = (BUTTON_WIDTH, BUTTON_HEIGHT)
                pixmap_dimensions = (CARD_WIDTH, CARD_HEIGHT)
                
                # Determine layout properties
                if layout in [getattr(self, 'leftHand', None), getattr(self, 'rightHand', None),
                            getattr(self, 'leftTop', None), getattr(self, 'rightTop', None),
                            getattr(self, 'leftBottom', None), getattr(self, 'rightBottom', None)]:
                    button.setFixedSize(*rotated_dimensions)
                    rotate = True
                else:
                    button.setFixedSize(*standard_dimensions)

                # Load the card image
                if cardType == 'bottom':  # Bottom cards (face down)
                    pixmap = QPixmap(fr"_internal\palaceData\cards\back.png").scaled(
                        *pixmap_dimensions, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                    )
                else:  # Top and hand cards (face up)
                    pixmap = QPixmap(fr"_internal\palaceData\cards\{card[0].lower()}_of_{card[1].lower()}.png").scaled(
                        *pixmap_dimensions, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                    )

                # Apply rotation if necessary
                if rotate:
                    rotation_angle = 90 if layout in [getattr(self, 'leftHand', None), getattr(self, 'leftTop', None), getattr(self, 'leftBottom', None)] else -90
                    transform = QTransform().rotate(rotation_angle)
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
    
    def startMainView(self):
        """
        Transition to the main game phase by displaying the center console.
        """
        # Remove confirm button
        self.confirmButton.hide()
        self.placeButton.show()
        self.deckLabel.show()
        self.pickUpPileButton.show()
        self.pileLabel.setText("Pile: Empty")
        self.currentPlayerLabel.setText("Current Player: ")
            
class GameController(QObject):
    indexAssigned = Signal(int)
    selectedCardsChanged = Signal(int)
    updatePlayerHandSignal = Signal(list)
    updateTopCardsSignal = Signal(list)
    updateBottomCardsSignal = Signal(list)
    updateOtherPlayerCardsSignal = Signal(int, list, list, list)
    startMainViewSignal = Signal()         # Notify when the main game starts
    confirmTopCardsSignal = Signal(int)

    topCardSelectionPhase = True

    def __init__(self, player_index, handCards, bottomCards, numPlayers, broadcastUpdate):
        super().__init__()
        self.player_index = player_index
        self.numPlayers = numPlayers
        self.selectedCards = []  # Track selected cards
        self.topCards = []       # Store top cards
        self.handCards = handCards  # Store hand cards
        self.bottomCards = bottomCards  # Store bottom cards (face down)
        self.broadcastUpdate = broadcastUpdate
        self.topCardConfirms = 0

    def startGame(self):
        self.updatePlayerHandSignal.emit(self.handCards)
        
    def prepareCardPlacement(self, cardIndex, cardLabel):
        """
        Handle selection and deselection of cards for placement.
        """
        card = self.handCards[cardIndex]

        if self.topCardSelectionPhase:
            # Limit to 3 selected cards during top card selection phase
            if (cardIndex, card) in self.selectedCards:
                self.selectedCards.remove((cardIndex, card))
                cardLabel.setStyleSheet("border: 2px solid transparent; background-color: transparent;")
            elif len(self.selectedCards) < 3:
                self.selectedCards.append((cardIndex, card))
                cardLabel.setStyleSheet("border: 2px solid blue; background-color: transparent;")

            # Enable the confirm button if exactly 3 cards are selected
            self.selectedCardsChanged.emit(len(self.selectedCards))

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
        self.broadcastUpdate('confirmedTopCards', {})
        self.broadcastCards()
        self.checkAllPlayersConfirmed()
    
    def checkAllPlayersConfirmed(self):
        if self.topCardConfirms == self.numPlayers:
            self.startMainGame()
            self.broadcastUpdate('startMainGame', {})
    
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
            'playerIndex': self.player_index,
            'handCards': self.handCards,
            'topCards': self.topCards,
            'bottomCards': self.bottomCards
        }
        self.broadcastUpdate('updateCards', payload)
    
    def updateOtherPlayerHand(self, playerIndex, handCards, topCards, bottomCards):
        """
        Update the hand cards of another player.
        """
        if playerIndex != self.player_index:  # Ensure it's not updating its own hand
            self.updateOtherPlayerCardsSignal.emit(playerIndex, handCards, topCards, bottomCards)
    
    def startMainGame(self):
        """
        Transition to the main game phase.
        """
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
