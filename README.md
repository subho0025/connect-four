# Real-Time Multiplayer Connect Four with Adversarial AI

### Live Demo

[phantom-connect4.vercel.app](https://phantom-connect4.vercel.app)

## Overview
A full-stack, real-time multiplayer Connect Four web application engineered with a focus on high-performance backend architecture, concurrent state management, and algorithmic artificial intelligence. 

Originally conceived as an **Introduction To AI** course laboratory implementation, the backend is built entirely from scratch using **FastAPI** and **Asyncio WebSockets**, supporting instant matchmaking, private shareable rooms, and local gameplay. The AI engine implements adversarial search algorithms, optimized for highly efficient board evaluation to maintain responsive, real-time gameplay.

## Features

### Game Modes
* Human vs AI
* AI vs AI
* Random vs AI
* Multiplayer (Private Room)
* Multiplayer (Public Matchmaking)

### Multiplayer Features

**1. Public Matchmaking:** Players can join a matchmaking queue and get paired automatically with another player.

**2. Private Rooms:** Players can create a room and share the room ID with friends to play together.

**3. Real-Time Gameplay:** WebSockets are used to synchronize game state between players instantly without polling.

### AI Algorithms

**1.Alpha-Beta Pruning:** The AI uses Minimax with Alpha-Beta Pruning to efficiently search the game tree and select strong moves against human or AI opponents.

**2.Expectimax:** When playing against a Random Player, the AI switches to Expectimax to model probabilistic opponent behavior and maximize expected utility.

**3.Iterative Deepening:** Both search agents use iterative deepening under a configurable time limit to improve move quality while maintaining responsiveness.

## Core Features

### Real-Time WebSocket Architecture
* **Event-Driven Multiplayer:** Utilizes asynchronous WebSockets to maintain stateful, low-latency connections between clients.
* **Matchmaking & Private Rooms:** Custom connection manager handles global matchmaking queues and generates secure, concurrent private rooms for peer-to-peer play.
* **Defensive Concurrency:** Implemented strict error-handling blocks (`try/except` during broadcasting) and centralized memory cleanup (`clean_disconnect`) to gracefully manage simultaneous socket disconnections and "ghost" lobbies without crashing the server.
* **Stateful Disconnects (Forfeit Logic):** Acts as an automated referee during multiplayer matches. If a player drops their connection mid-game, the server instantly detects the severed socket, awards a forfeit victory to the remaining player, and broadcasts the finalized game state to cleanly resolve the UI.

### Adversarial AI Engine & Architecture
To maintain a fast, non-blocking game engine, the AI relies on highly modular, mathematically optimized search functions:

**1. Minimax with Alpha-Beta Pruning**
* **`get_alpha_beta_move(board)`:** The primary entry point for matches against human players or other deterministic AI agents. 
* **`max_value` & `min_value`:** Recursively explores the state-space tree to maximize the AI's score while simulating optimal opponent counter-play. Strictly prunes branches that fall outside the dynamic `alpha` and `beta` thresholds to drastically reduce computational load.

**2. Iterative Deepening Search (IDS) & Time Management**
* **Dynamic Depth Scaling & Variance:** Wraps the core search algorithms in an Iterative Deepening loop constrained by a dynamically generated `maxTime` parameter (randomized between 1.0 and 2.0 seconds per move). This ensures the AI progressively explores deeper levels of the tree, safely yields the best-evaluated move upon timeout.

**3. Expectimax Search**
* **`get_expectimax_move(board)`:** A probabilistic search algorithm deployed specifically when the AI plays against "Random" opponents. 
* **`exp_chance_value`:** Instead of assuming perfect optimal play from the opponent, this calculates the expected utility (average outcome) of all possible valid moves a random agent could make, allowing the AI to take calculated risks.

**4. Heuristic Evaluation & Optimization**
* **`evaluation_function(board)`:** Scans the board across all four axes (horizontal, vertical, positive diagonal, negative diagonal) using a sliding 4-slot window mechanism (`evaluate_windows`).
* **Weighted Scoring:** Applies granular heuristic weights (`evaluate_score`) to non-terminal states (e.g., heavily penalizing the opponent having 3-in-a-row while heavily rewarding its own 4-in-a-row).
* **Heuristic Move Ordering:** The `get_valid_moves(board)` function is hardcoded to evaluate the center columns first (`[3, 2, 4, 1, 5, 0, 6]`). This vastly increases the likelihood of finding a high-value path early, leading to earlier branch pruning and massive performance gains.

### Backend & State Management
* **Stateless vs. Stateful Routing:** Seamlessly bridges stateless HTTP REST endpoints (for local AI games) with stateful WebSocket connections (for multiplayer).
* **Concurrency & Race Condition Mitigation:** Leverages `asyncio.Lock` to safely govern access to shared global in-memory states, including the `deque`-based matchmaking waiting queue. This strictly prevents race conditions, ensuring thread-safe operations during simultaneous WebSocket connections, sudden disconnections, and rapid state mutations.
* **Custom Vanilla JS Diffing:** The frontend avoids heavy frameworks by using a custom, lightweight DOM diffing engine to update the board state purely through JavaScript, keeping the main thread free for networking.

## Tech Stack
* **Backend:** Python3, FastAPI, Uvicorn, Asyncio
* **Frontend:** Vanilla JavaScript, HTML5, CSS3
* **Networking:** WebSockets, REST APIs
* **Deployment:** Vercel(Frontend), Render(Backend)

## Running Locally

To run this project on your local machine:

**1. Clone the repository**

```bash
git clone https://github.com/subho0025/connect-four.git
cd connect-four
```

**2. Set up a Python Virtual Environment**

```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install Dependencies**

```bash
pip install -r requirements.txt
```

**4. Start the Backend Server**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**5. Launch the Client**

Simply open index.html in your preferred web browser, or serve it using a lightweight local server:
```bash
python3 -m http.server 5500
```
Then navigate to http://localhost:5500 in your browser.

## Future Road Map

* Migration from in-memory data structures (dict) to a persistent database (PostgreSQL)
* User authentication
* Match history
* Elo-based Ranking and Leaderboards
* Redis-backed matchmaking
* Spectator mode
* Ranked matchmaking
* Docker deployment

## Scalability Notes

The current implementation stores active games and matchmaking state in server memory:

games = {}

This design is simple and effective for current single server deployment.

For horizontal scaling, active game state and matchmaking queues could be migrated to:

* Redis
* PostgreSQL

allowing multiple backend instances to serve players simultaneously.
