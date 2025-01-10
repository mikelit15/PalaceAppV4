import sys
import socket
import threading
import random
import json
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,\
    QTextEdit, QGridLayout, QSpacerItem, QSizePolicy, QDialog, QMessageBox)
from PySide6.QtGui import QPixmap, QIcon, QTransform, QPainter
from PySide6.QtCore import Qt, QRect, QObject, Signal, QTimer, QMetaObject, Slot, Q_ARG
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
    elif name == "gameView":
        offset = 15
    elif name == "onlineMenu":
        offset = 15
    elif name == "hostLobby":
        offset = 20
    elif name == "joinLobby":
        offset = 20

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

RANKS = {'3': 2, '4': 3, '5': 4, '6': 5, '8': 6, '9': 7, 'J': 8, 'Q': 9, '7': 10, 'K': 11, 'A': 12, '2': 13, '10': 14}
VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}


class GameOverDialog(QDialog):
    playAgainSignal = Signal()
    mainMenuSignal = Signal()
    exitSignal = Signal()

    def __init__(self, winnerName, parentCoords, numPlayers):        
        super().__init__()
        self.numPlayers = numPlayers
        playAgainCount = 0
        self.setWindowTitle("Game Over")
        self.setWindowIcon(QIcon(r"palaceData\palaceIcon.ico"))
        self.setGeometry(805, 350, 300, 200)
        layout = QVBoxLayout()
        label = QLabel(f"Game Over! Player {winnerName} wins!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        self.counterLabel = QLabel(f"Play Again: {playAgainCount}/{numPlayers}")
        self.counterLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.counterLabel)
        buttonBox = QHBoxLayout()
        self.playAgainButton = QPushButton("Play Again")
        self.playAgainButton.clicked.connect(self.playAgain)
        mainMenuButton = QPushButton("Main Menu")
        mainMenuButton.clicked.connect(self.mainMenu)
        exitButton = QPushButton("Exit")
        exitButton.clicked.connect(self.exitGame)
        buttonBox.addWidget(self.playAgainButton)
        buttonBox.addWidget(mainMenuButton)
        buttonBox.addWidget(exitButton)
        layout.addLayout(buttonBox)
        
        self.setLayout(layout)
       
        centerDialog(self, parentCoords, "GameOverDialog")
    
    def playAgain(self):
        self.playAgainButton.setDisabled(True)
        self.playAgainSignal.emit()

    def mainMenu(self):
        self.mainMenuSignal.emit()
        self.accept()

    def exitGame(self):
        self.exitSignal.emit()
        self.accept()

    def updateCounter(self, count):
        self.playAgainCount = count
        self.counterLabel.setText(f"Play Again: {self.playAgainCount}/{self.numPlayers}")
    
### Home Screen ###
class HomeMenu(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.setWindowTitle("Palace")
        self.setWindowIcon(QIcon(r"palaceData\palaceIcon.ico"))
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
        centerDialog(self, parent, "onlineMenu")

    def initUI(self):
        self.setWindowTitle("Online Menu")
        self.setWindowIcon(QIcon(r"palaceData\palaceIcon.ico"))
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
        self.hostLobby = HostLobby(self.parent, self)
        self.hostLobby.show()

    def joinGame(self):
        self.hide()
        self.joinLobby = JoinLobby(self.parent, self)
        self.joinLobby.show()

    def goBack(self):
        self.hide()
        self.parent.show()

### Host Lobby ###
class HostLobby(QDialog):
    updateOtherPlayerHandSignal = Signal(int, list, list, list)
    
    def __init__(self, mainMenu, onlineMenu):
        super().__init__()
        self.parent = onlineMenu
        self.mainMenu = mainMenu
        self.server = None
        self.hostGameView = None
        self.clients = {}  # Map client sockets to indices
        self.nextIndex = 2  # Host is always Player 1
        self.numPlayers = None
        self.playAgainCount = 0
        self.playerNicknames = {}
        self.gameOverDialog = None
        self.hostController = None
        self.initUI()
        centerDialog(self, self.parent, "hostLobby")
        self.startServer()
        
    def initUI(self):
        self.setWindowTitle("Hosting Lobby")
        self.setWindowIcon(QIcon(r"palaceData\palaceIcon.ico"))
        self.setGeometry(700, 300, 400, 300)
        layout = QVBoxLayout()
        
        self.infoLabel = QLabel("Hosting Lobby...\nWaiting for players to join.")
        layout.addWidget(self.infoLabel)

        self.nicknameInput = QLineEdit()
        self.nicknameInput.setPlaceholderText("Enter Nickname")
        layout.addWidget(self.nicknameInput)
        
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
        try:
            if self.server:
                self.shutdownServer()  # Ensure the previous server is closed properly
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server.bind(("0.0.0.0", 12345))
            hostIP = socket.gethostbyname(socket.gethostname())
            self.server.listen(4)
            QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                         Q_ARG(str, f"Server started on {hostIP}, port 12345."))
            threading.Thread(target=self.acceptConnections, daemon=True).start()
        except OSError as e:
            if e.errno == 10048:
                QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, "Host server already running"))

    def acceptConnections(self):
        while self.server:
            try:
                clientSocket, addr = self.server.accept()
                if len(self.clients) < 3:  # Max 4 players (host + 3 clients)
                    index = self.nextIndex
                    self.clients[clientSocket] = index
                    self.nextIndex += 1
                    QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                         Q_ARG(str, f"Player {index} connected from {addr}."))
                    # Notify the client of their player index
                    indexData = json.dumps({"action": "setIndex", "index": index}) + "\n"
                    clientSocket.send(indexData.encode())
                    self.updatePlayerCount()
                    threading.Thread(target=self.handleClient, args=(clientSocket, addr), daemon=True).start()
                else:
                    clientSocket.send(b"Lobby full.\n")
                    clientSocket.close()
            except Exception as e:
                QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, f"Error accepting connections: {e}"))
                break

    def handleClient(self, clientSocket, addr):
        index = self.clients[clientSocket]
        buffer = ""
        try:
            while True:
                message = clientSocket.recv(2048).decode()
                if not message:
                    print(f"Player {index} disconnected unexpectedly: no message received.")
                    break
                buffer += message
                while "\n" in buffer:
                    json_message, buffer = buffer.split("\n", 1)  # Split by delimiter
                    try:
                        print(f"received from Player {index}: {json_message}")
                        data = json.loads(json_message)  # Parse JSON
                        if data['action'] == 'join':
                            nickname = data.get('nickname', f"Player {index}")
                            if nickname != "":
                                QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                                    Q_ARG(str, f"Player {index} joined with nickname: {nickname}"))
                                self.broadcastToClients('updateLog', {'log': f"Player {index} connected from {addr}.\nPlayer {index} joined with nickname: {nickname}"}, exclude=clientSocket)
                                self.playerNicknames[str(index)] = nickname
                            else:
                                QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                                    Q_ARG(str, f"Player {index} joined"))
                        elif data['action'] == 'updateCards':
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
                            self.hostController.startMainGame(data['lowestPlayer'])
                            self.broadcastToClients('startMainGame', data)
                        elif data['action'] == 'startNewGame':
                            self.startNewGame()
                            self.broadcastToClients('startNewGame', data)
                        elif data['action'] == 'updateCurrentPlayer':
                            self.hostController.currentPlayer = data['currentPlayer']
                            self.hostGameView.updateCurrentPlayer(data['currentPlayer'])
                            self.broadcastToClients('updateCurrentPlayer', data, exclude=clientSocket)
                        elif data['action'] == 'gameOver':
                            self.broadcastToClients('gameEnd', {'winner': data['winner']})
                            QMetaObject.invokeMethod(self, "showGameOverDialog", Qt.ConnectionType.QueuedConnection,
                                Q_ARG(int, data['winner']))
                        elif data['action'] == 'updatePlayAgainCount':
                            self.playAgainCount = data['playAgainCount']
                            self.gameOverDialog.updateCounter(data['playAgainCount'])
                            self.broadcastToClients('updatePlayAgainCount', data, exclude=clientSocket)
                        elif data['action'] == 'updateDeck':
                            self.hostController.deck = data['deck']
                            self.hostGameView.updateDeck(data['deck'])
                            self.broadcastToClients('updateDeck', data, exclude=clientSocket)
                        elif data['action'] == 'updatePile':
                            self.hostController.pile = data['pile']
                            self.hostGameView.updatePile(data['pile'])
                            self.broadcastToClients('updatePile', data, exclude=clientSocket)
                        elif data['action'] == 'updatePileLabel':
                            self.hostGameView.updatePileLabel(data['pileLabel'])
                            self.broadcastToClients('updatePileLabel', data, exclude=clientSocket)
                        elif data['action'] == 'sevenSwitch':
                            self.hostController.sevenSwitch = data['sevenSwitch']
                            self.broadcastToClients('sevenSwitch', data, exclude=clientSocket)
                        elif data['action'] == 'playerDisconnected':
                            del self.clients[clientSocket]
                            try:
                                clientSocket.close()  # Ensure the socket is properly closed
                            except Exception as e:
                                print(f"Error closing client socket: {e}")
                            if self.hostController.numPlayers == 2:
                                self.broadcastToClients('gameClose', {})
                                QMetaObject.invokeMethod(self.hostGameView, "returnToMainMenu", Qt.ConnectionType.QueuedConnection)
                                self.shutdownServer()
                            elif self.hostController.numPlayers == 3:
                                self.numPlayers -= 1
                                self.hostController.numPlayers = self.numPlayers
                                allPlayers = [1, 2, 3, 4]
                                remainingPlayers = [p for p in allPlayers if p != index]
                                self.hostGameView.switchToTwoPlayerLayout(remainingPlayers)
                                self.broadcastToClients('switchToTwoPlayerLayout', {'remainingPlayers': remainingPlayers})
                            elif self.hostController.numPlayers == 4:
                                self.numPlayers -= 1
                                self.hostController.numPlayers = self.numPlayers
                                allPlayers = [1, 2, 3, 4]
                                remainingPlayers = [p for p in allPlayers if p != index]
                                self.hostGameView.switchToThreePlayerLayout(remainingPlayers)
                                self.broadcastToClients('switchToThreePlayerLayout', {'remainingPlayers': remainingPlayers})
                        elif data['action'] == 'leaveLobby':
                            del self.clients[clientSocket]
                            try:
                                clientSocket.close()  # Ensure the socket is properly closed
                            except Exception as e:
                                print(f"Error closing client socket: {e}")
                            self.numPlayers -= 1
                            self.gameOverDialog.numPlayers = self.numPlayers
                            if self.numPlayers == 1:
                                QMetaObject.invokeMethod(self.gameOverDialog, "close", Qt.ConnectionType.QueuedConnection)
                                QMetaObject.invokeMethod(self.hostGameView, "returnToMainMenu", Qt.ConnectionType.QueuedConnection)
                                self.shutdownServer()
                            self.gameOverDialog.updateCounter(self.playAgainCount)
                            self.broadcastToClients('updateNumPlayersLobby', {}, exclude=clientSocket)
                            self.checkAllPlayersPlayAgain()
                    except json.JSONDecodeError:
                        print(f"Received invalid data from Player {index}: {message}")
                        break
        except Exception as e:
            print(f"Player {index} disconnected: {e}")
        finally:
            self.clients.pop(clientSocket, None)
            if self.playerNicknames.get(str(index)):
                QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, f"Player {index}: {self.playerNicknames.get(str(index))} disconnected"))
                self.broadcastToClients('updateLog', {'log': f"Player {index}: {self.playerNicknames.get(str(index))} disconnected"})
            else:
                QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, f"Player {index} disconnected"))
                self.broadcastToClients('updateLog', {'log': f"Player {index} disconnected"})
            self.nextIndex -= 1
            self.reassignIndices()
            self.updatePlayerCount()
            clientSocket.close()
    
    @Slot()
    def handleHostDisconnect(self):
        """
        If host is the one disconnecting, then goBack(). 
        This shuts down the server and returns to main menu.
        """
        self.shutdownServer()
    
    @Slot(int)
    def showGameOverDialog(self, winner):
        """
        Ensure the Game Over dialog runs on the main thread safely.
        """
        QTimer.singleShot(0, lambda: self._showGameOverDialogInMainThread(winner))

    def _showGameOverDialogInMainThread(self, winner):
        """
        Create and show the Game Over dialog in the main thread.
        """
        parentCoords = self.geometry()
        self.gameOverDialog = GameOverDialog(winner, parentCoords, self.numPlayers)
        self.gameOverDialog.playAgainSignal.connect(self.playAgain)
        self.gameOverDialog.mainMenuSignal.connect(self.returnToMainMenu)
        self.gameOverDialog.exitSignal.connect(self.quitGame)
        self.gameOverDialog.exec()
    
    def playAgain(self):
        self.playAgainCount += 1
        self.gameOverDialog.updateCounter(self.playAgainCount)
        self.broadcastToClients('updatePlayAgainCount', {'playAgainCount': self.playAgainCount})
        self.checkAllPlayersPlayAgain()
        
    def returnToMainMenu(self):
        self.broadcastToClients('gameClose', {})
        QMetaObject.invokeMethod(self.hostGameView, "returnToMainMenu", Qt.ConnectionType.QueuedConnection)
        self.shutdownServer()
    
    def quitGame(self):
        self.broadcastToClients('gameClose', {})
        QApplication.instance().quit
        
    def checkAllPlayersPlayAgain(self):        
        if self.playAgainCount == self.numPlayers:
            try:
                QMetaObject.invokeMethod(self.gameOverDialog, "close", Qt.ConnectionType.QueuedConnection)
            except Exception:
                pass
            try:
                QMetaObject.invokeMethod(self.hostGameView, "close", Qt.ConnectionType.QueuedConnection)
            except Exception:
                pass
            QMetaObject.invokeMethod(self, "startGame", Qt.ConnectionType.QueuedConnection)
    
    def startNewGame(self):
        try:
            QMetaObject.invokeMethod(self.gameOverDialog, "close", Qt.ConnectionType.QueuedConnection)
        except Exception:
            pass
        try:
            QMetaObject.invokeMethod(self.hostGameView, "close", Qt.ConnectionType.QueuedConnection)
        except Exception:
            pass
        QMetaObject.invokeMethod(self, "startGame", Qt.ConnectionType.QueuedConnection)
    
    def reassignIndices(self):
        """
        Reassign indices after a player disconnects and notify all clients of the updated indices.
        """
        QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, "Reassigning player indices after disconnection."))
        newClients = {}
        newIndex = 2  # Start at 2 since host is Player 1

        for clientSocket in self.clients.keys():
            newClients[clientSocket] = newIndex
            indexData = json.dumps({"action": "setIndex", "index": newIndex}) + "\n"
            clientSocket.send(indexData.encode())
            newIndex += 1

        self.clients = newClients
    
    def updatePlayerCount(self):
        count = len(self.clients) + 1  # Host included
        self.playerCountLabel.setText(f"Players: {count}/4")
        self.startButton.setEnabled(count > 1)  # Enabled only if 2+ players
    
    def broadcastToClients(self, action, data, exclude=None):
        message = json.dumps({"action": action, **data}) + "\n"
        current_clients = list(self.clients.keys())
        for clientSocket in current_clients:
            if clientSocket != exclude:
                try:
                    clientSocket.send(message.encode())
                except Exception as e:
                    QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, f"Error broadcasting to client: {e}"))
    
    @Slot()
    def startGame(self):
        self.playAgainCount = 0
        if self.nicknameInput.text() != "":
            self.playerNicknames[1] = self.nicknameInput.text()
        suits = ['hearts', 'diamonds', 'clubs', 'spades']
        self.deck = [(value, suit, False, False) for value in VALUES.keys() for suit in suits]
        random.shuffle(self.deck)

        self.players = []
        playerData = {}

        for i, client in enumerate(list(self.clients.keys()) + [None], start=1):
            bottomCards = [(card[0], card[1], False, True) for card in self.deck[:3]]
            hand = [(card[0], card[1], False, False) for card in self.deck[3:9]]
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
            'numPlayers': self.numPlayers,
            'nicknames': self.playerNicknames
        }
        payload = json.dumps(data) + "\n"
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
            self.broadcastToClients,
            self.playerNicknames
        )
        self.hostController.gameOverSignal.connect(self.showGameOverDialog)
        self.hostController.hostDisconnectedSignal.connect(self.handleHostDisconnect)
        self.hostGameView = GameView(self.hostController, self.geometry(), self.numPlayers, self.mainMenu)
        self.hostGameView.show()
        self.hostController.startGame()
    
    def shutdownServer(self):
        self.broadcastToClients('shutdownServer', {})
        if self.server:
            for client in list(self.clients.keys()):
                try:
                    client.close()
                except Exception as e:
                    QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, f"Error closing client connection: {e}"))
            self.clients.clear()
            self.server.close()
            self.server = None
            print("Server shut down.")

    def goBack(self):
        self.shutdownServer()
        self.hide()
        self.parent.show()

    def closeEvent(self, event):
        """
        Override the closeEvent to confirm shutdown.
        """
        reply = QMessageBox.question(
            self,
            'Quit Confirmation',
            'Are you sure you want to quit hosting?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            QMetaObject.invokeMethod(self.hostGameView, "returnToMainMenu", Qt.ConnectionType.QueuedConnection)
            self.shutdownServer()
            event.accept()
        else:
            event.ignore()

### Join Lobby ###
class JoinLobby(QDialog):
    startGameSignal = Signal(int)
    def __init__(self, mainMenu, onlineMenu):
        super().__init__()
        self.parent = onlineMenu
        self.mainMenu = mainMenu
        self.client = None
        self.controller = None
        self.connected = False  # Track connection status
        self.playerIndex = None  # Store the assigned player index
        self.numPlayers = None
        self.playAgainCount = 0
        self.gameView = None
        self.playerNicknames = {}
        self.initUI()
        centerDialog(self, self.parent, "joinLobby")

        # Connect the startGameSignal to the startGame slot
        self.startGameSignal.connect(self.startGame)

    def initUI(self):
        self.setWindowTitle("Join Lobby")
        self.setWindowIcon(QIcon(r"palaceData\palaceIcon.ico"))
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
        
        self.leaveButton = QPushButton("Leave Server")
        self.leaveButton.setStyleSheet("""
            QPushButton {
                background-color: red;
                color: white;
            }
            QPushButton:hover {
                background-color: #FF6666;
                color: lightgray;
            }
        """)
        self.leaveButton.clicked.connect(self.closeEvent2)
        self.leaveButton.setVisible(False)
        layout.addWidget(self.leaveButton)

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
            QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, "Connected to server."))
            self.connected = True
            self.joinButton.setDisabled(True)
            self.leaveButton.show()
            # Send a join message to the host
            initialData = {
                'action': 'join',
                'nickname': nickname
            }
            self.client.send(json.dumps(initialData).encode() + b"\n")

            # Start listening to the server
            threading.Thread(target=self.listenToServer, daemon=True).start()
        except Exception as e:
            QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, f"Failed to connect: {e}"))

    def listenToServer(self):
        buffer = ""
        try:
            while True:
                message = self.client.recv(2048).decode()
                if not message:
                    print("Server closed the connection.")
                    break
                buffer += message  # Accumulate received data
                while "\n" in buffer:
                    json_message, buffer = buffer.split("\n", 1)  # Split by delimiter
                    try:
                        data = json.loads(json_message)  # Deserialize JSON
                        print(f"received from server: {data}")
                        if data["action"] == "setIndex":
                            self.playerIndex = data["index"]
                            QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                                Q_ARG(str, f"Assigned Player {self.playerIndex}"))
                        elif data["action"] == "deckSync":
                            QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                                Q_ARG(str, "Deck and player data received."))
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
                            lowestPlayer = data['lowestPlayer']
                            self.controller.clockwise = data['direction']
                            self.controller.startMainGame(lowestPlayer)
                        elif data['action'] == 'confirmedTopCards':
                            self.controller.topCardConfirms += 1
                            self.controller.checkAllPlayersConfirmed()
                        elif data['action'] == 'gameOver':
                            self.broadcastUpdate('gameOver', data)
                        elif data['action'] == 'gameEnd':
                            QMetaObject.invokeMethod(self, "showGameOverDialog", Qt.ConnectionType.QueuedConnection,
                                Q_ARG(int, data['winner']))
                        elif data['action'] == 'updatePlayAgainCount':
                            self.playAgainCount = data['playAgainCount']
                            self.gameOverDialog.updateCounter(data['playAgainCount'])
                        elif data['action'] == 'updateDeck':
                            self.controller.deck = data['deck']
                            self.gameView.updateDeck(data['deck'])
                        elif data['action'] == 'updatePile':
                            self.controller.pile = data['pile']
                            self.gameView.updatePile(data['pile'])
                        elif data['action'] == 'updatePileLabel':
                            self.gameView.updatePileLabel(data['pileLabel'])
                        elif data['action'] == 'sevenSwitch':
                            self.controller.sevenSwitch = data['sevenSwitch']
                        elif data['action'] == 'playerDisconnected':
                            if self.controller.numPlayers == 2:
                                self.broadcastUpdate('playerDisconnected', {})
                        elif data['action'] == 'switchToTwoPlayerLayout':
                            self.numPlayers -= 1
                            self.controller.numPlayers = self.numPlayers
                            self.gameView.switchToTwoPlayerLayout(data['remainingPlayers'])
                        elif data['action'] == 'switchToThreePlayerLayout':
                            self.numPlayers -= 1
                            self.controller.numPlayers = self.numPlayers
                            self.gameView.switchToThreePlayerLayout(data['remainingPlayers'])
                        elif data['action'] == 'gameClose':
                            try:
                                QMetaObject.invokeMethod(self.gameOverDialog, "close", Qt.ConnectionType.QueuedConnection)
                            except Exception:
                                pass
                            QMetaObject.invokeMethod(self.gameView, "returnToMainMenu", Qt.ConnectionType.QueuedConnection)
                            self.leaveServer()
                        elif data['action'] == 'updateNumPlayersLobby':
                            self.numPlayers -= 1
                            self.gameOverDialog.numPlayers = self.numPlayers
                            self.gameOverDialog.updateCounter(self.playAgainCount)
                        elif data['action'] == 'updateLog':
                            QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                                Q_ARG(str, data['log']))
                        elif data['action'] == 'shutdownServer':
                            QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                                Q_ARG(str, "Server shutdown by host."))
                            self.leaveButton.hide()
                            self.joinButton.setDisabled(False)
                    except Exception as e:
                        print(f"Error processing server message: {e}") 
        except Exception as e:
            print(f"Error in listenToServer: {e}")
        finally:
            print("Exiting listenToServer and closing client socket.")
    
    @Slot(int)
    def showGameOverDialog(self, winner):
        """
        Ensure the Game Over dialog runs on the main thread safely.
        """
        QTimer.singleShot(0, lambda: self._showGameOverDialogInMainThread(winner))

    def _showGameOverDialogInMainThread(self, winner):
        """
        Create and show the Game Over dialog in the main thread.
        """
        parentCoords = self.geometry()
        self.gameOverDialog = GameOverDialog(winner, parentCoords, self.numPlayers)
        self.gameOverDialog.playAgainSignal.connect(self.playAgain)
        self.gameOverDialog.mainMenuSignal.connect(self.returnToMainMenu)
        self.gameOverDialog.exitSignal.connect(self.quitGame)
        self.gameOverDialog.exec()
    
    def playAgain(self):
        self.playAgainCount += 1
        self.gameOverDialog.updateCounter(self.playAgainCount)
        self.broadcastUpdate('updatePlayAgainCount', {'playAgainCount': self.playAgainCount})
        self.checkAllPlayersPlayAgain()
        
    def returnToMainMenu(self):
        if self.connected:
            self.broadcastUpdate('leaveLobby', {})
        QMetaObject.invokeMethod(self.gameView, "close", Qt.ConnectionType.QueuedConnection)
        QMetaObject.invokeMethod(self.gameView, "returnToMainMenu", Qt.ConnectionType.QueuedConnection)
        if self.connected:
            self.leaveServer()
        
    def quitGame(self):
        self.broadcastUpdate('leaveLobby', {})
        QApplication.instance().quit
    
    def checkAllPlayersPlayAgain(self):        
        if self.playAgainCount == self.numPlayers:
            self.broadcastUpdate('startNewGame', {})
    
    def broadcastUpdate(self, action, data):
        message = json.dumps({"action": action, **data}) + "\n"
        try:
            self.client.send(message.encode())
        except Exception as e:
            print(f"Error sending update: {e}")
    
    def confirmTopCards(self):
        if self.controller:
            self.controller.confirmTopCards()
            payload = {'action': 'confirmTopCards', 'playerIndex': self.playerIndex}
            self.broadcastUpdate('confirmTopCards', payload)
    
    def processDeckSync(self, data):
        try:
            QMetaObject.invokeMethod(self.gameOverDialog, "close", Qt.ConnectionType.QueuedConnection)
        except Exception:
            pass
        try:
            QMetaObject.invokeMethod(self.gameView, "close", Qt.ConnectionType.QueuedConnection)
        except Exception:
            pass
        self.playerNicknames = data.get("nicknames", {})
        self.deck = data.get("deck", [])
        players = data.get("players", {})
        playerKey = f'player{self.playerIndex}'
        self.numPlayers = data.get('numPlayers')
        self.handCards = players.get(playerKey, {}).get('hand', [])
        self.bottomCards = players.get(playerKey, {}).get('bottomCards', [])
        self.startGameSignal.emit(self.playerIndex)

    def leaveServer(self):
        if self.client:
            try:
                self.client.close()
            except Exception as e:
                QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
                    Q_ARG(str, f"Error closing client connection: {e}"))
            finally:
                self.client = None
        self.connected = False
        self.leaveButton.hide()
        self.joinButton.setDisabled(False)
        QMetaObject.invokeMethod(self.logText, "append", Qt.ConnectionType.QueuedConnection,
            Q_ARG(str, "Disconnected from server."))
    
    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            'Quit Confirmation',
            'Are you sure you want to leave the lobby?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.returnToMainMenu()

            
    def closeEvent2(self, event):
        reply = QMessageBox.question(
            self,
            'Quit Confirmation',
            'Are you sure you want to leave the lobby?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.leaveServer()
    
    def goBack(self):
        if self.connected:
            self.leaveServer()
        self.hide()
        self.parent.show()

    def startGame(self, playerIndex):
        self.playAgainCount = 0
        print(f"Starting game as Player {playerIndex}.")
        self.hide()
        self.controller = GameController(
            self.deck,
            self.playerIndex,
            self.handCards,
            self.bottomCards,
            self.numPlayers,
            self.broadcastUpdate,
            self.playerNicknames
        )
        self.gameView = GameView(self.controller, self.geometry(), self.numPlayers, self.mainMenu)
        self.gameView.show()
        self.controller.startGame()


class GameView(QWidget):
    
    twoPlayerLayoutSignal = Signal()
    threePlayerLayoutSignal = Signal()
    
    def __init__(self, controller, parentCoords, numPlayers, mainMenu):
        super().__init__()
        self.controller = controller
        self.gameOverDialog = None
        self.mainMenu = mainMenu
        self.numPlayers = numPlayers
        self.playerIndex = self.controller.playerIndex
        self.selectedCards = []
        self.playAgainCount = 0
        self.initUI()
        centerDialog(self, parentCoords, "gameView")
                
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
        self.controller.updatePileLabelSignal.connect(self.updatePileLabel)
        self.controller.updateDeckSignal.connect(self.updateDeck)
        self.controller.playerDisconnectedSignal.connect(self.returnToMainMenu)
        self.controller.gameWonSignal.connect(self.gameOver)
        
        self.twoPlayerLayoutSignal.connect(self.initTwoPlayerLayout)
        self.threePlayerLayoutSignal.connect(self.initThreePlayerLayout)
        
    def initUI(self):
        self.setWindowTitle(f'Palace Card Game - Player {self.playerIndex}')
        self.setWindowIcon(QIcon(r"palaceData\palaceIcon.ico"))
        self.setGeometry(450, 75, 900, 900)
        self.layout = QGridLayout()

        # Disconnect Button
        self.disconnectButton = QPushButton("Disconnect")
        self.disconnectButton.setFixedWidth(125)
        self.disconnectButton.clicked.connect(self.closeEvent)
        if self.numPlayers == 2:
            self.layout.addWidget(self.disconnectButton, 1, 1, alignment=Qt.AlignmentFlag.AlignTop)
            self.layout.addWidget(self.disconnectButton, 0, 2)
            self.layout.addWidget(self.disconnectButton, 0, 14)
            self.layout.addWidget(self.disconnectButton, 0, 15)
        elif self.numPlayers == 3:
            self.layout.addWidget(self.disconnectButton, 1, 1, alignment=Qt.AlignmentFlag.AlignTop)
            self.layout.addWidget(self.disconnectButton, 0, 14)
        else:
            self.layout.addWidget(self.disconnectButton, 1, 1, alignment=Qt.AlignmentFlag.AlignTop)
        
        self.spacerButtonTopBottom = QLabel()
        self.spacerButtonTopBottom.setFixedWidth(125)
        
        self.spacerButtonLeftRight = QLabel()
        self.spacerButtonLeftRight.setFixedHeight(125)

        # Center Console
        self.initCenterConsole()
        
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
        
        buttonsTopContainerLayout.addWidget(self.spacerButtonTopBottom, alignment=Qt.AlignmentFlag.AlignCenter)
        buttonsLeftContainerLayout.addWidget(self.spacerButtonLeftRight, alignment=Qt.AlignmentFlag.AlignCenter)
        buttonsRightContainerLayout.addWidget(self.spacerButtonLeftRight, alignment=Qt.AlignmentFlag.AlignCenter)
        buttonsBottomContainerLayout.addWidget(self.confirmButton, alignment=Qt.AlignmentFlag.AlignCenter)
        buttonsBottomContainerLayout.addWidget(self.placeButton, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(buttonsTopContainerLayout, 0, 6, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(buttonsBottomContainerLayout, 12, 6, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Dynamic Layout Adjustment
        if self.numPlayers == 2:
            self.initTwoPlayerLayout()
        elif self.numPlayers == 3:
            self.layout.addLayout(buttonsLeftContainerLayout, 6, 0, alignment=Qt.AlignmentFlag.AlignCenter)
            self.initThreePlayerLayout()
        elif self.numPlayers == 4:
            self.layout.addLayout(buttonsLeftContainerLayout, 6, 0, alignment=Qt.AlignmentFlag.AlignCenter)
            self.layout.addLayout(buttonsRightContainerLayout, 6, 12, alignment=Qt.AlignmentFlag.AlignCenter)
            self.initFourPlayerLayout()
        
        self.setLayout(self.layout)

    def initCenterConsole(self):
        """
        Initializes the center console with the deck, pile, and current player information.
        """
        self.deckLabel = QLabel()
        self.deckLabel.setFixedWidth(192)
        self.deckLabel.hide()
        
        self.pileLabel = QLabel("\t     Select your 3 Top cards...")
        self.pileLabel.setFixedHeight(BUTTON_HEIGHT + 10)

        self.pickUpPileButton = QPushButton("Pick Up Pile")
        self.pickUpPileButton.setFixedWidth(123)
        self.pickUpPileButton.clicked.connect(self.controller.pickUpPile)
        self.pickUpPileButton.hide()
        
        self.currentPlayerLabel = QLabel("")
        spacer = QSpacerItem(60, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
    
        self.consoleLayout = QHBoxLayout()
        self.consoleLayout.addWidget(self.deckLabel, alignment=Qt.AlignmentFlag.AlignLeft)
        self.consoleLayout.addWidget(self.pileLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.consoleLayout.addItem(spacer)
        self.consoleLayout.addWidget(self.pickUpPileButton, alignment=Qt.AlignmentFlag.AlignRight)

        self.centerContainer = QWidget()
        self.centerContainer.setLayout(self.consoleLayout)
        self.centerContainer.setFixedWidth(460)
        
        self.centerLayout = QVBoxLayout()
        self.centerLayout.addWidget(QLabel(""))
        self.centerLayout.addWidget(self.currentPlayerLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.centerLayout.addWidget(self.centerContainer, alignment=Qt.AlignmentFlag.AlignCenter)
        self.centerLayout.addWidget(QLabel(""))
        self.centerLayout.addWidget(QLabel(""))

        self.layout.addLayout(self.centerLayout, 6, 6, alignment=Qt.AlignmentFlag.AlignCenter)
    
    def initPlayerAreaTop(self, labelText, position):
        """
        Helper function to initialize a player area (hand, top cards, bottom cards).
        """
        layout = QVBoxLayout()
        
        playerHandContainer = QWidget()
        playerHandContainer.setMaximumWidth(400)
        handLayout = QHBoxLayout(playerHandContainer)
        playerHandContainerLayout = QHBoxLayout()
        playerHandContainerLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        playerHandContainerLayout.addWidget(playerHandContainer, alignment=Qt.AlignmentFlag.AlignCenter)
        playerHandContainerLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        layout.addLayout(playerHandContainerLayout)
        
        handLabelLayout = QLabel(labelText)
        layout.addWidget(handLabelLayout, alignment=Qt.AlignmentFlag.AlignCenter)
            
        topCardsLayout = QHBoxLayout()
        layout.addLayout(topCardsLayout)

        bottomCardsLayout = QHBoxLayout()
        layout.addLayout(bottomCardsLayout)

        for _ in range(3):  # Assume max 3 cards for each area
            handSpacer = QLabel()
            handSpacer.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            handSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            handLayout.addWidget(handSpacer)

            topSpacer = QLabel()
            topSpacer.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            topSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            topCardsLayout.addWidget(topSpacer)

            bottomSpacer = QLabel()
            bottomSpacer.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
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
        
        playerHandContainer = QWidget()
        playerHandContainer.setMaximumWidth(400)
        handLayout = QHBoxLayout(playerHandContainer)
        playerHandContainerLayout = QHBoxLayout()
        playerHandContainerLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        playerHandContainerLayout.addWidget(playerHandContainer, alignment=Qt.AlignmentFlag.AlignCenter)
        playerHandContainerLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        layout.addLayout(playerHandContainerLayout)

        for _ in range(3):  # Assume max 3 cards for each area
            handSpacer = QLabel()
            handSpacer.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            handSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            handLayout.addWidget(handSpacer)

            topSpacer = QLabel()
            topSpacer.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            topSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            topCardsLayout.addWidget(topSpacer)

            bottomSpacer = QLabel()
            bottomSpacer.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            bottomSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            bottomCardsLayout.addWidget(bottomSpacer)

        self.layout.addLayout(layout, *position)
        return handLayout, handLabelLayout, topCardsLayout, bottomCardsLayout

    def initPlayerAreaLeft(self, labelText, position):
        """
        Helper function to initialize a player area (hand, top cards, bottom cards).
        """
        layout = QHBoxLayout()
        
        playerHandContainer = QWidget()
        playerHandContainer.setMaximumHeight(250)
        handLayout = QVBoxLayout(playerHandContainer)
        playerHandContainerLayout = QVBoxLayout()
        playerHandContainerLayout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        playerHandContainerLayout.addWidget(playerHandContainer, alignment=Qt.AlignmentFlag.AlignCenter)
        playerHandContainerLayout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        layout.addLayout(playerHandContainerLayout)
        
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
            handSpacer.setFixedSize(BUTTON_HEIGHT, BUTTON_WIDTH)
            handSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            handLayout.addWidget(handSpacer)

            topSpacer = QLabel()
            topSpacer.setFixedSize(BUTTON_HEIGHT, BUTTON_WIDTH)
            topSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            topCardsLayout.addWidget(topSpacer)

            bottomSpacer = QLabel()
            bottomSpacer.setFixedSize(BUTTON_HEIGHT, BUTTON_WIDTH)
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
        
        playerHandContainer = QWidget()
        playerHandContainer.setMaximumHeight(250)
        handLayout = QVBoxLayout(playerHandContainer)
        playerHandContainerLayout = QVBoxLayout()
        playerHandContainerLayout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        playerHandContainerLayout.addWidget(playerHandContainer, alignment=Qt.AlignmentFlag.AlignCenter)
        playerHandContainerLayout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        layout.addLayout(playerHandContainerLayout)

        for _ in range(3):  # Assume max 3 cards for each area
            handSpacer = QLabel()
            handSpacer.setFixedSize(BUTTON_HEIGHT, BUTTON_WIDTH)
            handSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            handLayout.addWidget(handSpacer)

            topSpacer = QLabel()
            topSpacer.setFixedSize(BUTTON_HEIGHT, BUTTON_WIDTH)
            topSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            topCardsLayout.addWidget(topSpacer)

            bottomSpacer = QLabel()
            bottomSpacer.setFixedSize(BUTTON_HEIGHT, BUTTON_WIDTH)
            bottomSpacer.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
            bottomCardsLayout.addWidget(bottomSpacer)

        self.layout.addLayout(layout, *position)
        return handLayout, handLabelLayout, topCardsLayout, bottomCardsLayout

    def initTwoPlayerLayout(self):
        """
        Initializes the layout for a two-player game.
        """
        if hasattr(self, 'topHand'):
            self.clearPlayerLayout(self.topHand, self.topHandLabel, self.topTop, self.topBottom)
        if hasattr(self, 'leftHand'):
            self.clearPlayerLayout(self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom)
        if hasattr(self, 'playerHand'):
            self.clearPlayerLayout(self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom)
        if self.playerIndex == 1:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 6))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop(f"{self.controller.playerNicknames.get('2', 'Player 2')}'s Hand", (1, 6))
        else:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 6))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop(f"{self.controller.playerNicknames.get('1', 'Player 1')}'s Hand", (1, 6))

    def initThreePlayerLayout(self):
        """
        Initializes the layout for a three-player game.
        """
        if hasattr(self, 'topHand'):
            self.clearPlayerLayout(self.topHand, self.topHandLabel, self.topTop, self.topBottom)
        if hasattr(self, 'leftHand'):
            self.clearPlayerLayout(self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom)
        if hasattr(self, 'rightHand'):
            self.clearPlayerLayout(self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom)
        if hasattr(self, 'playerHand'):
            self.clearPlayerLayout(self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom)
        if self.playerIndex == 1:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 6))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft(f"{self.controller.playerNicknames.get('2', 'Player 2')}'s Hand", (6, 1))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop(f"{self.controller.playerNicknames.get('3', 'Player 3')}'s Hand", (1, 6))
        elif self.playerIndex == 2:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 6))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft(f"{self.controller.playerNicknames.get('3', 'Player 3')}'s Hand", (6, 1))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop(f"{self.controller.playerNicknames.get('1', 'Player 1')}'s Hand", (1, 6))
        elif self.playerIndex == 3:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 6))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft(f"{self.controller.playerNicknames.get('1', 'Player 1')}'s Hand", (6, 1))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop(f"{self.controller.playerNicknames.get('2', 'Player 2')}'s Hand", (1, 6))

    def initFourPlayerLayout(self):
        """
        Initializes the layout for a four-player game.
        """
        if self.playerIndex == 1:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 6))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft(f"{self.controller.playerNicknames.get('2', 'Player 2')}'s Hand", (6, 1))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop(f"{self.controller.playerNicknames.get('3', 'Player 3')}'s Hand", (1, 6))
            self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom = self.initPlayerAreaRight(f"{self.controller.playerNicknames.get('4', 'Player 4')}'s Hand", (6, 10))
        elif self.playerIndex == 2:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 6))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft(f"{self.controller.playerNicknames.get('3', 'Player 3')}'s Hand", (6, 1))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop(f"{self.controller.playerNicknames.get('4', 'Player 4')}'s Hand", (1, 6))
            self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom = self.initPlayerAreaRight(f"{self.controller.playerNicknames.get(1, 'Player 1')}'s Hand", (6, 10))
        elif self.playerIndex == 3:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 6))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft(f"{self.controller.playerNicknames.get('4', 'Player 4')}'s Hand", (6, 1))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop(f"{self.controller.playerNicknames.get('1', 'Player 1')}'s Hand", (1, 6))
            self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom = self.initPlayerAreaRight(f"{self.controller.playerNicknames.get('2', 'Player 2')}'s Hand", (6, 10))
        elif self.playerIndex == 4:
            self.playerHand, self.playerHandLabel, self.playerTop, self.playerBottom = self.initPlayerAreaBot("Your Hand", (11, 6))
            self.leftHand, self.leftHandLabel, self.leftTop, self.leftBottom = self.initPlayerAreaLeft(f"{self.controller.playerNicknames.get('1', 'Player 1')}'s Hand", (6, 1))
            self.topHand, self.topHandLabel, self.topTop, self.topBottom = self.initPlayerAreaTop(f"{self.controller.playerNicknames.get('2', 'Player 2')}'s Hand", (1, 6))
            self.rightHand, self.rightHandLabel, self.rightTop, self.rightBottom = self.initPlayerAreaRight(f"{self.controller.playerNicknames.get('3', 'Player 3')}'s Hand", (6, 10))
    
    def switchToTwoPlayerLayout(self, remainingPlayers):
        # Clear existing layouts for the top, left, or right players
        if self.controller.playerIndex == 1 and 2 in remainingPlayers:
            self.numPlayers = 2
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 2
            storedCards = self.controller.allPlayerCards.get(3, {}).get('handCards', []) + \
                          self.controller.allPlayerCards.get(3, {}).get('topCards', []) + \
                          self.controller.allPlayerCards.get(3, {}).get('bottomCards', [])
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(2, {}),
            }
        elif self.controller.playerIndex == 1 and 3 in remainingPlayers:
            self.numPlayers = 2
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 3
            storedCards = self.controller.allPlayerCards.get(2, {}).get('handCards', []) + \
                          self.controller.allPlayerCards.get(2, {}).get('topCards', []) + \
                          self.controller.allPlayerCards.get(2, {}).get('bottomCards', [])
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(3, {}),
            }
        elif self.controller.playerIndex == 2:
            self.numPlayers = 2
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 2
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(2, {}),
            }
        elif self.controller.playerIndex == 3:
            self.playerIndex = 2
            self.controller.playerIndex = self.playerIndex
            self.numPlayers = 2
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 2
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(3, {}),
            }
        
        self.controller.currentPlayerChangedSignal.emit(self.controller.currentPlayer)
        
        # Reinitialize the layout for a 2-player game
        if self.playerIndex == 1:
            topPlayerCards = self.controller.allPlayerCards.get(2, {})
        elif self.playerIndex == 2:
            topPlayerCards = self.controller.allPlayerCards.get(1, {})
        self.twoPlayerLayoutSignal.emit()
        
        if not self.controller.topCardSelectionPhase:
            self.controller.updateBottomCardsSignal.emit(self.controller.bottomCards)
        self.controller.updateTopCardsSignal.emit(self.controller.topCards)
        self.controller.updatePlayerHandSignal.emit(self.controller.handCards)
        if self.playerIndex == 1:
            if self.controller.deck and storedCards:
                random.shuffle(storedCards)
                self.controller.deck.extend(storedCards)
                self.controller.updateDeckSignal.emit(self.controller.deck)
                self.controller.broadcastUpdate('updateDeck', {'deck': self.controller.deck})
            self.controller.updateOtherPlayerCardsSignal.emit(2, topPlayerCards.get('handCards', []), topPlayerCards.get('topCards', []), topPlayerCards.get('bottomCards', []))
        elif self.playerIndex == 2:
            self.controller.updateOtherPlayerCardsSignal.emit(1, topPlayerCards.get('handCards', []), topPlayerCards.get('topCards', []), topPlayerCards.get('bottomCards', []))
        
        self.setWindowTitle(f'Palace Card Game - Player {self.playerIndex}')
        
    def switchToThreePlayerLayout(self, remainingPlayers):
        # Clear existing layouts for the top, left, or right players
        if self.controller.playerIndex == 1 and 2 in remainingPlayers and 3 in remainingPlayers:
            self.numPlayers = 3
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 2
            storedCards = self.controller.allPlayerCards.get(4, {}).get('handCards', []) + \
                          self.controller.allPlayerCards.get(4, {}).get('topCards', []) + \
                          self.controller.allPlayerCards.get(4, {}).get('bottomCards', [])
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(2, {}),
                3: self.controller.allPlayerCards.get(3, {}),
            }
        elif self.controller.playerIndex == 1 and 2 in remainingPlayers and 4 in remainingPlayers:
            self.numPlayers = 3
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 2
            storedCards = self.controller.allPlayerCards.get(3, {}).get('handCards', []) + \
                          self.controller.allPlayerCards.get(3, {}).get('topCards', []) + \
                          self.controller.allPlayerCards.get(3, {}).get('bottomCards', [])
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(2, {}),
                3: self.controller.allPlayerCards.get(4, {}),
            }
        elif self.controller.playerIndex == 1 and 3 in remainingPlayers and 4 in remainingPlayers:
            self.numPlayers = 3
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 3
            storedCards = self.controller.allPlayerCards.get(2, {}).get('handCards', []) + \
                          self.controller.allPlayerCards.get(2, {}).get('topCards', []) + \
                          self.controller.allPlayerCards.get(2, {}).get('bottomCards', [])
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(3, {}),
                3: self.controller.allPlayerCards.get(4, {}),
            }
        elif self.controller.playerIndex == 2 and 1 in remainingPlayers and 3 in remainingPlayers:
            self.numPlayers = 3
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 2
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(2, {}),
                3: self.controller.allPlayerCards.get(3, {}),
            }
        elif self.controller.playerIndex == 2 and 1 in remainingPlayers and 4 in remainingPlayers:
            self.numPlayers = 3
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 2
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(2, {}),
                3: self.controller.allPlayerCards.get(4, {}),
            }
        elif self.controller.playerIndex == 3 and 1 in remainingPlayers and 2 in remainingPlayers:
            self.numPlayers = 3
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 3
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(2, {}),
                3: self.controller.allPlayerCards.get(3, {}),
            }
        elif self.controller.playerIndex == 3 and 1 in remainingPlayers and 4 in remainingPlayers:
            self.numPlayers = 3
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 3
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(3, {}),
                3: self.controller.allPlayerCards.get(4, {}),
            }
        elif self.controller.playerIndex == 4 and 1 in remainingPlayers and 2 in remainingPlayers:
            self.playerIndex = 3
            self.controller.playerIndex = self.playerIndex
            self.numPlayers = 3
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 3
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(2, {}),
                3: self.controller.allPlayerCards.get(4, {}),
            }
        elif self.controller.playerIndex == 4 and 1 in remainingPlayers and 3 in remainingPlayers:
            self.playerIndex = 3
            self.controller.playerIndex = self.playerIndex
            self.numPlayers = 3
            self.controller.numPlayers = self.numPlayers
            self.controller.currentPlayer = 3
            self.controller.allPlayerCards = {
                1: self.controller.allPlayerCards.get(1, {}),
                2: self.controller.allPlayerCards.get(3, {}),
                3: self.controller.allPlayerCards.get(4, {}),
            }

        self.controller.currentPlayerChangedSignal.emit(self.controller.currentPlayer) 
        
        if self.playerIndex == 1:
            leftPlayerCards = self.controller.allPlayerCards.get(2, {})
            topPlayerCards = self.controller.allPlayerCards.get(3, {})
        elif self.playerIndex == 2:
            leftPlayerCards = self.controller.allPlayerCards.get(3, {})
            topPlayerCards = self.controller.allPlayerCards.get(1, {})
        elif self.playerIndex == 3:
            leftPlayerCards = self.controller.allPlayerCards.get(1, {})
            topPlayerCards = self.controller.allPlayerCards.get(2, {})
        
        self.threePlayerLayoutSignal.emit()

        # Update signals for the current player and other players
        if not self.controller.topCardSelectionPhase:
            self.controller.updateBottomCardsSignal.emit(self.controller.bottomCards)
        self.controller.updateTopCardsSignal.emit(self.controller.topCards)
        self.controller.updatePlayerHandSignal.emit(self.controller.handCards)

        if self.playerIndex == 1:
            if self.controller.deck and storedCards:
                random.shuffle(storedCards)
                self.controller.deck.extend(storedCards)
                self.controller.updateDeckSignal.emit(self.controller.deck)
                self.controller.broadcastUpdate('updateDeck', {'deck': self.controller.deck})
            self.controller.updateOtherPlayerCardsSignal.emit(2, leftPlayerCards.get('handCards', []), leftPlayerCards.get('topCards', []), leftPlayerCards.get('bottomCards', []))
            self.controller.updateOtherPlayerCardsSignal.emit(3, topPlayerCards.get('handCards', []), topPlayerCards.get('topCards', []), topPlayerCards.get('bottomCards', []))
        elif self.playerIndex == 2:
            self.controller.updateOtherPlayerCardsSignal.emit(3, leftPlayerCards.get('handCards', []), leftPlayerCards.get('topCards', []), leftPlayerCards.get('bottomCards', []))
            self.controller.updateOtherPlayerCardsSignal.emit(1, topPlayerCards.get('handCards', []), topPlayerCards.get('topCards', []), topPlayerCards.get('bottomCards', []))
        elif self.playerIndex == 3:
            self.controller.updateOtherPlayerCardsSignal.emit(1, leftPlayerCards.get('handCards', []), leftPlayerCards.get('topCards', []), leftPlayerCards.get('bottomCards', []))
            self.controller.updateOtherPlayerCardsSignal.emit(2, topPlayerCards.get('handCards', []), topPlayerCards.get('topCards', []), topPlayerCards.get('bottomCards', []))
        
        self.setWindowTitle(f'Palace Card Game - Player {self.playerIndex}')
        
    def clearPlayerLayout(self, handLayout, handLabel, topLayout, bottomLayout):
            layouts = [handLayout, topLayout, bottomLayout]
            for layout in layouts:
                while layout.count():
                    item = layout.takeAt(0)
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()
            if handLabel:
                handLabel.deleteLater()
    
    def updateHandCards(self, handCards):
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
        for idx, card in enumerate(handCards):
            button = QLabel()
            button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            button.setStyleSheet("border: 2px solid transparent; background-color: transparent;")
            if card:
                if not card[3]:
                    pixmap = QPixmap(fr"palaceData\cards\{card[0].lower()}_of_{card[1].lower()}.png").scaled(
                        CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                    )
                    button.setPixmap(pixmap)
                    button.setAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    pixmap = QPixmap(fr"palaceData\cards\back.png").scaled(
                        CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                    )
                    button.setPixmap(pixmap)
                    button.setAlignment(Qt.AlignmentFlag.AlignCenter)
                # Add mouse press event for card selection
                button.mousePressEvent = lambda event, idx=idx, btn=button: self.controller.prepareCardPlacement(idx, btn)
            self.playerHand.addWidget(button)
        
        if not handCards:
            for _ in range(3):  # Assume maximum 3 placeholders
                placeholder = QLabel()
                placeholder.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
                placeholder.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
                self.playerHand.addWidget(placeholder)
    
    def updateTopCards(self, topCards):
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
        for card in topCards:
            button = QLabel()
            button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            pixmap = QPixmap(fr"palaceData\cards\{card[0].lower()}_of_{card[1].lower()}.png").scaled(
                CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            button.setPixmap(pixmap)
            button.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.playerTop.addWidget(button)

        # Add placeholders if no top cards
        if not topCards:
            for _ in range(3):  
                placeholder = QLabel()
                placeholder.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
                placeholder.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
                self.playerTop.addWidget(placeholder)

    def updateBottomCards(self, bottomCards):
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
        for card in bottomCards:
            button = QLabel()
            button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            button.setStyleSheet("border: 0px solid black; background-color: transparent;")
            pixmap = QPixmap(r"palaceData\cards\back.png").scaled(
                CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            button.setPixmap(pixmap)
            button.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.playerBottom.addWidget(button)

        # Add a placeholder if no bottom cards
        if not bottomCards:
            for _ in range(3):
                placeholder = QLabel()
                placeholder.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
                placeholder.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
                self.playerBottom.addWidget(placeholder)

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
            if cards:
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
                    if cardType == 'top':  # Top and hand cards (face up)
                        pixmap = QPixmap(fr"palaceData\cards\{card[0].lower()}_of_{card[1].lower()}.png").scaled(
                            *pixmapDimensions, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                        )
                    else:  # Bottom cards (face down)
                        pixmap = QPixmap(fr"palaceData\cards\back.png").scaled(
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
            else:
                rotatedDimensions = (BUTTON_HEIGHT, BUTTON_WIDTH)
                standardDimensions = (BUTTON_WIDTH, BUTTON_HEIGHT)
                for _ in range(3):  # Assume a maximum of 3 placeholders
                    placeholder = QLabel()
                    if layout in [getattr(self, 'leftHand', None), getattr(self, 'rightHand', None),
                                getattr(self, 'leftTop', None), getattr(self, 'rightTop', None),
                                getattr(self, 'leftBottom', None), getattr(self, 'rightBottom', None)]:
                        placeholder.setFixedSize(*rotatedDimensions)
                        rotate = True
                    else:
                        placeholder.setFixedSize(*standardDimensions)
                    placeholder.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
                    layout.addWidget(placeholder)
    
    def updateConfirmButton(self, selectedCount):
        """
        Enable the confirm button only when exactly 3 cards are selected.
        """
        self.confirmButton.setEnabled(selectedCount == 3)
        if selectedCount == 3:
            selectedCardObjs = [tup[1] for tup in self.controller.selectedCards]
            for i, handCard in enumerate(self.controller.handCards):
                isEnabled = (handCard in selectedCardObjs)
                self.updateCardState(i, isEnabled)
                
        else:
            self.setPlayerHandEnabled(True)
                
    def updatePlaceButton(self, isEnabled, text):
        if text == "Waiting for other players...":
            self.confirmButton.setEnabled(isEnabled)
            self.confirmButton.setText(text)
        else:
            self.placeButton.setEnabled(isEnabled)
            self.placeButton.setText(text)
    
    def updateDeck(self, deck):
        self.deckLabel.setText(f"Draw Deck:\n\n{len(deck)} cards remaining")
    
    def updatePile(self, pile):
        """
        Update the pile view with the top card.
        """
        if pile:
            topCard = pile[-1]
            pixmap = QPixmap(fr"palaceData\cards\{topCard[0].lower()}_of_{topCard[1].lower()}.png").scaled(
                CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.pileLabel.setPixmap(pixmap)
        else:
            self.pileLabel.setText("Pile:\nEmpty")
    
    def updatePileLabel(self, text):
        self.pileLabel.setText(text)
    
    def updateCurrentPlayer(self, currentPlayer):
        """
        Update the UI for the current player.
        """
        currentPlayerNickname = self.controller.playerNicknames.get(f"{self.controller.currentPlayer}", f"Player {self.controller.currentPlayer}")
        if not self.controller.topCardSelectionPhase:
            self.currentPlayerLabel.setText(f"Current Player: {currentPlayerNickname}")
        isCurrentPlayer = currentPlayer == self.playerIndex
        self.setPlayerHandEnabled(isCurrentPlayer)
        if not isCurrentPlayer:
            self.placeButton.setEnabled(isCurrentPlayer)
        if self.controller.pile and isCurrentPlayer:
            self.pickUpPileButton.setEnabled(isCurrentPlayer)
        else:
            self.pickUpPileButton.setEnabled(False)
        if isCurrentPlayer:
            self.controller.updatePlayableCards()
            self.placeButton.setText("Select A Card")
        else:
            self.placeButton.setText(f"Player {currentPlayerNickname}'s Turn...")
    
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
        self.updatePlaceButton(False, f"Player {self.controller.currentPlayer}'s Turn...")
        self.deckLabel.show()
        self.deckLabel.setText(f"Draw Deck:\n\n{len(self.controller.deck)} cards remaining")
        self.pickUpPileButton.show()
        self.pileLabel.setText("Pile:\nEmpty")
        self.pileLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pileLabel.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT + 4)
        self.pileLabel.setStyleSheet("border: 2px dashed gray; background-color: transparent;")
        self.currentPlayerLabel.setText(f"Current Player: {self.controller.currentPlayer}")
        self.updateCurrentPlayer(self.controller.currentPlayer)
            
    def gameOver(self, winner):
        self.placeButton.setDisabled(True)
        self.pickUpPileButton.setDisabled(True)
        self.currentPlayerLabel.setText(f"Player {winner} is Winner!!!")
    
    @Slot()
    def returnToMainMenu(self):
        # Close the current game view and return to the main menu
        self.hide()
        self.mainMenu.show()
    
    def closeEvent(self, event):
        """
        Override the closeEvent to ensure proper disconnection behavior.
        """
        if self.controller.playerIndex == 1 or self.controller.numPlayers == 2:
            reply = QMessageBox.question(
                self,
                'Quit Confirmation',
                'Are you sure you want to quit the game?\nAll players will be disconnected.',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
        else:
            reply = QMessageBox.question(
                self,
                'Quit Confirmation',
                'Are you sure you want to quit the game?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

        if reply == QMessageBox.StandardButton.Yes:
            self.controller.disconnect()
            event.accept()
        else:
            event.ignore()
    
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
    updatePileLabelSignal = Signal(str)
    updateDeckSignal = Signal(list)
    gameWonSignal = Signal(int)
    gameOverSignal = Signal(int)
    hostDisconnectedSignal = Signal()
    playerDisconnectedSignal = Signal()
    
    topCardSelectionPhase = True

    def __init__(self, deck, playerIndex, handCards, bottomCards, numPlayers, broadcastUpdate, playerNicknames):
        super().__init__()
        self.deck = deck
        self.playerIndex = playerIndex
        self.numPlayers = numPlayers
        self.selectedCards = []
        self.sevenSwitch = False
        self.pile = []
        self.playerNicknames = playerNicknames
        self.handCards = handCards
        self.topCards = []
        self.clockwise = None
        self.bottomCards = bottomCards 
        self.broadcastUpdate = broadcastUpdate
        self.topCardConfirms = 0
        self.currentPlayer = None
        self.gameWon = False
        
        self.allPlayerCards = {
            self.playerIndex: {
                'handCards': self.handCards,
                'topCards': self.topCards,
                'bottomCards': self.bottomCards,
            }
        }

    def startGame(self):
        self.updatePlayerHandSignal.emit(self.handCards)
    
    def updatePlayableCards(self):
        for i, card in enumerate(self.handCards):
            isPlayable = self.isCardPlayable(card) or card[3]
            self.updateCardStateSignal.emit(i, isPlayable)
    
    def isCardPlayable(self, card):
        topCard = self.pile[-1] if self.pile else None
        if self.sevenSwitch:
            return VALUES[card[0]] <= 7 or card[0] in ['2', '10']
        if not topCard:
            return True 
        if card[3]:
            return True
        return card[0] == '2' or card[0] == '10' or VALUES[card[0]] >= VALUES[topCard[0]]
    
    def prepareCardPlacement(self, cardIndex, cardLabel):
        card = self.handCards[cardIndex]
        if self.topCardSelectionPhase:
            if (cardIndex, card) in self.selectedCards:
                self.selectedCards.remove((cardIndex, card))
                cardLabel.setStyleSheet("border: 2px solid transparent; background-color: transparent;")
            elif len(self.selectedCards) < 3:
                self.selectedCards.append((cardIndex, card))
                cardLabel.setStyleSheet("border: 2px solid blue; background-color: transparent;")

            self.selectedCardsChanged.emit(len(self.selectedCards))
        else:
            if (card, cardLabel) in self.selectedCards:
                self.selectedCards.remove((card, cardLabel))
                cardLabel.setStyleSheet("border: 0px solid black; background-color: transparent;")
            else:
                if card[3] or self.isCardPlayable(card):
                    self.selectedCards.append((card, cardLabel))
                    cardLabel.setStyleSheet("border: 2px solid blue; background-color: transparent;")
                    
            selectedCardRank = card[0]
            for i, handCard in enumerate(self.handCards):
                isEnabled = (
                    not self.selectedCards or (handCard[0] == selectedCardRank and (not handCard[3] or handCard == card))
                )
                self.updateCardStateSignal.emit(i, isEnabled)
            if self.selectedCards:
                self.placeButtonStateChanged.emit(True, "Place")
            else:
                self.placeButtonStateChanged.emit(False, "Select A Card")
                self.updatePlayableCards()

    def checkFourOfAKind(self):
        if len(self.pile) < 4:
            return False
        return len(set(card[0] for card in self.pile[-4:])) == 1
    
    def placeCard(self):
        playedCards = []
        pickUpFlag = False
        # Add selected cards to the pile
        for card, label in self.selectedCards:
            popped = self.handCards.pop(self.handCards.index(card))
            if popped[2]:
                popped = [card[0], card[1], False, False]
                self.pile.append(popped)
            elif card[3]:
                popped = [card[0], card[1], card[2], False]
                self.pile.append(popped)
                if not self.sevenSwitch:
                    if len(self.pile) >= 2 and self.pile[-1][0] not in {"2", "10"} and self.pile[-2][0] >= self.pile[-1][0]:
                        pickUpFlag = True
                        continue
                else:
                    if len(self.pile) >= 2 and self.pile[-1][0] not in {"2", "10"} and self.pile[-2][0] <= self.pile[-1][0]:
                        pickUpFlag = True
                        continue
            else:
                self.pile.append(popped)
            playedCards.append(popped)
        
        # Clear selected cards
        self.selectedCards.clear()

        # Update the pile view
        self.updatePileSignal.emit(self.pile)
        self.broadcastUpdate('updatePile', {'pile': self.pile})

        if pickUpFlag:
            QTimer.singleShot(1250, self.pickUpPile)
            return
        
        # Draw a card if hand has fewer than 3 cards
        while len(self.handCards) < 3 and self.deck:
            newCard = self.deck.pop(0)
            self.handCards.append(newCard)
            
        self.updatePlayerHandSignal.emit(self.handCards)
        self.updateDeckSignal.emit(self.deck)
        self.broadcastUpdate('updateDeck', {'deck': self.deck})

        if self.checkFourOfAKind():
            print("Four of a kind! Clearing the pile.\n")
            self.pile.clear()
            self.updatePileSignal.emit(self.pile)
            self.broadcastUpdate('updatePile', {'pile': self.pile})
            self.updatePileLabelSignal.emit("Pile:\nBombed!!!")
            self.broadcastUpdate('updatePileLabel', {'pileLabel': "Pile:\nBombed!!!"})
            self.sevenSwitch = False
            self.broadcastUpdate('sevenSwitch', {'sevenSwitch': False})
            self.checkGameState()
            self.broadcastCards()
            if self.gameWon:
                QTimer.singleShot(1250, self.gameOver)
            return
        
        if '2' in [card[0] for card in playedCards]:
            self.sevenSwitch = False
            self.placeButtonStateChanged.emit(False, 'Select a Card')
            self.broadcastUpdate('sevenSwitch', {'sevenSwitch': False})
            self.checkGameState()
            self.broadcastCards()
            if self.gameWon:
                QTimer.singleShot(1250, self.gameOver)
            return
        elif '10' in [card[0] for card in playedCards]:
            self.pile.clear()
            self.updatePileSignal.emit(self.pile)
            self.broadcastUpdate('updatePile', {'pile': self.pile})
            self.updatePileLabelSignal.emit("Pile:\nBombed!!!")
            self.broadcastUpdate('updatePileLabel', {'pileLabel': "Pile:\nBombed!!!"})
            self.sevenSwitch = False
            self.placeButtonStateChanged.emit(False, 'Select a Card')
            self.broadcastUpdate('sevenSwitch', {'sevenSwitch': False})
            self.checkGameState()
            self.broadcastCards()
            if self.gameWon:
                QTimer.singleShot(1250, self.gameOver)
            return
        if '7' in [card[0] for card in playedCards]:
            self.broadcastUpdate('sevenSwitch', {'sevenSwitch': True})
        else:
            self.broadcastUpdate('sevenSwitch', {'sevenSwitch': False})
        self.checkGameState()
        self.broadcastCards()
        if self.gameWon:
            QTimer.singleShot(1250, self.gameOver)
            return
        self.rotateTurn()
    
    def pickUpPile(self):
        topFlag = False
        bottomFlag = False
        self.handCards.extend(self.pile)
        self.updatePlayerHandSignal.emit(self.handCards)
        self.pile.clear()
        print(f"Player {self.playerIndex} picks up the pile\n")
        topCardsIndices = [index for index, card in enumerate(self.handCards) if card[2]]
        bottomCardsIndices = [index for index, card in enumerate(self.handCards) if card[3]]
        topFlag = any(card[2] for card in self.handCards)
        bottomFlag = any(card[3] for card in self.handCards)
        if topFlag:
            self.topCards = [self.handCards[index] for index in topCardsIndices]
            for index in sorted(topCardsIndices, reverse=True):
                self.handCards.pop(index)
            self.updateTopCardsSignal.emit(self.topCards)
            self.updatePlayerHandSignal.emit(self.handCards)
            print(self.topCards)
            print(self.handCards)
        elif bottomFlag:
            self.bottomCards = [self.handCards[index] for index in bottomCardsIndices]
            for index in sorted(bottomCardsIndices, reverse=True):
                self.handCards.pop(index)
            self.updateBottomCardsSignal.emit(self.bottomCards)
            self.updatePlayerHandSignal.emit(self.handCards)
            print(self.bottomCards)
            print(self.handCards)
        self.updatePileSignal.emit(self.pile)
        self.broadcastUpdate('sevenSwitch', {'sevenSwitch': False})
        self.broadcastUpdate('updatePile', {'pile': self.pile})
        self.broadcastCards()
        self.rotateTurn()
    
    def rotateTurn(self):
        """
        Handle turn rotation logic based on the number of players.
        """
        if self.clockwise:
            self.currentPlayer = (self.currentPlayer % self.numPlayers) + 1
        else:
            self.currentPlayer = (self.currentPlayer - 2) % self.numPlayers + 1
        self.currentPlayerChangedSignal.emit(self.currentPlayer)
        self.broadcastUpdate('updateCurrentPlayer', {'currentPlayer': self.currentPlayer})
    
    def confirmTopCards(self):
        # Move selected cards to top cards
        for index, card in self.selectedCards:
            card = [card[0], card[1], True, False]
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
        self.placeButtonStateChanged.emit(False, "Waiting for other players...")
        if self.playerIndex == 1:
            self.checkAllPlayersConfirmed()
    
    def checkAllPlayersConfirmed(self):        
        if self.topCardConfirms == self.numPlayers:
            lowestPlayer, secondLowestPlayer, rankTotals = self.calculateRankTotals()
            print(f"Rank totals for top cards: {rankTotals}")
            print(f"Player {lowestPlayer} has the lowest rank total.")
            print(f"Player {secondLowestPlayer} has the second lowest rank total.")
            
            if secondLowestPlayer:
                next_player = lowestPlayer % self.numPlayers + 1
                self.clockwise = (secondLowestPlayer == next_player)
            else:
                self.clockwise = True
            if self.playerIndex == 1:
                self.startMainGame(lowestPlayer)
            self.broadcastUpdate('startMainGame', {"lowestPlayer": lowestPlayer, "direction": self.clockwise})
    
    def checkGameState(self):
        if not self.handCards and not self.deck:
            if self.topCards:
                self.handCards = self.topCards
                self.topCards = []
            elif self.bottomCards:
                self.handCards = self.bottomCards
                self.bottomCards = []
            elif not self.bottomCards:
                self.handCards = []
                self.gameWon = True
        self.updatePlayerHandSignal.emit(self.handCards)
        self.updateTopCardsSignal.emit(self.topCards)
        self.updateBottomCardsSignal.emit(self.bottomCards)
    
    def gameOver(self):
        currentPlayerNickname = self.playerNicknames.get(f"{self.currentPlayer}", self.currentPlayer)
        self.gameWonSignal.emit(currentPlayerNickname)
        if self.playerIndex == 1:
            self.gameOverSignal.emit(currentPlayerNickname)
            self.broadcastUpdate('gameEnd', {'winner': currentPlayerNickname})
        else:
            self.broadcastUpdate('gameOver', {'winner': currentPlayerNickname})
    
    def disconnect(self):
        if self.playerIndex == 1:
            self.broadcastUpdate('gameClose', {})
            self.hostDisconnectedSignal.emit()
            self.playerDisconnectedSignal.emit()
            return
        self.broadcastUpdate('playerDisconnected', {'playerIndex': self.playerIndex})
        self.playerDisconnectedSignal.emit()
        
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
        if playerIndex != self.playerIndex:  
            self.updateOtherPlayerCardsSignal.emit(playerIndex, handCards, topCards, bottomCards)
    
    def calculateRankTotals(self):
        rankTotals = {}
        for playerIndex, cards in self.allPlayerCards.items():
            topCards = cards.get('topCards', [])
            total = sum(RANKS[card[0]] for card in topCards)
            rankTotals[playerIndex] = total
        
        lowestPlayer = min(rankTotals, key=rankTotals.get)

        # Find the second lowest adjacent player
        if self.numPlayers > 2:
            adjacentPlayers = [
                ((lowestPlayer - 2) % self.numPlayers) + 1,  # Left adjacent player
                (lowestPlayer % self.numPlayers) + 1         # Right adjacent player
            ]
            adjacentTotals = {p: rankTotals.get(p, float('inf')) for p in adjacentPlayers}
            secondLowestPlayer = min(adjacentTotals, key=adjacentTotals.get)
        else:
            secondLowestPlayer = None  # No second lowest for 2 players

        return lowestPlayer, secondLowestPlayer, rankTotals

    def startMainGame(self, lowestPlayer):
        """
        Transition to the main game phase, calculate rank totals, and identify the player with the highest rank.
        """
        self.currentPlayer = lowestPlayer
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
