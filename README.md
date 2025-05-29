# Palace Card Game

A cross-platform desktop application built with PySide6 and qdarktheme that lets you play the classic “Palace” card game locally against AI opponents or online with friends.

---

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Usage](#usage)
4. [Code Overview](#code-overview)
5. [Directory Structure](#directory-structure)
6. [Configuration & Assets](#configuration--assets)

---

## Features

* **Local Play vs. AI**: Choose 2–4 player modes with configurable AI difficulty levels (Easy, Medium, Hard, Impossible).&#x20;
* **Online Multiplayer**: Host or join games over LAN using a simple TCP socket protocol, synchronized in real time.&#x20;
* **Modern UI**: Dark/light theming via qdarktheme with custom color overrides for buttons, dialogs, and pop-ups.&#x20;
* **Dynamic Layouts**: Adaptive card layouts for 2, 3, or 4 players, complete with bottom, top, and hand zones rendered using Qt widgets.&#x20;
* **Robust Networking**: JSON-based message protocol handles player actions (card updates, game state, play-again counters) and disconnection gracefully.&#x20;
* **Game Over & Replay**: End-of-game dialog shows the winner, tracks “play again” votes, and allows a seamless rematch or return to main menu.&#x20;

---

## Prerequisites

* **Python 3.9+**
* **PySide6** ≥ 6.0
* **qdarktheme** for dark/light UI styling
* Standard library modules: `socket`, `threading`, `json`, `random`, `time`

Install dependencies via pip:

```bash
pip install PySide6 qdarktheme
```

---

## Usage

### Launching the App

```bash
python main.py
```

### Main Menu

* **Play**: Start offline game setup.
* **Play Online**: Host or join a LAN game.
* **Rules**: View game rules (placeholder).
* **Exit**: Quit application.

### Offline Play

1. Select number of players (2–4) and AI difficulty.
2. Click **OK** to deal cards and enter the game view.
3. Play turns by selecting valid cards; pick up pile when no play is possible.
4. Top-card confirmation and placement are handled via on-screen buttons.
5. Game Over dialog appears when a player wins.

### Online Play

1. **Host Game**: Opens a lobby listening on port 12345. Players receive assigned indices and nicknames.
2. **Join Game**: Enter host IP and nickname to connect.
3. Once ≥2 players are connected, host clicks **Start Game**.
4. Gameplay and state updates broadcast to all connected clients.
5. Disconnections and reconnects are handled gracefully; game layout adapts accordingly.

---

## Code Overview

All functionality is contained in `main.py`:

* **Styling & Utilities**

  * `Dark = qdarktheme.load_stylesheet(...)` defines custom styles for dark mode.
  * `centerDialog()` recenters dialogs over parent windows with optional offsets.&#x20;

* **Data Structures & Constants**

  * `RANKS` and `VALUES` map card faces to sorting and numeric values.
  * `CARD_WIDTH`, `CARD_HEIGHT`, `BUTTON_WIDTH`, `BUTTON_HEIGHT` define layout metrics.&#x20;

* **UI Components**

  * `HomeMenu`, `OfflineMenu`, `OnlineMenu`, `HostLobby`, `JoinLobby`, `GameView`, and `GameOverDialog` classes handle all screens.&#x20;
  * Layouts use `QVBoxLayout`, `QHBoxLayout`, and `QGridLayout` for flexible arrangement.&#x20;

* **Networking & Multiplayer**

  * `HostLobby` opens a TCP server on port 12345, assigns player indices, and manages client threads.
  * JSON messages (`action` fields) coordinate card updates, turn changes, and game events.&#x20;

* **Game Logic**

  * `AIPlayer` encapsulates AI behavior per difficulty, using controller callbacks for moves.
  * `OfflineGameView` initializes deck shuffling, deals cards, and spins up AI threads.&#x20;
  * `GameController` (imported or defined below) drives state transitions and signals UI updates.

---

## Directory Structure

```
palace-card-game/
├── main.py             # All application code
├── requirements.txt    # PySide6, qdarktheme
├── palaceData/         # Assets: icons, card images, rules text
│   ├── palaceIcon.ico
│   └── cards/… 
└── README.md
```

---

## Configuration & Assets

* **`palaceData/palaceIcon.ico`**: Window and dialog icon.
* **Card Images**: Place 56×84 PNGs in `palaceData/cards/`, named `A_hearts.png`, etc.
* **Optional Rules File**: `palaceData/rules.txt` (displayed via the Rules button).
