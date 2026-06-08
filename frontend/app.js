const API = "https://connect-four-backend-ud48.onrender.com/game";
const WS = "wss://connect-four-backend-ud48.onrender.com/ws";

let client = { id: null, mode: null, pNum: 1, ws: null };

const $ = id => document.getElementById(id);
const show = id => document.querySelectorAll('.screen').forEach(s => s.classList.toggle('active', s.id === `screen-${id}`));

const showError = (msg) => {
    let el = $('error-msg');
    if (!el) {
        el = document.createElement('div');
        el.id = 'error-msg';
        el.style = 'position: fixed; top: 20px; left: 50%; transform: translateX(-50%); color: white; background: #e74c3c; padding: 10px 20px; border-radius: 5px; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.2); z-index: 1000; transition: opacity 0.3s;';
        document.body.appendChild(el);
    }
    el.innerText = msg;
    el.style.display = 'block';
    setTimeout(() => el.style.display = 'none', 3000);
};

const api = async (path, method = "GET", body = null) => {
    const res = await fetch(`${API}${path}`, {
        method,
        headers: body ? { "Content-Type": "application/json" } : undefined,
        body: body ? JSON.stringify(body) : null
    });
    const data = await res.json();
    
    if (!res.ok || data.type === "error") { 
        const errorMsg = data.detail || data.message || "An unknown error occurred";
        showError(errorMsg); 
        throw new Error(errorMsg); 
    }
    return data;
};

function goMenu() {
    if (client.ws) { client.ws.close(); client.ws = null; }
    else {api(`/${client.id}/delete`, 'DELETE').catch(()=>{})};
    client.id= null;
    client.mode= null;
    client.pNum= 1;
    show('menu');
}

async function startLocalGame(p1, p2) {
    client.mode = p1 === "ai" ? "ai_vs_ai" : (p1 === "human" ? "human_vs_ai" : "random_vs_ai");
    client.pNum = 1; 
    
    const data = await api("", "POST", { player1: p1, player2: p2 });
    client.id = data.id;
    updateBoard(await api(`/${client.id}/state`));
    show('game');
}

async function makeMove(col) {
    try {
        if (client.ws) {
            client.ws.send(JSON.stringify({ type: "move", col }));
        } else {
            updateBoard(await api(`/${client.id}/move/${col}`, "POST"));
        }
    } catch(e) {}
}

async function aiNextMove() {
    try { updateBoard(await api(`/${client.id}/ai-move`, "POST")); } catch(e) {}
}

async function randomMove() {
    try { updateBoard(await api(`/${client.id}/random-move`, "POST"));} catch(e) {}
}

async function restartGame() {
    try { updateBoard(await api(`/${client.id}/restart`, "POST")); } catch(e) {}
}

function findPublicMatch() {
    show('loading');
    $('loading-text').innerText = "Finding match...";
    client.ws = new WebSocket(`${WS}/find-match`);
    client.ws.onmessage = message => {
        const data = JSON.parse(message.data);
        if (data.type === "match found") {
            client.ws.close();
            connectWS(data.id); }
    };
}

async function createPrivateMatch() {
    const data = await api("", "POST", { player1: "human", player2: "human" });
    show('loading');
    $('loading-text').innerText = `Room ID: ${data.id}\nShare this ID with your friend.`;
    connectWS(data.id);
}

function joinPrivateRoom() {
    const id = $("room-id-input").value.trim();
    if (id) connectWS(id);
    else showError("Please enter a Room ID");
}

function connectWS(id) {
    client.id = id;
    client.mode = "multiplayer";
    client.ws = new WebSocket(`${WS}/${id}`);

    client.ws.onclose = () => {
        if ($('screen-loading').classList.contains('active')) {
            showError("Server disconnected unexpectedly. Please try again.");
            goMenu();
        }
    };

    client.ws.onmessage = message => {
        const data = JSON.parse(message.data);
        
        if (data.type === "join confirmation") {
            client.pNum = data.player;
            updateBoard(data.state);
            show('game');
        }
        else if (data.type === "state") {
            updateBoard(data);
        }
        else if (data.type === "error") {
            showError(data.message);
        }
        else if (data.type === "disconnection") {
            showError("Opponent disconnected!");
            updateBoard(data);
        }
    };
}

function updateBoard(s) {
    const board = $("board");
    
    if (board.children.length === 0) {
        for (let r = 0; r < 6; r++) {
            for (let c = 0; c < 7; c++) {
                const cell = document.createElement("div");
                cell.className = "cell";
                cell.id = `cell-${r}-${c}`;
                board.appendChild(cell);
            }
        }
    }
    
    s.board.forEach((row, r) => {
        row.forEach((val, c) => {
            const cell = $(`cell-${r}-${c}`);
            
            if (val === 1 && !cell.classList.contains('p1')) {
                cell.classList.add('p1');
            } else if (val === 2 && !cell.classList.contains('p2')) {
                cell.classList.add('p2');
            } else if (val === 0) {
                cell.className = 'cell'; 
            }

            cell.onclick = !s.game_over ? () => makeMove(c) : null;
        });
    });

    const status = $("status");
    const aiBtn = $("ai-next-btn");
    const randomBtn = $("random-btn")
    const restartBtn = $("restart-btn");
    
    aiBtn.style.display = "none";
    randomBtn.style.display= "none";
    restartBtn.style.display = client.mode !== "multiplayer" ? "inline-block" : "none";

    if (s.game_over) {
        if (!s.winner) {
            status.innerText = "It's a Draw!";
        } else if (client.mode === "ai_vs_ai") {
            status.innerText = `AI ${s.winner} Wins!`;
        } else if (client.mode === "random_vs_ai"){
            if (s.winner===1){
                status.innerText = "Random Player Wins";
            }else{
                status.innerText = "AI Wins"
            }
        } else {
            status.innerText = s.winner === client.pNum ? "You Win!" : "You Lost!";
        }
    } else {
        if (client.mode === "multiplayer") {
            status.innerText = s.current_turn === client.pNum ? "Your Turn" : "Opponent's Turn";
        } else if (client.mode === "ai_vs_ai") {
            status.innerText = `AI ${s.current_turn} is thinking...`;
            aiBtn.style.display = "inline-block";
        } else if (client.mode === "random_vs_ai") {
            status.innerText = s.current_turn===1 ? "Random Player Turn" : "AI is thinking...";
            if (s.current_turn === 1) randomBtn.style.display = "inline-block";
            else aiBtn.style.display = "inline-block";
        } else if (client.mode === "human_vs_ai") {
            status.innerText = s.current_turn === 1 ? "Your Turn (Click a column)" : "AI is thinking...";
            if (s.current_turn === 2) aiBtn.style.display = "inline-block";
        }
    }
}

window.addEventListener("beforeunload", () => {
    if (client.id && !client.ws) {
        navigator.sendBeacon(`${API}/${client.id}/delete`);
    }
});