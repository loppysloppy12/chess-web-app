import streamlit as st
import chess
import chess.engine
import os
import shutil
from streamlit_chessboard import chessboard

# ================= 1. PAGE CONFIG =================
st.set_page_config(page_title="Chess AI", page_icon="♟️", layout="centered")

# Custom CSS to remove whitespace and make it look like an 'App'
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    h1 {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ================= 2. ENGINE SETUP =================
def get_stockfish_path():
    if os.path.exists("stockfish.exe"): return "stockfish.exe"
    path = shutil.which("stockfish")
    if path: return path
    if os.path.exists("/usr/games/stockfish"): return "/usr/games/stockfish"
    return None

def get_engine():
    path = get_stockfish_path()
    if not path:
        return None
    try:
        return chess.engine.SimpleEngine.popen_uci(path)
    except: return None

# ================= 3. STATE MANAGEMENT =================
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'ai_side' not in st.session_state:
    st.session_state.ai_side = chess.BLACK
if 'history' not in st.session_state:
    st.session_state.history = []

# ================= 4. LOGIC =================
def make_ai_move():
    if st.session_state.board.is_game_over(): return
    
    engine = get_engine()
    if engine:
        # Think for 0.5 seconds for speed
        result = engine.play(st.session_state.board, chess.engine.Limit(time=0.5))
        st.session_state.board.push(result.move)
        st.session_state.history.append(f"AI: {result.move}")
        engine.quit()

def restart_game(color):
    st.session_state.board.reset()
    st.session_state.history = []
    st.session_state.ai_side = chess.BLACK if color == "White" else chess.WHITE
    
    if st.session_state.ai_side == chess.WHITE:
        make_ai_move()
    st.rerun()

# ================= 5. THE UI =================
st.title("♟️ Chess AI")

# -- CONTROLS --
col1, col2 = st.columns([1, 1])
with col1:
    user_side = st.selectbox("Play As:", ["White", "Black"])
with col2:
    if st.button("🔄 New Game", use_container_width=True):
        restart_game(user_side)

# -- THE BOARD --
# Determine orientation
orientation = "white" if st.session_state.ai_side == chess.BLACK else "black"

# This component handles the Drag & Drop AND Clicks
# It returns the move ONLY when you finish the action
move_data = chessboard(
    st.session_state.board.fen(), 
    orientation=orientation, 
    key="game_board",
    width=350, # Optimized size for mobile
    height=350
)

# -- MOVE HANDLING --
if move_data:
    # 1. Parse the move from the UI component
    move_str = move_data["source"] + move_data["target"]
    move = chess.Move.from_uci(move_str)
    
    # 2. Check Promotion (Auto-Queen)
    if move_str in [m.uci()[:4] for m in st.session_state.board.legal_moves]:
        # If it's a legal move but missing promotion char, assume Queen
        move = chess.Move.from_uci(move_str + "q")

    # 3. Apply Move
    if move in st.session_state.board.legal_moves:
        # Only push if it's a new move (prevents loop)
        if st.session_state.board.fen() != move_data["fen"]:
            st.session_state.board.push(move)
            st.session_state.history.append(f"You: {move}")
            
            # AI Reply
            if not st.session_state.board.is_game_over():
                with st.spinner("AI Thinking..."):
                    make_ai_move()
            
            # Force refresh to update the visual board
            st.rerun()

# -- STATUS --
if st.session_state.board.is_game_over():
    res = st.session_state.board.result()
    msg = "Draw"
    if res == "1-0": msg = "White Wins!"
    elif res == "0-1": msg = "Black Wins!"
    st.success(f"🏆 {msg}")
elif st.session_state.board.is_check():
    st.error("Check!")

# -- HISTORY --
with st.expander("Move History"):
    for move in st.session_state.history:
        st.caption(move)
