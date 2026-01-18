import streamlit as st
import chess
import chess.engine
import os
import shutil
from streamlit_chessboard import chessboard

# ================= 1. CONFIGURATION =================
st.set_page_config(page_title="Chess AI", page_icon="♟️", layout="centered")

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
        st.error("Stockfish not found.")
        return None
    try:
        return chess.engine.SimpleEngine.popen_uci(path)
    except: return None

# ================= 3. STATE MANAGEMENT =================
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'ai_side' not in st.session_state:
    st.session_state.ai_side = chess.BLACK
if 'last_fen' not in st.session_state:
    st.session_state.last_fen = st.session_state.board.fen()

# ================= 4. LOGIC =================
def make_ai_move():
    """AI thinks and moves"""
    if st.session_state.board.is_game_over(): return
    
    engine = get_engine()
    if engine:
        # Think for 1 second
        result = engine.play(st.session_state.board, chess.engine.Limit(time=1.0))
        st.session_state.board.push(result.move)
        st.session_state.last_fen = st.session_state.board.fen() # Update sync state
        engine.quit()

def restart_game(color_name):
    st.session_state.board.reset()
    st.session_state.ai_side = chess.BLACK if color_name == "White" else chess.WHITE
    
    # If AI is White, it moves first
    if st.session_state.ai_side == chess.WHITE:
        make_ai_move()
    
    st.session_state.last_fen = st.session_state.board.fen()
    st.rerun()

# ================= 5. UI LAYOUT =================
st.title("♟️ Chess AI")

# Sidebar
with st.sidebar:
    st.header("Settings")
    mode = st.radio("Play As:", ["White", "Black"])
    if st.button("New Game"):
        restart_game(mode)

# Game Status
if st.session_state.board.is_game_over():
    res = st.session_state.board.result()
    st.success(f"Game Over: {res}")
elif st.session_state.board.is_check():
    st.warning("Check!")

# Determine Orientation
board_orientation = "white" if st.session_state.ai_side == chess.BLACK else "black"

# --- THE INTERACTIVE BOARD ---
# This component handles the clicks for us!
move_data = chessboard(
    st.session_state.board.fen(), 
    orientation=board_orientation, 
    key="board_component"
)

# --- HANDLE MOVES ---
# If the user made a move on the board, 'move_data' will contain the info
if move_data:
    # Get the move in UCI format (e.g., "e2e4")
    move_str = move_data["source"] + move_data["target"]
    
    # Check for promotion (simplistic: always promote to Queen if moving pawn to edge)
    # We essentially guess if it's a promotion based on the move
    move = chess.Move.from_uci(move_str)
    
    # If move is illegal (maybe it needs promotion char), try adding 'q'
    if move not in st.session_state.board.legal_moves:
        move = chess.Move.from_uci(move_str + "q")

    # Final Check and Apply
    if move in st.session_state.board.legal_moves:
        # Only apply if the board state hasn't already processed this move
        # (This prevents infinite loops of re-processing the same click)
        if st.session_state.board.fen() != move_data["fen"]: 
            st.session_state.board.push(move)
            
            # AI Reply
            if not st.session_state.board.is_game_over():
                 with st.spinner("Thinking..."):
                    make_ai_move()
            
            # Force reload to update the board component with AI's move
            st.rerun()
