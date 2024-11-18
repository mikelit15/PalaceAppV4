import sys
import random
import json
import socket
import threading
import struct
import time
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QLabel, QDialog, QGridLayout, QRadioButton, QButtonGroup, QSpacerItem, QSizePolicy, \
    QTextEdit, QLineEdit
from PySide6.QtGui import QPixmap, QIcon, QTransform
from PySide6.QtCore import Qt, QCoreApplication, QTimer, Signal, QObject
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

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
VALUES = {'2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10, 'J': 11, 'Q': 12, 'K': 13, 'A': 14}
CARD_WIDTH = 56
CARD_HEIGHT = 84
BUTTON_WIDTH = 66
BUTTON_HEIGHT = 87

class SignalCommunicator(QObject):
    updateOpponentBottomCardsSignal = Signal(int, list)
    updateOpponentTopCardsSignal = Signal(int, list)
    updateOpponentHandSignal = Signal(int, list)
    updateDeckSignal = Signal(dict)
    startGameSignal = Signal()
    proceedWithGameSetupSignal = Signal()
    updateUISignal = Signal()
    resetGameSignal = Signal()
    setupGameSignal = Signal()
    logTextSignal = Signal(str)
    playerCountLabelSignal = Signal(str)
    startButtonEnabledSignal = Signal(bool)
    playerConnectedSignal = Signal(str)
    playerDisconnectedSignal = Signal(str)
    connectionStatusSignal = Signal(str)
    disconnectSignal = Signal() 

def centerDialog(dialog, parent, name):
    offset = 0
    if name == "playerSelectionDialog":
        offset = 100
    elif name == "rulesDialog":
        offset = 225
    parentGeometery = parent.geometry()
    parentCenterX = parentGeometery.center().x()
    parentCenterY = parentGeometery.center().y()
    dialogGeometery = dialog.geometry()
    dialogCenterX = dialogGeometery.width() // 2
    dialogCenterY = dialogGeometery.height() // 2
    newX = parentCenterX - dialogCenterX
    newY = parentCenterY - dialogCenterY - offset
    dialog.move(newX, newY)

class HostLobby(QDialog):
    def __init__(self, parent=None, mainWindow=None):
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.setWindowTitle("Host Lobby")
        self.setGeometry(0, 0, 300, 200)
        self.serverSocket = None
        self.clientSockets = []
        self.clientAddresses = {}
        self.clientNicknames = {}
        self.serverThread = None
        self.running = False
        self.playerCount = 1  # Starting with host player
        self.communicator = mainWindow.communicator  # Get the communicator from mainWindow
        self.initUI()
        centerDialog(self, self, "GameView")

    def initUI(self):
        layout = QVBoxLayout()

        self.infoLabel = QLabel("Hosting Lobby...\nWaiting for players to join.")
        layout.addWidget(self.infoLabel)

        self.logText = QTextEdit()
        self.logText.setReadOnly(True)
        layout.addWidget(self.logText)

        self.playerCountLabel = QLabel("Players: 1/2")
        layout.addWidget(self.playerCountLabel)

        self.startButton = QPushButton("Start Game")
        self.startButton.setEnabled(False)
        self.startButton.clicked.connect(self.startGame)
        layout.addWidget(self.startButton)

        backButton = QPushButton("Back")
        backButton.clicked.connect(self.backToOnlineDialog)
        layout.addWidget(backButton)

        self.setLayout(layout)
        self.startServer()

    def showEvent(self, event):
        centerDialog(self, self.mainWindow, "Host Lobby")

    def startServer(self):
        try:
            self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            host_ip = socket.gethostbyname(socket.gethostname())
            self.serverSocket.bind((host_ip, 12345))
            self.logText.append(f"Server started on {host_ip}, port: 12345")
            self.serverSocket.listen(5)
            self.communicator.logTextSignal.emit(f"Server started on {host_ip}:12345")
            self.communicator.logTextSignal.emit("Host Connected")
            self.running = True
            self.serverThread = threading.Thread(target=self.acceptConnections, daemon=True)
            self.serverThread.start()
        except OSError as e:
            if e.errno == 10048:
                self.communicator.logTextSignal.emit("Server is already running")
            else:
                self.communicator.logTextSignal.emit(f"Failed to start server: {e}")

    def acceptConnections(self):
        while self.running:
            try:
                clientSocket, clientAddress = self.serverSocket.accept()
                if len(self.clientSockets) >= 2:
                    clientSocket.send(b'lobby full')
                    self.logText.append(f"Connection attempt from {clientAddress}")
                    clientSocket.close()
                else:
                    self.clientSockets.append(clientSocket)
                    self.clientAddresses[clientSocket] = clientAddress
                    threading.Thread(target=self.handleClient, args=(clientSocket,), daemon=True).start()
                    threading.Thread(target=self.listenForDisconnection, args=(clientSocket,), daemon=True).start()
            except Exception as e:
                if self.running:  # Only log if the server is supposed to be running
                    self.logText.append(f"Error accepting connections: {e}")

    def handleClient(self, clientSocket):
        try:
            data = clientSocket.recv(1024).decode('utf-8')
            if data == "Player":
                data = f"Player {self.playerCount + 1}"
            nickname = data
            self.clientNicknames[clientSocket] = nickname
            self.playerCount += 1
            logMessage = f"{nickname} connected from {self.clientAddresses[clientSocket]}"
            self.communicator.playerConnectedSignal.emit(logMessage)
            self.sendLogToClients(logMessage)  # Send log message to all clients
            self.communicator.playerCountLabelSignal.emit(f"Players: {self.playerCount}/2")
            if self.playerCount > 2:
                self.communicator.startButtonEnabledSignal.emit(True)
        except Exception as e:
            self.communicator.logTextSignal.emit(f"Error handling client: {e}")

    def sendLogToClients(self, message):
        for clientSocket in self.clientSockets:
            try:
                clientSocket.sendall(f"log: {message}".encode('utf-8'))
            except Exception as e:
                self.communicator.logTextSignal.emit(f"Failed to send log to client: {e}")

    def listenForDisconnection(self, clientSocket):
        try:
            while self.running:
                data = clientSocket.recv(1024).decode('utf-8')
                if data == 'leave':
                    self.removeClient(clientSocket)
                    break
        except Exception as e:
            self.removeClient(clientSocket)

    def removeClient(self, clientSocket):
        nickname = self.clientNicknames.pop(clientSocket, "Unknown")
        if clientSocket in self.clientSockets:
            self.clientSockets.remove(clientSocket)
            self.clientAddresses.pop(clientSocket, None)
            self.playerCount -= 1
            message = f"{nickname} has left the server."
            self.communicator.playerDisconnectedSignal.emit(message)
            self.sendLogToClients(message)  # Send the disconnection message to all clients
            self.communicator.playerCountLabelSignal.emit(f"Players: {self.playerCount}/2")
            clientSocket.close()
            if self.playerCount <= 1:
                self.communicator.startButtonEnabledSignal.emit(False)

    def startGame(self):
        self.logText.append("Starting game...")
        self.notifyClientsToStart()
        self.accept()  # Close the lobby window
        self.mainWindow.startHost()

    def notifyClientsToStart(self):
        for clientSocket in self.clientSockets:
            try:
                clientSocket.sendall(b'start')
            except Exception as e:
                self.logText.append(f"Failed to notify client: {e}")

    def backToOnlineDialog(self):
        self.running = False
        if self.serverSocket:
            self.serverSocket.close()
        for clientSocket in self.clientSockets:
            clientSocket.close()
        self.accept()
        self.mainWindow.playOnline()

    def cleanup(self):
        self.running = False
        if self.serverSocket:
            self.serverSocket.close()
        for clientSocket in self.clientSockets:
            clientSocket.close()
        self.clientSockets = []
        self.clientAddresses = {}
        self.clientNicknames = {}
        self.playerCount = 1

    def closeEvent(self, event):
        self.cleanup()
        event.accept()

class JoinLobby(QDialog):
    connectionEstablished = Signal()
    startSignalReceived = Signal()
    lobbyFullSignal = Signal()

    def __init__(self, parent=None, mainWindow=None):
        super().__init__(parent)
        self.mainWindow = mainWindow
        self.setWindowTitle("Join Lobby")
        self.setGeometry(0, 0, 300, 200)  # Default position, will be centered later
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        self.clientSocket = None
        self.communicator = mainWindow.communicator  # Get the communicator from mainWindow
        self.initUI()

        # Connect signals to slots
        self.connectionEstablished.connect(self.onConnectionEstablished)
        self.startSignalReceived.connect(self.onStartSignalReceived)
        self.lobbyFullSignal.connect(self.onLobbyFull)

        centerDialog(self, self, "GameView")

    def initUI(self):
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
        self.backButton.clicked.connect(self.backToOnlineDialog)
        layout.addWidget(self.backButton)

        self.leaveButton = QPushButton("Leave Server")
        self.leaveButton.setStyleSheet("background-color: red; color: white;")
        self.leaveButton.clicked.connect(self.leaveServer)
        self.leaveButton.setVisible(False)
        layout.addWidget(self.leaveButton)

        self.setLayout(layout)

    def showEvent(self, event):
        centerDialog(self, self.mainWindow, "JoinLobby")

    def joinLobby(self):
        hostAddress = self.addressInput.text()
        nickname = self.nicknameInput.text() or "Player"
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.clientSocket.connect((hostAddress, 12345))
            self.clientSocket.sendall(nickname.encode('utf-8'))
            self.connectionEstablished.emit()
            threading.Thread(target=self.listenForStartSignal, daemon=True).start()
            self.backButton.setVisible(False)
            self.leaveButton.setVisible(True)
            self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, False)
            self.show()
        except OSError as e:
            if e.errno == 10049:
                self.communicator.connectionStatusSignal.emit("Server does not exist.")
            elif e.errno == 10061:
                self.communicator.connectionStatusSignal.emit("Server is not running.")
            else:
                self.communicator.connectionStatusSignal.emit(f"Failed to connect: {e}")

    def listenForStartSignal(self):
        try:
            while True:
                self.joinButton.setDisabled(True)
                data = self.clientSocket.recv(1024).decode('utf-8')
                if data == 'start':
                    self.startSignalReceived.emit()
                    break
                elif data == 'lobby full':
                    self.lobbyFullSignal.emit()
                    break
                elif data.startswith('log:'):
                    logMessage = data[4:].strip()
                    self.communicator.logTextSignal.emit(logMessage)
        except ConnectionResetError:
            self.communicator.connectionStatusSignal.emit("Connection was closed by the server.")
            self.leaveButton.setVisible(False)
            self.backButton.setVisible(True)
            self.joinButton.setDisabled(False)
        except Exception as e:
            self.communicator.connectionStatusSignal.emit(f"Error in listenForStartSignal: {e}")

    def onConnectionEstablished(self):
        self.communicator.connectionStatusSignal.emit(f"Connected to lobby")

    def onStartSignalReceived(self):
        self.accept()
        self.mainWindow.startClient()

    def onLobbyFull(self):
        self.communicator.connectionStatusSignal.emit("Lobby is full. Unable to join.\n")
        self.leaveButton.setVisible(False)
        self.backButton.setVisible(True)
        self.joinButton.setDisabled(False)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        self.show()

    def leaveServer(self):
        if self.clientSocket:
            self.clientSocket.sendall(b'leave')
            self.clientSocket.close()
        self.clientSocket = None
        self.leaveButton.setVisible(False)
        self.communicator.connectionStatusSignal.emit("Disconnected from server.")
        self.addressInput.setEnabled(True)
        self.nicknameInput.setEnabled(True)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        self.show()
        self.mainWindow.joinLobby(self)
        self.accept()

    def backToOnlineDialog(self):
        if self.clientSocket:
            try:
                self.clientSocket.sendall(b'leave')
            except (ConnectionResetError, BrokenPipeError):
                pass
            self.clientSocket.close()
        self.accept()
        self.mainWindow.playOnline()

    def cleanup(self):
        if self.clientSocket:
            try:
                self.clientSocket.sendall(b'leave')
            except Exception:
                pass
            self.clientSocket.close()

    def closeEvent(self, event):
        self.cleanup()
        event.accept()

class Server:
    def __init__(self, host, port, communicator):
        self.host = host
        self.port = port
        self.communicator = communicator
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind((self.host, self.port))
        self.serverSocket.listen(1)
        self.controller = None 
        self.communicator.logTextSignal.emit(f"Server listening on {self.host}:{self.port}\n")
        self.clientSocket, self.clientAddress = self.serverSocket.accept()
        self.communicator.logTextSignal.emit(f"Connection from {self.clientAddress}\n")

        # Start a thread to handle client communication
        threading.Thread(target=self.handleClient).start()

    def handleClient(self):
        try:
            while True:
                data = self.receiveData(self.clientSocket)
                if data:
                    self.processClientData(data)
                else:
                    self.communicator.logTextSignal.emit("Client disconnected.")
                    self.handleClientDisconnection()
                    break
        except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
            self.communicator.logTextSignal.emit(f"Connection error: {e}\n")
            self.handleClientDisconnection()
        except Exception as e:
            self.communicator.logTextSignal.emit(f"Unexpected error: {e}\n")
            self.handleClientDisconnection()
        if self.clientSocket:
            self.clientSocket.close()

    def handleClientDisconnection(self):
        self.clientSocket.close()
        self.clientSocket = None
        self.communicator.connectionStatusSignal.emit("Client disconnected.")
        self.communicator.playerDisconnectedSignal.emit("Client has left the server.")
    
    def disconnect(self):
        self.communicator.logTextSignal.emit("Disconnected from client.")
        self.communicator.disconnectSignal.emit() 
        if self.clientSocket:
            try:
                self.clientSocket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            self.clientSocket.close()
            self.clientSocket = None
        if self.serverSocket:
            self.serverSocket.close()

    def sendDisconnectSignalToClient(self):
        if self.clientSocket:
            try:
                data = json.dumps({'action': 'disconnect'}).encode('utf-8')
                self.clientSocket.sendall(struct.pack('>I', len(data)) + data)
            except Exception as e:
                self.communicator.logTextSignal.emit(f"Failed to send disconnect signal to client: {e}")
    
    def processClientData(self, data):
        if data is None:
            return
        if data['action'] == 'confirmTopCards':
            playerIndex = int(data['playerIndex'])
            self.communicator.updateOpponentBottomCardsSignal.emit(playerIndex, data['bottomCards'])
            self.communicator.updateOpponentTopCardsSignal.emit(playerIndex, data['topCards'])
            self.communicator.updateOpponentHandSignal.emit(playerIndex, data['hand'])
            self.controller.checkBothPlayersConfirmed()
        elif data['action'] == 'startGame':
            self.controller.proceedWithGameSetup()
        elif data['action'] == 'playCard':
            self.controller.receiveGameState(data)
        elif data['action'] == 'playAgainRequest':
            self.controller.playAgainCount = data['count']
            self.controller.handlePlayAgain()
        elif data['action'] == 'resetGame':
            self.controller.resetGame()
        elif data['action'] == 'gameOver':
            self.controller.gameOverSignal.emit(data['winner'])
        elif data['action'] == 'disconnect':
            self.controller.disconnectSignal.emit()

    def sendToClient(self, data):
        if self.clientSocket:
            try:
                serializedData = json.dumps(data).encode('utf-8')
                msgLen = struct.pack('>I', len(serializedData))
                print(f"Sending data to client: {data}\n")
                self.clientSocket.sendall(msgLen + serializedData)
            except Exception as e:
                print(f"Error sending data to client: {e}\n")
        else:
            print("Client socket is not connected\n")

    def receiveData(self, sock):
        rawMsgLen = self.recvall(sock, 4)
        if not rawMsgLen:
            return None
        msglen = struct.unpack('>I', rawMsgLen)[0]
        message = self.recvall(sock, msglen)
        if message is None:
            return None
        data = json.loads(message)
        print(f"Received data: {data}\n")
        return data

    def recvall(self, sock, n):
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def close(self):
        if self.clientSocket:
            try:
                self.clientSocket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            self.clientSocket.close()
        if self.serverSocket:
            self.serverSocket.close()

class Client:
    def __init__(self, host, port, communicator):
        self.host = host
        self.port = port
        self.communicator = communicator
        self.clientSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.controller = None 
        try:
            self.clientSocket.connect((self.host, self.port))
            self.communicator.logTextSignal.emit("Connected to the server\n")
            threading.Thread(target=self.handleServer).start()
        except Exception as e:
            self.communicator.logTextSignal.emit(f"Failed to connect to the server: {e}\n")
            self.clientSocket = None  

    def handleServer(self):
        try:
            while self.clientSocket:
                data = self.receiveData(self.clientSocket)
                if data:
                    if data.get('action') == 'disconnect':
                        self.communicator.connectionStatusSignal.emit("Server disconnected.")
                        self.disconnect()
                        break
                    self.processServerData(data)
                else:
                    self.communicator.connectionStatusSignal.emit("Server disconnected.")
                    self.disconnect()
                    break
        except (ConnectionResetError, ConnectionAbortedError, OSError) as e:
            self.communicator.connectionStatusSignal.emit(f"Connection error: {e}\n")
            self.disconnect()
        except Exception as e:
            self.communicator.connectionStatusSignal.emit(f"Unexpected error: {e}\n")
            self.disconnect()
        if self.clientSocket:
            self.clientSocket.close()

    def disconnect(self):
        if self.clientSocket:
            try:
                self.clientSocket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            self.clientSocket.close()
            self.clientSocket = None
        self.communicator.connectionStatusSignal.emit("Disconnected from server.")
        self.communicator.disconnectSignal.emit()
    
    def processServerData(self, data):
        if data is None:
            self.communicator.logTextSignal.emit("Received None data from server\n")
            return
        if data['action'] == 'confirmTopCards':
            playerIndex = int(data['playerIndex'])
            self.communicator.updateOpponentBottomCardsSignal.emit(playerIndex, data['bottomCards'])
            self.communicator.updateOpponentTopCardsSignal.emit(playerIndex, data['topCards'])
            self.communicator.updateOpponentHandSignal.emit(playerIndex, data['hand'])
            self.controller.checkBothPlayersConfirmed()
        elif data['action'] == 'deckSync':
            self.communicator.updateDeckSignal.emit(data)
        elif data['action'] == 'startGame':
            self.controller.proceedWithGameSetup()
        elif data['action'] == 'playCard':
            self.controller.receiveGameState(data)
        elif data['action'] == 'playAgainRequest':
            self.controller.playAgainCount = data['count']
            self.controller.handlePlayAgain()
        elif data['action'] == 'resetGame':
            self.controller.resetGame()
        elif data['action'] == 'gameOver':
            self.controller.gameOverSignal.emit(data['winner'])
        elif data['action'] == 'disconnect':
            self.controller.disconnectSignal.emit()

    def sendToServer(self, data):
        if self.clientSocket:
            try:
                serializedData = json.dumps(data).encode('utf-8')
                msgLen = struct.pack('>I', len(serializedData))
                print(f"Sending data to server: {data}\n")
                self.clientSocket.sendall(msgLen + serializedData)
            except Exception as e:
                print(f"Error sending data to server: {e}\n")
        else:
            print("Client socket is not connected\n")

    def receiveData(self, sock):
        rawMsgLen = self.recvall(sock, 4)
        if not rawMsgLen:
            return None
        msglen = struct.unpack('>I', rawMsgLen)[0]
        message = self.recvall(sock, msglen)
        if message is None:
            return None
        data = json.loads(message)
        print(f"Received data: {data}\n")
        return data

    def recvall(self, sock, n):
        data = b''
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data += packet
        return data

    def close(self):
        if self.clientSocket:
            try:
                self.clientSocket.shutdown(socket.SHUT_RDWR)
            except Exception:
                pass
            self.clientSocket.close()
            self.clientSocket = None

class GameOverDialog(QDialog):
    playAgainSignal = Signal()
    mainMenuSignal = Signal()
    exitSignal = Signal()

    def __init__(self, winnerName, parentCoords):
        super().__init__()
        self.setWindowTitle("Game Over")
        self.setWindowIcon(QIcon(r"_internal\palaceData\palace.ico"))
        self.setGeometry(805, 350, 300, 200)
        layout = QVBoxLayout()
        label = QLabel(f"Game Over! {winnerName} wins!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        buttonBox = QHBoxLayout()
        playAgainButton = QPushButton("Play Again")
        playAgainButton.clicked.connect(self.playAgain)
        mainMenuButton = QPushButton("Main Menu")
        mainMenuButton.clicked.connect(self.mainMenu)
        exitButton = QPushButton("Exit")
        exitButton.clicked.connect(self.exitGame)
        buttonBox.addWidget(playAgainButton)
        buttonBox.addWidget(mainMenuButton)
        buttonBox.addWidget(exitButton)
        layout.addLayout(buttonBox)
        
        self.setLayout(layout)
       
        centerDialog(self, parentCoords, "GameView")
    
    def playAgain(self):
        self.playAgainSignal.emit()
        self.accept()

    def mainMenu(self):
        self.mainMenuSignal.emit()
        self.accept()

    def exitGame(self):
        self.exitSignal.emit()
        QCoreApplication.instance().quit()

class HomeScreen(QWidget):
    def __init__(self, communicator):
        super().__init__()
        self.communicator = communicator
        self.controller = None
        self.initUI()
        self.communicator.logTextSignal.connect(self.updateLogText)
        self.communicator.playerCountLabelSignal.connect(self.updatePlayerCountLabel)
        self.communicator.startButtonEnabledSignal.connect(self.setStartButtonEnabled)
        self.communicator.playerConnectedSignal.connect(self.updateLogText)
        self.communicator.playerDisconnectedSignal.connect(self.updateLogText)
        self.communicator.connectionStatusSignal.connect(self.updateLogText)

    def initUI(self):
        self.setWindowTitle('Palace')
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
        playButton.clicked.connect(self.showPlayerSelectionDialog)
        buttonLayout.addWidget(playButton)

        buttonLayout.addWidget(QLabel(""))

        onlineButton = QPushButton("Online")
        onlineButton.clicked.connect(self.playOnline)
        onlineButton.setFixedWidth(225)
        buttonLayout.addWidget(onlineButton, alignment=Qt.AlignmentFlag.AlignCenter)

        buttonLayout.addWidget(QLabel(""))
        
        rulesButton = QPushButton("Rules")
        rulesButton.clicked.connect(self.showRules)
        rulesButton.setFixedWidth(225)
        buttonLayout.addWidget(rulesButton, alignment=Qt.AlignmentFlag.AlignCenter)

        buttonLayout.addWidget(QLabel(""))

        exitButton = QPushButton("Exit")
        exitButton.clicked.connect(QCoreApplication.instance().quit)
        exitButton.setFixedWidth(225)
        buttonLayout.addWidget(exitButton, alignment=Qt.AlignmentFlag.AlignCenter)

        buttonLayout.addWidget(QLabel(""))

        buttonContainer = QWidget()
        buttonContainer.setLayout(buttonLayout)
        layout.addWidget(buttonContainer, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(layout)
    
    def returnToMainMenu(self):
        self.show()
        if self.controller:
            self.controller.view.close()
    
    def showPlayerSelectionDialog(self):
        self.playerSelectionDialog = QDialog(self)
        self.playerSelectionDialog.setWindowTitle("Select Number of Players")
        self.playerSelectionDialog.setGeometry(805, 350, 300, 200)

        layout = QVBoxLayout()

        label = QLabel("How many players?")
        layout.addWidget(label)

        self.radioGroup = QButtonGroup(self.playerSelectionDialog)
        radioButton2 = QRadioButton("Player vs. CPU")
        radioButton2.setFixedWidth(107)
        radioButton3 = QRadioButton("Player vs. CPU vs. CPU")
        radioButton3.setFixedWidth(150)
        radioButton4 = QRadioButton("Player vs. CPU vs. CPU vs. CPU")
        radioButton4.setFixedWidth(193)

        self.radioGroup.addButton(radioButton2, 2)
        self.radioGroup.addButton(radioButton3, 3)
        self.radioGroup.addButton(radioButton4, 4)

        layout.addWidget(radioButton2)
        layout.addWidget(radioButton3)
        layout.addWidget(radioButton4)
        layout.addWidget(QLabel(""))

        difficultyLabel = QLabel("Select AI Difficulty:")
        layout.addWidget(difficultyLabel)

        self.difficultyGroup = QButtonGroup(self.playerSelectionDialog)
        easyButton = QRadioButton("Easy")
        easyButton.setFixedWidth(55)
        mediumButton = QRadioButton("Medium")
        mediumButton.setFixedWidth(75)
        hardButton = QRadioButton("Hard")
        hardButton.setFixedWidth(57)
        impossibleButton = QRadioButton("Impossible")
        impossibleButton.setFixedWidth(115)

        self.difficultyGroup.addButton(easyButton, 1)
        self.difficultyGroup.addButton(mediumButton, 2)
        self.difficultyGroup.addButton(hardButton, 3)
        self.difficultyGroup.addButton(impossibleButton, 3)

        layout.addWidget(easyButton)
        layout.addWidget(mediumButton)
        layout.addWidget(hardButton)
        layout.addWidget(impossibleButton)
        layout.addWidget(QLabel(""))
        
        buttonBox = QHBoxLayout()
        okButton = QPushButton("OK")
        cancelButton = QPushButton("Cancel")
        okButton.clicked.connect(lambda: self.startGameWithSelectedPlayers(self.playerSelectionDialog))
        cancelButton.clicked.connect(self.playerSelectionDialog.reject)
        buttonBox.addWidget(okButton)
        buttonBox.addWidget(cancelButton)
        layout.addLayout(buttonBox)

        self.playerSelectionDialog.setLayout(layout)
        centerDialog(self.playerSelectionDialog, self, "playerSelectionDialog")
        self.playerSelectionDialog.exec()

    def startGameWithSelectedPlayers(self, dialog):
        numPlayers = self.radioGroup.checkedId()
        difficulty = self.difficultyGroup.checkedId()
        if numPlayers in [2, 3, 4]:
            dialog.accept()
            self.hide()
            difficultyMap = {1: 'easy', 2: 'medium', 3: 'hard'}
            difficultyLevel = difficultyMap.get(difficulty, 'medium')
            self.controller = GameController(numPlayers, difficultyLevel, self.geometry())  # Pass the geometry
            self.controller.view.show()

    def playOnline(self):
        self.onlineDialog = QDialog(self)
        self.onlineDialog.setWindowTitle("Online Multiplayer")
        self.onlineDialog.setGeometry(835, 400, 250, 150)
        layout = QVBoxLayout()

        hostButton = QPushButton("Host Lobby")
        hostButton.clicked.connect(lambda: self.hostLobby(self.onlineDialog))
        layout.addWidget(hostButton)

        layout.addWidget(QLabel())

        joinButton = QPushButton("Join Lobby")
        joinButton.clicked.connect(lambda: self.joinLobby(self.onlineDialog))
        layout.addWidget(joinButton)

        layout.addWidget(QLabel())

        closeButton = QPushButton("Close")
        closeButton.setFixedWidth(75)
        closeButton.clicked.connect(self.onlineDialog.accept)
        layout.addWidget(closeButton, alignment=Qt.AlignmentFlag.AlignCenter)

        self.onlineDialog.setLayout(layout)
        centerDialog(self.onlineDialog, self, "playOnlineDialog")
        self.onlineDialog.exec()

    def hostLobby(self, onlineDialog):
        self.hostLobbyDialog = HostLobby(self, self)
        self.hostLobbyDialog.show()
        onlineDialog.accept()

    def joinLobby(self, onlineDialog):
        self.joinLobbyDialog = JoinLobby(self, self)
        self.joinLobbyDialog.show()
        onlineDialog.accept()

    def startHost(self):
        self.hide()
        self.server = Server('localhost', 5555, self.communicator)
        self.controller = GameController(numPlayers=2, difficulty='medium', parentCoord=self, connection=self.server, isHost=True, mainWindow=self)  
        self.server.controller = self.controller
        self.controller.view.show()

    def startClient(self):
        self.hide()
        self.client = Client('localhost', 5555, self.communicator) 
        self.controller = GameController(numPlayers=2, difficulty='medium', parentCoord=self, connection=self.client, isHost=False, mainWindow=self) 
        self.client.controller = self.controller
        self.controller.view.show()
    
    def showRules(self):
        self.rulesDialog = QDialog(self)
        self.rulesDialog.setWindowTitle("Rules")
        self.rulesDialog.setGeometry(560, 100, 800, 300)
        self.rulesDialog.setWindowIcon(QIcon(r"_internal\palaceData\palace.ico"))
        layout = QVBoxLayout()
        rulesLabel = QLabel(
            """<h2>The Pack</h2>
        <ul>
            <li>2-4 players use one standard deck of 52 cards.</li>
        </ul>
        <h2>Rank of Cards</h2>
        <ul>
            <li>A-K-Q-J-9-8-7-6-5-4-3</li>
            <li>The 2 and 10 are special cards that reset the deck.</li>
            <li>The 7 is a special card that reverses the rank hierarchy, the next player ONLY must play a card rank 7 or lower.</li>
        </ul>
        <h2>Object of the Game</h2>
        <ul>
            <li>Play your cards in a pile using ascending order, and the first player to run out of cards wins.</li>
        </ul>
        <h2>The Deal</h2>
        <ul>
            <li>Deal three cards face down to each player. Players are not allowed to look at these cards and must place them
            face down in three columns in front of each player.</li>
            <li>Deal six cards to each player face down. Players may look at these cards in their hand.</li>
            <li>Players select three cards from their hand and place them face up on the three face down cards in front of them.
            Typically, higher value cards are placed face up.</li>
            <li>Place the remaining cards from the deck face down in the center of the table to form the Draw pile.</li>
        </ul>
        <h2>The Play</h2>
        <ul>
            <li>The player with the agreed worst average top cards is the first player and the second player is clockwise or counter clockwise
            with the second worst average top cards.</li>
            <li>The first player plays any card from their hand. You can play multiple cards on your turn, as long as they're all equal to or
            higher than the top pile card.</li>
            <li>Once you have have finished your turn, draw cards from the Draw pile to maintain three cards in your hand at all times.</li>
            <li>You must play a card if you can or pick up the current pile and add it to your hand.</li>
            <li>On their turn, a player can play any 2 card which resets the top pile card to 2, starting the sequence all over.</li>
            <li>On their turn, a player can play the 10 on any card, but it puts the pile into a bomb pile instead of resetting the sequence. The
            player who put the 10 down then draws up to three cards and plays any card.</li>
            <li>If four of the same rank are played in a row, either by one player or multiple players, it clears the pile. Place it in the bomb pile,
            as these cards are out of the game. The player that played the fourth card can then play any card from their hand.</li>
            <li>Play continues around the table until the deck is depleted.</li>
            <li>Once the deck is depleted, players rely solely on the cards in their hand. Keep playing until there are no cards left in your
            hand.</li>
            <li>When it's your turn and you don't have a hand, play one card from your face-up cards in front of you.</li>
            <li>When it's your turn and you've played all your face-up cards, pick a card that's face-down on the table. Don't look at it to choose.
            Simply flip it over. If it plays on the current card by being equal or higher, you can play it. If not, you must pick up the discard pile.</li>
            <li>If you pick up the discard pile, you must play those before continuing to play your face-down cards.</li>
            <li>First player to finish all cards in hand, face-up cards, and face-down cards, wins the game.</li>
        </ul>
        <ul>
            <li>
        </ul>
        """
        )
        rulesLabel.setTextFormat(Qt.TextFormat.RichText)
        rulesLabel.setWordWrap(True)
        rulesLabel.setFixedWidth(800)
        layout.addWidget(rulesLabel)
        closeButton = QPushButton("Close")
        closeButton.clicked.connect(self.rulesDialog.accept)
        layout.addWidget(closeButton)
        self.rulesDialog.setLayout(layout)
        centerDialog(self.rulesDialog, self, "rulesDialog")
        self.rulesDialog.exec()

    def updateLogText(self, message):
        if hasattr(self, 'hostLobbyDialog') and self.hostLobbyDialog:
            self.hostLobbyDialog.logText.append(message)
        if hasattr(self, 'joinLobbyDialog') and self.joinLobbyDialog:
            self.joinLobbyDialog.logText.append(message)
    
    def updatePlayerCountLabel(self, text):
        if hasattr(self, 'hostLobbyDialog') and self.hostLobbyDialog:
            self.hostLobbyDialog.playerCountLabel.setText(text)
    
    def setStartButtonEnabled(self, enabled):
        if hasattr(self, 'hostLobbyDialog') and self.hostLobbyDialog:
            self.hostLobbyDialog.startButton.setEnabled(enabled)
    
class Player:
    def __init__(self, name):
        self.name = name
        self.hand = []
        self.bottomCards = []
        self.topCards = []

    def playCard(self, cardIndex, pile):
        card = self.hand.pop(cardIndex)
        if card[2]:
            card = (card[0], card[1], False, False)
        if card[3]:
            card = (card[0], card[1], card[2], False)
        pile.append(card)
        return card

    def addToHand(self, cards):
        self.hand.extend(cards)

    def pickUpPile(self, pile):
        self.hand.extend(pile)
        pile.clear()

class GameView(QWidget):
    def __init__(self, controller, playerType, communicator, parentCoord):
        super().__init__()
        self.controller = controller
        self.playerType = playerType
        self.communicator = communicator
        self.initUI()

        # Connect signals to slots
        self.communicator.updateOpponentBottomCardsSignal.connect(self.updateOpponentBottomCards)
        self.communicator.updateOpponentTopCardsSignal.connect(self.updateOpponentTopCards)
        self.communicator.updateOpponentHandSignal.connect(self.updateOpponentHand)
        self.communicator.resetGameSignal.connect(self.handleResetGame)
        self.communicator.disconnectSignal.connect(self.handleDisconnect)

        # Use the centerDialog function to position the window
        centerDialog(self, parentCoord, "GameView")
        
    def initUI(self):
        self.setWindowTitle(f'Palace Card Game - {self.playerType}')
        self.setWindowIcon(QIcon(r"_internal\palaceData\palace.ico"))
        self.setGeometry(450, 75, 900, 900)
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)

        self.layout = QGridLayout()

        # Disconnect Button (row 0, column 0)
        self.disconnectButton = QPushButton("Disconnect")
        self.disconnectButton.setFixedWidth(125)
        self.disconnectButton.setFixedHeight(25)
        self.disconnectButton.clicked.connect(self.disconnect)
        self.layout.addWidget(self.disconnectButton, 0, 0)
        
        # Disconnect Button Spacer (row 0, column 0)
        self.disconnectButtonSpacer = QLabel()
        self.disconnectButtonSpacer.setFixedWidth(125)
        self.disconnectButtonSpacer.setFixedHeight(25)
        self.layout.addWidget(self.disconnectButtonSpacer, 0, 9)
        
        # Opponent Hand (row 0, column 5)
        self.opponentHandContainer = QWidget()
        self.opponentHandContainer.setMaximumWidth(500)  # Set maximum width here
        self.opponentHandLayout = QHBoxLayout(self.opponentHandContainer)
        # Create a container layout with spacers to center the hand layout
        self.opponentHandContainerLayout = QHBoxLayout()
        self.opponentHandContainerLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.opponentHandContainerLayout.addWidget(self.opponentHandContainer, alignment=Qt.AlignmentFlag.AlignCenter)
        self.opponentHandContainerLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.layout.addLayout(self.opponentHandContainerLayout, 0, 5, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Opponent Hand Label (row 1, column 5)
        self.opponentHandLabel = QLabel(f"{'Player 2' if self.playerType == 'Player 1' else 'Player 1'}'s Hand")
        self.opponentHandLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.opponentHandLabel, 1, 5, alignment=Qt.AlignmentFlag.AlignCenter)

        # Opponent Top Cards (row 2, column 5)
        self.opponentTopCardsLayout = QHBoxLayout()
        self.layout.addLayout(self.opponentTopCardsLayout, 2, 5, alignment=Qt.AlignmentFlag.AlignCenter)

        # Opponent Bottom Cards (row 3, column 5)
        self.opponentBottomCardsLayout = QHBoxLayout()
        self.layout.addLayout(self.opponentBottomCardsLayout, 3, 5, alignment=Qt.AlignmentFlag.AlignCenter)

        # Spacer (row 4, column 5)
        spacer1 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout.addItem(spacer1, 4, 5)

        # Center layout setup (row 5, column 5)
        self.deckLabel = QLabel()
        self.deckLabel.setFixedWidth(190)
        self.deckLabel.setVisible(False)
        self.pileLabel = QLabel("\t     Select your 3 Top cards...")
        self.pileLabel.setStyleSheet("border: 0px solid black; background-color: transparent;")
        self.pickUpPileButton = QPushButton("Pick Up Pile")
        self.pickUpPileButton.setFixedWidth(125)
        self.pickUpPileButton.setVisible(False)
        self.pickUpPileButton.clicked.connect(self.controller.pickUpPile)
        self.currentPlayerLabel = QLabel("")

        spacer = QSpacerItem(60, 1, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.consoleLayout = QHBoxLayout()
        self.consoleLayout.addWidget(self.deckLabel, alignment=Qt.AlignmentFlag.AlignLeft)
        self.consoleLayout.addWidget(self.pileLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.consoleLayout.addItem(spacer)
        self.consoleLayout.addWidget(self.pickUpPileButton, alignment=Qt.AlignmentFlag.AlignRight)

        self.centerContainer = QWidget()
        self.centerContainer.setLayout(self.consoleLayout)
        self.centerContainer.setFixedWidth(500)

        self.centerLayout = QVBoxLayout()
        self.centerLayout.addWidget(QLabel(""))
        self.centerLayout.addWidget(self.currentPlayerLabel, alignment=Qt.AlignmentFlag.AlignCenter)
        self.centerLayout.addWidget(self.centerContainer, alignment=Qt.AlignmentFlag.AlignCenter)
        self.centerLayout.addWidget(QLabel(""))
        self.centerLayout.addWidget(QLabel(""))

        self.layout.addLayout(self.centerLayout, 5, 5, alignment=Qt.AlignmentFlag.AlignCenter)

        # Spacer (row 6, column 5)
        spacer2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.layout.addItem(spacer2, 6, 5)

        # Player Bottom Cards (row 7, column 5)
        self.bottomCardsLayout = QHBoxLayout()
        self.layout.addLayout(self.bottomCardsLayout, 7, 5, alignment=Qt.AlignmentFlag.AlignCenter)

        # Player Top Cards (row 8, column 5)
        self.topCardsLayout = QHBoxLayout()
        self.layout.addLayout(self.topCardsLayout, 8, 5, alignment=Qt.AlignmentFlag.AlignCenter)

        # Player Hand Label (row 9, column 5)
        self.playerHandLabel = QLabel(f"{self.playerType}'s Hand")
        self.playerHandLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.playerHandLabel, 9, 5, alignment=Qt.AlignmentFlag.AlignCenter)

        # Player Hand (row 10, column 5)
        self.playerHandContainer = QWidget()
        self.playerHandContainer.setMaximumWidth(500)  # Set maximum width here
        self.playerHandLayout = QHBoxLayout(self.playerHandContainer)
        # Create a container layout with spacers to center the hand layout
        self.playerHandContainerLayout = QHBoxLayout()
        self.playerHandContainerLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.playerHandContainerLayout.addWidget(self.playerHandContainer, alignment=Qt.AlignmentFlag.AlignCenter)
        self.playerHandContainerLayout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.layout.addLayout(self.playerHandContainerLayout, 10, 5, alignment=Qt.AlignmentFlag.AlignCenter)

        # Confirm/Place Button (row 11, column 5)
        buttonsContainerLayout = QVBoxLayout()
        self.confirmButton = QPushButton("Confirm")
        self.confirmButton.setEnabled(False)
        self.confirmButton.setFixedWidth(240)
        self.confirmButton.clicked.connect(self.confirmTopCardSelection)
        self.placeButton = QPushButton("Select A Card")
        self.placeButton.setEnabled(False)
        self.placeButton.setFixedWidth(240)
        self.placeButton.clicked.connect(self.controller.placeCard)
        self.placeButton.setVisible(False)

        buttonsContainerLayout.addWidget(self.confirmButton, alignment=Qt.AlignmentFlag.AlignCenter)
        buttonsContainerLayout.addWidget(self.placeButton, alignment=Qt.AlignmentFlag.AlignCenter)
        self.layout.addLayout(buttonsContainerLayout, 11, 5, alignment=Qt.AlignmentFlag.AlignCenter)

        # Width of the center console column
        self.layout.setColumnMinimumWidth(5, 500)

        if self.controller.numPlayers >= 3:
            # Player 3 setup
            self.player3HandLayout = QVBoxLayout()
            self.player3TopCardsLayout = QVBoxLayout()
            self.player3BottomCardsLayout = QVBoxLayout()

            self.layout.addLayout(self.player3HandLayout, 5, 0, alignment=Qt.AlignmentFlag.AlignCenter)
            self.player3HandLabel = QLabel("Player 3's Hand")
            self.player3HandLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(self.player3HandLabel, 5, 1, alignment=Qt.AlignmentFlag.AlignCenter)
            self.layout.addLayout(self.player3TopCardsLayout, 5, 2, alignment=Qt.AlignmentFlag.AlignCenter)
            self.layout.addLayout(self.player3BottomCardsLayout, 5, 3, alignment=Qt.AlignmentFlag.AlignCenter)

            # Spacer (row 5, column 4)
            spacer3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            self.layout.addItem(spacer3, 5, 4)

        if self.controller.numPlayers == 4:
            # Player 4 setup
            self.player4HandLayout = QVBoxLayout()
            self.player4TopCardsLayout = QVBoxLayout()
            self.player4BottomCardsLayout = QVBoxLayout()

            # Spacer (row 5, column 6)
            self.layout.addItem(spacer3, 5, 6)

            self.layout.addLayout(self.player4BottomCardsLayout, 5, 7, alignment=Qt.AlignmentFlag.AlignCenter)
            self.layout.addLayout(self.player4TopCardsLayout, 5, 8, alignment=Qt.AlignmentFlag.AlignCenter)
            self.player4HandLabel = QLabel("Player 4's Hand")
            self.player4HandLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(self.player4HandLabel, 5, 9, alignment=Qt.AlignmentFlag.AlignCenter)
            self.layout.addLayout(self.player4HandLayout, 5, 10, alignment=Qt.AlignmentFlag.AlignCenter)

        self.setLayout(self.layout)
    
    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
    
    def handleResetGame(self):
        self.clearSelectionLayout()
    
    def updateHandButtons(self, hand, layout, isPlayer, rotate):
        self.controller.playCardButtons = []
        for idx, card in enumerate(hand):
            button = QLabel()
            if rotate:
                button.setFixedSize(BUTTON_HEIGHT, BUTTON_WIDTH)
            else:
                button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            button.setStyleSheet("border: 0px solid black; background-color: transparent;")
            if not card[0] == "":
                if not card[3] and isPlayer:
                    pixmap = QPixmap(fr"_internal\palaceData\cards\{card[0].lower()}_of_{card[1].lower()}.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    if rotate:
                        transform = QTransform().rotate(90)
                        pixmap = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation).scaled(CARD_HEIGHT, CARD_WIDTH, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    else:
                        pixmap = pixmap.scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    button.setPixmap(pixmap)
                else:
                    pixmap = QPixmap(r"_internal\palaceData\cards\back.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    if rotate:
                        transform = QTransform().rotate(90)
                        pixmap = pixmap.transformed(transform, Qt.TransformationMode.SmoothTransformation).scaled(CARD_HEIGHT, CARD_WIDTH, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    else:
                        pixmap = pixmap.scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                    button.setPixmap(pixmap)
                button.setAlignment(Qt.AlignmentFlag.AlignCenter)
                if self.controller.topCardSelectionPhase:
                    button.mousePressEvent = lambda event, idx=idx, btn=button: self.selectTopCard(idx, btn)
                else:
                    try:
                        button.mousePressEvent = lambda event, idx=idx, btn=button: self.controller.prepareCardPlacement(idx, btn)
                    except IndexError:
                        return
            self.controller.playCardButtons.append(button)
            layout.addWidget(button)

        if len(hand) >= 10:
            spacer = QLabel()
            spacer.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            layout.addWidget(spacer)

    def updateOpponentHand(self, playerIndex, hand):
        self.controller.players[playerIndex].hand = hand
        self.updateOpponentHandButtons(hand)
        
    def updateOpponentTopCards(self, playerIndex, topCards):
        self.controller.players[playerIndex].topCards = topCards
        self.updateOpponentTopCardButtons(topCards)
        
    def updateOpponentBottomCards(self, playerIndex, bottomCards):
        self.controller.players[playerIndex].bottomCards = bottomCards
        self.updateOpponentBottomCardButtons(bottomCards)
    
    def updatePlayerHandButtons(self, hand):
        self.clear_layout(self.playerHandLayout)  # Clear the layout before updating
        self.updateHandButtons(hand, self.playerHandLayout, True, False)

    def updateOpponentHandButtons(self, hand):
        self.clear_layout(self.opponentHandLayout)  # Clear the layout before updating
        self.updateHandButtons(hand, self.opponentHandLayout, False, False)

    def updatePlayerTopCardButtons(self, topCards):
        self.clear_layout(self.topCardsLayout)  # Clear the layout before updating
        for card in topCards:
            button = QLabel()
            button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            button.setStyleSheet("border: 0px solid black; background-color: transparent;")
            pixmap = QPixmap(f"_internal\palaceData\cards\{card[0].lower()}_of_{card[1].lower()}.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            button.setPixmap(pixmap)
            button.setAlignment(Qt.AlignmentFlag.AlignCenter)
            button.setDisabled(True)
            self.topCardsLayout.addWidget(button)
        if not topCards:
            self.placeholder = QLabel()
            self.placeholder.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            self.topCardsLayout.addWidget(self.placeholder)

    def updateOpponentTopCardButtons(self, topCards):
        self.clear_layout(self.opponentTopCardsLayout)  # Clear the layout before updating
        for card in topCards:
            button = QLabel()
            button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            button.setStyleSheet("border: 0px solid black; background-color: transparent;")
            pixmap = QPixmap(f"_internal\palaceData\cards\{card[0].lower()}_of_{card[1].lower()}.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            button.setPixmap(pixmap)
            button.setAlignment(Qt.AlignmentFlag.AlignCenter)
            button.setDisabled(True)
            self.opponentTopCardsLayout.addWidget(button)
        if not topCards:
            self.placeholder = QLabel()
            self.placeholder.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            self.opponentTopCardsLayout.addWidget(self.placeholder)

    def updatePlayerBottomCardButtons(self, bottomCards):
        self.clear_layout(self.bottomCardsLayout)  # Clear the layout before updating
        for card in bottomCards:
            button = QLabel()
            button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            button.setStyleSheet("border: 0px solid black; background-color: transparent;")
            pixmap = QPixmap(r"_internal\palaceData\cards\back.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            button.setPixmap(pixmap)
            button.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.bottomCardsLayout.addWidget(button)
        if not bottomCards:
            self.placeholder = QLabel()
            self.placeholder.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            self.bottomCardsLayout.addWidget(self.placeholder)

    def updateOpponentBottomCardButtons(self, bottomCards):
        self.clear_layout(self.opponentBottomCardsLayout)  # Clear the layout before updating
        for card in bottomCards:
            button = QLabel()
            button.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            button.setStyleSheet("border: 0px solid black; background-color: transparent;")
            pixmap = QPixmap(r"_internal\palaceData\cards\back.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            button.setPixmap(pixmap)
            button.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.opponentBottomCardsLayout.addWidget(button)
        if not bottomCards:
            self.placeholder = QLabel()
            self.placeholder.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            self.opponentBottomCardsLayout.addWidget(self.placeholder)

    def confirmTopCardSelection(self):
        if self.controller.isHost:
            playerIndex = 0
        else:
            playerIndex = 1
        player = self.controller.players[playerIndex]
        for card, _ in self.chosenCards:
            player.topCards.append((card[0], card[1], True, False))
        for card, cardIndex in sorted(self.chosenCards, key=lambda x: x[1], reverse=True):
            del player.hand[cardIndex]

        if self.controller.isHost:
            self.updatePlayerBottomCardButtons(player.bottomCards)
            self.updatePlayerTopCardButtons(player.topCards)
            self.updatePlayerHandButtons(player.hand)
            self.controller.connection.sendToClient({
                'action': 'confirmTopCards',
                'playerIndex': playerIndex,
                'topCards': player.topCards,
                'bottomCards': player.bottomCards,
                'hand': player.hand
            })
        else:
            self.updatePlayerBottomCardButtons(player.bottomCards)
            self.updatePlayerTopCardButtons(player.topCards)
            self.updatePlayerHandButtons(player.hand)
            self.controller.connection.sendToServer({
                'action': 'confirmTopCards',
                'playerIndex': playerIndex,
                'topCards': player.topCards,
                'bottomCards': player.bottomCards,
                'hand': player.hand
            })
        self.confirmButton.setDisabled(True)
        self.disablePlayerHand()
    
    def updateUI(self, currentPlayer, deckSize, pile):
        self.enableOpponentHandNotClickable()
        if self.controller.topCardSelectionPhase:
            self.confirmButton.setEnabled(len(self.chosenCards) == 3)
        else:
            self.confirmButton.setVisible(False)
            self.placeButton.setVisible(True)
            self.deckLabel.setVisible(True)
            self.currentPlayerLabel.setVisible(True)
            self.pickUpPileButton.setVisible(True)
            self.currentPlayerLabel.setText("Current Player: ")
            self.pileLabel.setFixedSize(BUTTON_WIDTH, BUTTON_HEIGHT)
            self.currentPlayerLabel.setText(f"Current Player: {currentPlayer.name}")

            if deckSize:
                self.deckLabel.setText(f"Draw Deck:\n\n{deckSize} cards remaining")
            else:
                self.deckLabel.setText("Draw Deck:\n\nEmpty")

            if self.pileLabel.text() != "Bombed!!!" and not pile:
                self.pileLabel.setText("Pile: Empty")
            
            if pile:
                topCard = pile[-1]
                pixmap = QPixmap(fr"_internal/palaceData/cards/{topCard[0].lower()}_of_{topCard[1].lower()}.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
                self.pileLabel.setPixmap(pixmap)

            self.placeButton.setEnabled(len(self.controller.selectedCards) > 0)
       
    def revealCard(self, cardLabel, card):
        pixmap = QPixmap(fr"_internal/palaceData/cards/{card[0].lower()}_of_{card[1].lower()}.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        cardLabel.setPixmap(pixmap)

    def showTopCardSelection(self):
        self.chosenCards = []
        self.cardButtons = []

    def selectTopCard(self, cardIndex, button):
        if self.controller.isHost:
            playerIndex = 0 
        else:
            playerIndex = 1
        card = self.controller.players[playerIndex].hand[cardIndex]
        if (card, cardIndex) in self.chosenCards:
            self.chosenCards.remove((card, cardIndex))
            button.setStyleSheet("border: 0px solid black; background-color: transparent;")
        else:
            if len(self.chosenCards) < 3:
                self.chosenCards.append((card, cardIndex))
                button.setStyleSheet("border: 0px solid black; background-color: blue;")
        self.confirmButton.setEnabled(len(self.chosenCards) == 3)

    def clearSelectionLayout(self):
        self.chosenCards = []
        self.cardButtons = []
        self.pile = []
        self.topCardSelectionPhase = True
        self.pileLabel.setText("\t     Select your 3 Top cards...")
        self.pileLabel.setFixedWidth(200)
        self.deckLabel.setVisible(False)
        self.currentPlayerLabel.setVisible(False)
        self.pickUpPileButton.setVisible(False)
        self.placeButton.setVisible(False)
        self.confirmButton.setVisible(True)
        
        # Clear player hand layout
        while self.playerHandLayout.count():
            item = self.playerHandLayout.takeAt(0)
            widget = item.widget()
            if widget is None or (isinstance(widget, QLabel) and widget.pixmap() is None):  # Check if it's the spacer
                continue
            widget.deleteLater()
        
        # Clear opponent hand layout
        while self.opponentHandLayout.count():
            item = self.opponentHandLayout.takeAt(0)
            widget = item.widget()
            if widget is None or (isinstance(widget, QLabel) and widget.pixmap() is None):  # Check if it's the spacer
                continue
            widget.deleteLater()
        
        # Clear player top cards layout
        while self.topCardsLayout.count():
            item = self.topCardsLayout.takeAt(0)
            widget = item.widget()
            if widget is None or (isinstance(widget, QLabel) and widget.pixmap() is None):  # Check if it's the spacer
                continue
            widget.deleteLater()
        
        # Clear player bottom cards layout
        while self.bottomCardsLayout.count():
            item = self.bottomCardsLayout.takeAt(0)
            widget = item.widget()
            if widget is None or (isinstance(widget, QLabel) and widget.pixmap() is None):  # Check if it's the spacer
                continue
            widget.deleteLater()
        
        # Clear opponent top cards layout
        while self.opponentTopCardsLayout.count():
            item = self.opponentTopCardsLayout.takeAt(0)
            widget = item.widget()
            if widget is None or (isinstance(widget, QLabel) and widget.pixmap() is None):  # Check if it's the spacer
                continue
            widget.deleteLater()
        
        # Clear opponent bottom cards layout
        while self.opponentBottomCardsLayout.count():
            item = self.opponentBottomCardsLayout.takeAt(0)
            widget = item.widget()
            if widget is None or (isinstance(widget, QLabel) and widget.pixmap() is None):  # Check if it's the spacer
                continue
            widget.deleteLater()

    def enablePlayerHand(self):
        for i in range(self.playerHandLayout.count()):
            widget = self.playerHandLayout.itemAt(i).widget()
            if widget is None or (isinstance(widget, QLabel) and widget.pixmap() is None):  # Check if it's the spacer
                continue
            widget.setEnabled(True)

    def disablePlayerHand(self):
        for i in range(self.playerHandLayout.count()):
            widget = self.playerHandLayout.itemAt(i).widget()
            if widget is None or (isinstance(widget, QLabel) and widget.pixmap() is None):  # Check if it's the spacer
                continue
            widget.setEnabled(False)

    def enableOpponentHandNotClickable(self):
        for i in range(self.opponentHandLayout.count()):
            widget = self.opponentHandLayout.itemAt(i).widget()
            if widget:
                widget.setEnabled(True)
                widget.mousePressEvent = lambda event: None 

    def handleDisconnect(self):
        if self.controller.isHost:
            self.controller.view.updateLogText("Client has disconnected.")
            self.controller.view.disablePlayerHand()
        else:
            self.controller.disconnect()
            self.close()
            self.controller.returnToMainMenu()
    
    def disconnect(self):
        self.controller.disconnect()
        self.close()
        self.controller.returnToMainMenu()
        
    def closeEvent(self, event):
        self.controller.closeConnections()
        event.accept()
    
class GameController(QObject):
    gameOverSignal = Signal(str)

    def __init__(self, numPlayers, difficulty, parentCoord, connection=None, isHost=False, mainWindow=None):
        super().__init__()
        self.numPlayers = numPlayers
        self.difficulty = difficulty
        self.isHost = isHost
        self.mainWindow = mainWindow  # Add reference to mainWindow
        if connection is None:
            self.communicator = SignalCommunicator()
        else:
            self.communicator = connection.communicator
        self.communicator.startGameSignal.connect(self.proceedWithGameSetup)
        self.communicator.proceedWithGameSetupSignal.connect(self.proceedWithGameSetupOnMainThread)
        self.communicator.updateUISignal.connect(self.updateUI)
        self.communicator.updateDeckSignal.connect(self.receiveDeckFromServer)
        self.gameOverSignal.connect(self.stopTimer)
        self.communicator.setupGameSignal.connect(self.setupGame)
        if isHost:
            self.playerType = "Player 1"
        else:
            self.playerType = "Player 2"
        self.view = GameView(self, self.playerType, self.communicator, parentCoord)
        self.players = [Player("Player 1"), Player("Player 2")]
        self.sevenSwitch = False
        self.deck = []
        self.pile = []
        self.currentPlayerIndex = 0
        self.selectedCards = []
        self.playCardButtons = []
        self.topCardSelectionPhase = True
        self.connection = connection
        self.gameOver = False    
        self.playAgainCount = 0
        self.setupGame()

        # Track threads for cleanup
        self.threads = []

    def handleDisconnect(self):
        if self.isHost:
            self.view.updateLogText("Client has disconnected.")
            self.view.disablePlayerHand()
        else:
            self.disconnect()
            self.returnToMainMenu()
    
    def disconnect(self):
        self.gameOver = True
        self.closeThreads()
        if self.connection:
            self.connection.close()
        if not self.isHost:
            self.handleDisconnect()
    
    def returnToMainMenu(self):
        self.mainWindow.returnToMainMenu()
    
    def showGameOverDialog(self, winnerName):
        dialog = GameOverDialog(winnerName, self.view)
        dialog.playAgainSignal.connect(self.requestPlayAgain)
        dialog.mainMenuSignal.connect(self.returnToMainMenu)
        dialog.exitSignal.connect(self.exitGame)
        dialog.exec()
    
    def exitGame(self):
        QCoreApplication.instance().quit
    
    def notifyReset(self):
        data = {'action': 'resetGame'}
        self.connection.sendToClient(data)
    
    def requestPlayAgain(self):
        if self.playAgainCount == 2:
            self.handlePlayAgain()
        else:
            self.playAgainCount += 1
            if self.isHost:
                data = {'action': 'playAgainRequest', 
                        'count' : self.playAgainCount}
                self.connection.sendToClient(data)
            else:
                data = {'action': 'playAgainRequest', 
                        'count' : self.playAgainCount}
                self.connection.sendToServer(data)

    def handlePlayAgain(self):
        if self.playAgainCount == 2 and self.isHost:
            self.resetGame()
            self.notifyReset()
            self.communicator.setupGameSignal.emit()
        elif self.playAgainCount == 2:
            data = {'action': 'playAgainRequest', 
                    'count' : self.playAgainCount}
            self.connection.sendToServer(data)

    def resetGame(self):
        self.deck = []
        self.pile = []
        self.currentPlayerIndex = 0
        self.selectedCards = []
        self.playCardButtons = []
        self.topCardSelectionPhase = True
        self.players = [Player("Player 1"), Player("Player 2")]
        self.view.clearSelectionLayout()
        self.communicator.resetGameSignal.emit()
    
    def stopTimer(self, winner):
        if hasattr(self, 'timer'):
            self.timer.stop()
        QApplication.processEvents()
        time.sleep(1.2)
        self.showGameOverDialog(winner)
    
    def startGameLoop(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.gameLoop)
        self.timer.start(1000)  # Run the game loop every second

    def gameLoop(self):
        currentPlayer = self.players[self.currentPlayerIndex]
        self.view.updateUI(currentPlayer, len(self.deck), self.pile)

    def pickUpPile(self):
        if not self.pile:
            return
        currentPlayer = self.players[self.currentPlayerIndex]
        currentPlayer.pickUpPile(self.pile)
        print(f"{currentPlayer.name} picks up the pile\n")
        self.view.pileLabel.setText("Pile: Empty")
        self.sevenSwitch = False
        self.updateUI()
        self.changeTurn()
        self.sendGameState()
        self.view.placeButton.setText("Opponent's Turn...")

    def setupGame(self):
        if self.isHost:
            self.deck = self.createDeck()
            random.shuffle(self.deck)
            self.dealInitialCards(self.players[0])
            self.dealInitialCards(self.players[1])
            self.sendDeckToClient()
            self.view.updatePlayerHandButtons(self.players[0].hand)
        else:
            self.view.updatePlayerHandButtons(self.players[1].hand)
        self.view.showTopCardSelection()

    def proceedWithGameSetup(self):
        self.communicator.proceedWithGameSetupSignal.emit()

    def proceedWithGameSetupOnMainThread(self):
        self.topCardSelectionPhase = False
        self.updateUI()
        self.view.pileLabel.setText("Pile: Empty")
        if self.playerType == "Player 2":
            self.view.disablePlayerHand()
            self.view.pickUpPileButton.setDisabled(True)
        self.startGameLoop()

    def createDeck(self):
        suits = ['clubs', 'spades', 'hearts', 'diamonds']
        return [(rank, suit, False, False) for rank in RANKS for suit in suits]

    def dealInitialCards(self, player):
        player.bottomCards = [(card[0], card[1], False, True) for card in self.deck[:3]]
        player.hand = self.deck[3:9]
        self.deck = self.deck[9:]

    def sendDeckToClient(self):
        data = {'action': 'deckSync', 
                'deck': self.deck, 
                'player2bot': self.players[1].bottomCards,
                'player2top': self.players[1].topCards,
                'player2hand': self.players[1].hand
            }
        self.connection.sendToClient(data)
                
    def receiveDeckFromServer(self, data):
        self.deck = data['deck']
        self.players[1].bottomCards = data['player2bot']
        self.players[1].topCards = data['player2top']
        self.players[1].hand = data['player2hand']
        self.view.updatePlayerHandButtons(self.players[1].hand)
        self.view.placeButton.setText("Opponent's Turn...")

    def checkBothPlayersConfirmed(self):
        time.sleep(1)
        if all(player.topCards for player in self.players):
            self.sendStartGameSignal()
            self.proceedWithGameSetup()
    
    def sendStartGameSignal(self):
        data = {'action': 'startGame', 'gameState': ""}
        if self.isHost:
            self.connection.sendToClient(data)
        else:
            self.connection.sendToServer(data)
    
    def updateUI(self):
        self.view.enableOpponentHandNotClickable()
        currentPlayer = self.players[self.currentPlayerIndex]
        if not self.topCardSelectionPhase:
            self.view.updateUI(currentPlayer, len(self.deck), self.pile)
            if self.isHost:
                self.view.updatePlayerHandButtons(self.players[0].hand)
                self.view.updateOpponentHandButtons(self.players[1].hand)
                self.view.updatePlayerTopCardButtons(self.players[0].topCards)
                self.view.updateOpponentTopCardButtons(self.players[1].topCards)
                self.view.updatePlayerBottomCardButtons(self.players[0].bottomCards)
                self.view.updateOpponentBottomCardButtons(self.players[1].bottomCards)
            else:
                self.view.updatePlayerHandButtons(self.players[1].hand)
                self.view.updateOpponentHandButtons(self.players[0].hand)
                self.view.updatePlayerTopCardButtons(self.players[1].topCards)
                self.view.updateOpponentTopCardButtons(self.players[0].topCards)
                self.view.updatePlayerBottomCardButtons(self.players[1].bottomCards)
                self.view.updateOpponentBottomCardButtons(self.players[0].bottomCards)
        if not self.gameOver:
            if self.isSessionPlayer():
                self.updatePlayableCards()
            else:
                self.view.disablePlayerHand()

    def prepareCardPlacement(self, cardIndex, cardLabel):
        card = self.players[self.currentPlayerIndex].hand[cardIndex]
        if (card, cardLabel) in self.selectedCards:
            self.selectedCards.remove((card, cardLabel))
            cardLabel.setStyleSheet("border: 0px solid black; background-color: transparent;")
        else:
            self.selectedCards.append((card, cardLabel))
            cardLabel.setStyleSheet("border: 0px solid black; background-color: blue;")

        selectedCardRank = card[0]
        handIndex = 0
        if not self.selectedCards:
            for i in range(self.view.playerHandLayout.count()):
                lbl = self.view.playerHandLayout.itemAt(i).widget()
                if lbl is None or (isinstance(lbl, QLabel) and lbl.pixmap() is None):
                    continue
                if handIndex >= len(self.players[self.currentPlayerIndex].hand):
                    break
                handCard = self.players[self.currentPlayerIndex].hand[handIndex]
                if handCard[3] or self.isCardPlayable(handCard):
                    lbl.setEnabled(True)
                handIndex += 1
        else:
            handIndex = 0
            for i in range(self.view.playerHandLayout.count()):
                lbl = self.view.playerHandLayout.itemAt(i).widget()
                if lbl is None or (isinstance(lbl, QLabel) and lbl.pixmap() is None):
                    continue
                if handIndex >= len(self.players[self.currentPlayerIndex].hand):
                    break
                handCard = self.players[self.currentPlayerIndex].hand[handIndex]
                if handCard[0] == selectedCardRank or (handCard, lbl) in self.selectedCards:
                    lbl.setEnabled(True)
                elif not handCard[3]:
                    lbl.setEnabled(False)
                handIndex += 1
        self.view.placeButton.setEnabled(len(self.selectedCards) > 0)
        if self.view.placeButton.text() == "Place":
            self.view.placeButton.setText("Select A Card")
        else:
            self.view.placeButton.setText("Place")

    def isCardPlayable(self, card):
        if self.pile:
            topCard = self.pile[-1]
        else:
            topCard = None
        if self.sevenSwitch:
            return VALUES[card[0]] <= 7 or card[0] in ['2', '10']
        if not topCard:
            return True
        return card[0] == '2' or card[0] == '10' or VALUES[card[0]] >= VALUES[topCard[0]]

    def placeCard(self):
        currentPlayer = self.players[self.currentPlayerIndex]
        playedCards = []
        pickUp = False

        for card, button in sorted(self.selectedCards, key=lambda x: currentPlayer.hand.index(x[0])):
            if card[3] and not self.isCardPlayable(card):
                playedCards.append(card)
                for i, card in enumerate(playedCards):
                    self.pile.append(currentPlayer.hand.pop(currentPlayer.hand.index(playedCards[i])))
                    self.pile[-1] = (card[0], card[1], card[2], False)
                    self.view.revealCard(button, card)
                pickUp = True
                button.setParent(None)
                button.deleteLater()
            else:
                playedCards.append(card)
                currentPlayer.playCard(currentPlayer.hand.index(card), self.pile)
                self.view.revealCard(button, card)
                button.setParent(None)
                button.deleteLater()

        if pickUp:
            topCard = self.pile[-1]
            pixmap = QPixmap(fr"_internal/palaceData/cards/{topCard[0].lower()}_of_{topCard[1].lower()}.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.view.pileLabel.setPixmap(pixmap)
            QCoreApplication.processEvents()
            time.sleep(1)
            currentPlayer.pickUpPile(self.pile)
            print(f"{currentPlayer.name} picks up the pile\n")
            self.view.pileLabel.setText("Pile: Empty")
            self.sevenSwitch = False
            for card in reversed(currentPlayer.hand):
                if card[3]:
                    currentPlayer.bottomCards.append(currentPlayer.hand.pop(currentPlayer.hand.index(card)))
            self.updateUI()
            self.changeTurn()
            self.sendGameState()
            self.view.placeButton.setText("Opponent's Turn...")
            return

        self.selectedCards = []
        print(f"{currentPlayer.name} plays {', '.join([f'{card[0]} of {card[1]}' for card in playedCards])}\n")

        while len(currentPlayer.hand) < 3 and self.deck:
            currentPlayer.hand.append(self.deck.pop(0))

        self.view.updatePlayerHandButtons(currentPlayer.hand)

        if self.checkFourOfAKind():
            print("Four of a kind! Clearing the pile.\n")
            self.sevenSwitch = False
            topCard = self.pile[-1]
            pixmap = QPixmap(fr"_internal/palaceData/cards/{topCard[0].lower()}_of_{topCard[1].lower()}.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.view.pileLabel.setPixmap(pixmap)
            self.checkGameState()
            self.updateUI()
            self.sendGameState()
            self.pile.clear()
            self.updateUI()
            self.view.pileLabel.setText("Bombed!!!")
            self.view.placeButton.setText("Select A Card")
            return
        
        if '2' in [card[0] for card in playedCards]:
            self.sevenSwitch = False
            topCard = self.pile[-1]
            pixmap = QPixmap(fr"_internal/palaceData/cards/{topCard[0].lower()}_of_{topCard[1].lower()}.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.view.pileLabel.setPixmap(pixmap)
            self.updateUI()
            self.checkGameState()
            self.sendGameState()
            self.view.placeButton.setText("Select A Card")
        elif '10' in [card[0] for card in playedCards]:
            self.sevenSwitch = False
            topCard = self.pile[-1]
            pixmap = QPixmap(fr"_internal/palaceData/cards/{topCard[0].lower()}_of_{topCard[1].lower()}.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.view.pileLabel.setPixmap(pixmap)
            self.checkGameState()
            self.updateUI()
            self.sendGameState()
            self.pile.clear()
            self.updateUI()
            self.view.pileLabel.setText("Bombed!!!")
            self.view.placeButton.setText("Select A Card")
        else:
            if '7' in [card[0] for card in playedCards]:
                self.sevenSwitch = True
            else:
                self.sevenSwitch = False
            self.view.placeButton.setEnabled(False)
            topCard = self.pile[-1]
            pixmap = QPixmap(fr"_internal/palaceData/cards/{topCard[0].lower()}_of_{topCard[1].lower()}.png").scaled(CARD_WIDTH, CARD_HEIGHT, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.view.pileLabel.setPixmap(pixmap)
            self.checkGameState()
            self.updateUI()
            if not self.gameOver:
                self.changeTurn()
            self.sendGameState()
            self.view.placeButton.setText("Opponent's Turn...")
        if self.gameOver:
            self.gameOverSignal.emit(currentPlayer.name)

    def changeTurn(self):
        self.currentPlayerIndex = (self.currentPlayerIndex + 1) % len(self.players)
        self.selectedCards = []
        self.updateUI()
        self.view.disablePlayerHand()
        self.view.pickUpPileButton.setEnabled(False)

    def checkFourOfAKind(self):
        if len(self.pile) < 4:
            return False
        return len(set(card[0] for card in self.pile[-4:])) == 1

    def isSessionPlayer(self):
        if self.isHost:
            return self.currentPlayerIndex == 0 and self.playerType == "Player 1"
        else:
            return self.currentPlayerIndex == 1 and self.playerType == "Player 2"
    
    def checkGameState(self):
        currentPlayer = self.players[self.currentPlayerIndex]
        if not currentPlayer.hand and not self.deck:
            if currentPlayer.topCards:
                currentPlayer.hand = currentPlayer.topCards
                currentPlayer.topCards = []
                if self.isSessionPlayer():
                    self.view.updatePlayerHandButtons(currentPlayer.hand)
                    self.view.updatePlayerTopCardButtons(currentPlayer.topCards)
                else:
                    self.view.updateOpponentHandButtons(currentPlayer.hand)
                    self.view.updateOpponentTopCardButtons(currentPlayer.topCards)
            elif currentPlayer.bottomCards:
                currentPlayer.hand = currentPlayer.bottomCards
                currentPlayer.bottomCards = []
                if self.isSessionPlayer():
                    self.view.updatePlayerHandButtons(currentPlayer.hand)
                    self.view.updatePlayerBottomCardButtons(currentPlayer.bottomCards)
                else:
                    self.view.updateOpponentHandButtons(currentPlayer.hand)
                    self.view.updateOpponentBottomCardButtons(currentPlayer.bottomCards)
            elif not currentPlayer.bottomCards:
                placeholder = ("", "", False, False)
                currentPlayer.hand.append(placeholder)
                self.view.pickUpPileButton.setDisabled(True)
                self.view.placeButton.setDisabled(True)
                for button in self.playCardButtons:
                    button.setDisabled(True)
                print(f"{currentPlayer.name} wins!")
                self.gameOver = True

    def updatePlayableCards(self):
        currentPlayer = self.players[self.currentPlayerIndex]
        handIndex = 0  # To keep track of the actual card index in the player's hand

        for i in range(self.view.playerHandLayout.count()):
            item = self.view.playerHandLayout.itemAt(i)
            if item is None:
                continue
            lbl = item.widget()
            if lbl is None or (isinstance(lbl, QLabel) and lbl.pixmap() is None):  # Check if it's the spacer
                continue  # Skip the spacer

            if handIndex >= len(currentPlayer.hand):
                break  # Prevent index out of range error

            handCard = currentPlayer.hand[handIndex]
            if handCard[0] in ['2', '10'] or handCard[3] or self.isCardPlayable(handCard):
                lbl.setEnabled(True)
            else:
                lbl.setEnabled(False)
            
            handIndex += 1
        
    def sendGameState(self):
        if self.connection:
            data = self.serializeGameState()
            if isinstance(self.connection, Server):
                self.connection.sendToClient(data)
            else:
                self.connection.sendToServer(data)
            if self.gameOver:
                data = {
                    'action': 'gameOver',
                    'winner': self.players[self.currentPlayerIndex].name
                }
                if isinstance(self.connection, Server):
                    self.connection.sendToClient(data)
                else:
                    self.connection.sendToServer(data)

    def receiveGameState(self, data):
        self.deserializeGameState(data)
        if self.pile and self.pile[-1][0] == "2":
            pass
        elif self.pile and self.pile[-1][0] == "10":
            self.pile.clear()
            self.view.pileLabel.setText("Bombed!!!")
        else:
            self.view.placeButton.setText("Select a Card")
            self.view.pickUpPileButton.setEnabled(True)

    def serializeGameState(self):
        return {
            'action': 'playCard',
            'players': [
                {
                    'hand': self.players[0].hand,
                    'topCards': self.players[0].topCards,
                    'bottomCards': self.players[0].bottomCards
                },
                {
                    'hand': self.players[1].hand,
                    'topCards': self.players[1].topCards,
                    'bottomCards': self.players[1].bottomCards
                }
            ],
            'deck': self.deck,
            'pile': self.pile,
            'seven': self.sevenSwitch,
            'currentPlayerIndex': self.currentPlayerIndex,
        }

    def deserializeGameState(self, data):
        self.deck = data['deck']
        self.pile = data['pile']
        self.currentPlayerIndex = data['currentPlayerIndex']
        self.sevenSwitch = data['seven']
        self.players[0].hand = data['players'][0]['hand']
        self.players[0].topCards = data['players'][0]['topCards']
        self.players[0].bottomCards = data['players'][0]['bottomCards']
        self.players[1].hand = data['players'][1]['hand']
        self.players[1].topCards = data['players'][1]['topCards']
        self.players[1].bottomCards = data['players'][1]['bottomCards']
        self.communicator.updateUISignal.emit()
    
    def startHostServerThread(self):
        thread = threading.Thread(target=self.connection.handleClient, daemon=True)
        self.threads.append(thread)
        thread.start()

    def startClientServerThread(self):
        thread = threading.Thread(target=self.connection.handleServer, daemon=True)
        self.threads.append(thread)
        thread.start()

    def disconnect(self):
        self.gameOver = True
        self.closeThreads()
        if self.connection:
            self.connection.close()

    def closeThreads(self):
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)
    
    def closeConnections(self):
        if self.connection:
            self.connection.close()
       
def main():
    global scalingFactorWidth
    global scalingFactorHeight
    app = QApplication(sys.argv)
    app.setStyleSheet(Dark)
    screen = app.primaryScreen()
    screenSize = screen.size()
    screenWidth = screenSize.width()
    screenHeight = screenSize.height()
    scalingFactorWidth = screenWidth / 1920
    scalingFactorHeight = screenHeight / 1080
    communicator = SignalCommunicator()
    mainWindow = HomeScreen(communicator)  # Create the main window
    mainWindow.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()