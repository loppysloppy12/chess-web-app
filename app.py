import streamlit as st
import chess
import chess.svg
import chess.engine
import os
import shutil

# ================= CONFIGURATION =================
st.set_page_config(page_title="Chess AI", layout="centered")

# ================= ENGINE LOGIC =================
def get_stockfish_path():
    """Finds the stockfish binary on Windows or Linux"""
    # 1. Check for local Windows file
    if os.path.exists("stockfish.exe"):
        return "stockfish.exe"
    
    # 2. Check system path (Linux/Streamlit Cloud)
    path = shutil.which("stockfish")
    if path:
        return path
    
    # 3. Common Linux paths fallback
    if os.path.exists("/usr/games/stockfish"):
        return "/usr/games/stockfish"
    
    return None

def get_engine():
    path = get_stockfish_path()
    if not path:
        st.error("Stockfish engine not found! If running locally, put stockfish.exe in the folder.")
        return None
    try:
        return chess.engine.SimpleEngine.popen_uci(path)
    except Exception as e:
        st.error(f"Engine Error: {e}")
        return None

# ================= STATE MANAGEMENT =================
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'history' not in st.session_state:
    st.session_state.history = []
if 'ai_side' not in st.session_state:
    st.session_state.ai_side = chess.BLACK

# ================= GAME LOGIC =================
def make_ai_move():
    if st.session_state.board.is_game_over(): return

    engine = get_engine()
    if engine:
        result = engine.play(st.session_state.board, chess.engine.Limit(time=0.5))
        st.session_state.board.push(result.move)
        st.session_state.history.append(f"AI: {result.move}")
        engine.quit()

def handle_move(move_str):
    try:
        move = chess.Move.from_uci(move_str)
        if move in st.session_state.board.legal_moves:
            st.session_state.board.push(move)
            st.session_state.history.append(f"You: {move}")
            
            if not st.session_state.board.is_game_over():
                if st.session_state.ai_side is not None and st.session_state.board.turn == st.session_state.ai_side:
                    make_ai_move()
            st.rerun()
        else:
            st.error("Illegal Move.")
    except:
        st.error("Invalid format. Use e2e4, g1f3, etc.")

def restart_game():
    st.session_state.board.reset()
    st.session_state.history = []
    if st.session_state.ai_side == chess.WHITE:
        make_ai_move()
    st.rerun()

# ================= UI =================
st.title("♟️ Chess AI")

# Sidebar
with st.sidebar:
    st.header("Settings")
    mode = st.radio("Mode", ["Play as White", "Play as Black", "Manual"])
    if st.button("New Game"):
        if mode == "Play as White": st.session_state.ai_side = chess.BLACK
        elif mode == "Play as Black": st.session_state.ai_side = chess.WHITE
        else: st.session_state.ai_side = None
        restart_game()

    st.write("---")
    st.write("**History:**")
    for m in st.session_state.history[-10:]:
        st.caption(m)

# Board Display
is_flipped = (st.session_state.ai_side == chess.WHITE)
board_svg = chess.svg.board(
    st.session_state.board, 
    size=350, 
    flipped=is_flipped,
    lastmove=st.session_state.board.peek() if st.session_state.board.move_stack else None
)
st.image(board_svg, use_column_width=False)

# Input
move = st.text_input("Enter Move (e.g. e2e4):", key="move_input")
if st.button("Submit Move"):
    handle_move(move)

# Status
if st.session_state.board.is_game_over():
    st.success(f"Game Over: {st.session_state.board.result()}")
elif st.session_state.board.is_check():
    st.warning("Check!")