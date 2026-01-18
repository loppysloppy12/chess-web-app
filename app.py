import streamlit as st
import chess
import chess.svg
import chess.engine
import os
import shutil

# ================= 1. PAGE CONFIG =================
st.set_page_config(page_title="Chess AI", page_icon="♟️", layout="centered")

# ================= 2. ENGINE SETUP =================
def get_stockfish_path():
    """Finds Stockfish on Windows (Local) or Linux (Cloud)"""
    # Check local Windows file
    if os.path.exists("stockfish.exe"):
        return "stockfish.exe"
    # Check system path (Linux/Cloud)
    path = shutil.which("stockfish")
    if path: return path
    # Check common Linux install locations
    if os.path.exists("/usr/games/stockfish"):
        return "/usr/games/stockfish"
    return None

def get_engine():
    path = get_stockfish_path()
    if not path:
        st.error("❌ Stockfish engine not found. Ensure 'packages.txt' contains 'stockfish'.")
        return None
    try:
        # Limit threads to 1 for cloud stability
        return chess.engine.SimpleEngine.popen_uci(path)
    except Exception as e:
        st.error(f"Engine Error: {e}")
        return None

# ================= 3. GAME LOGIC =================
# Initialize Session State (Memory)
if 'board' not in st.session_state:
    st.session_state.board = chess.Board()
if 'history' not in st.session_state:
    st.session_state.history = []
if 'ai_side' not in st.session_state:
    st.session_state.ai_side = chess.BLACK # Default: Human is White

def make_ai_move():
    """The Computer thinks and moves"""
    if st.session_state.board.is_game_over(): return

    engine = get_engine()
    if engine:
        # Think for 1.0 second (Smarter)
        result = engine.play(st.session_state.board, chess.engine.Limit(time=1.0))
        st.session_state.board.push(result.move)
        st.session_state.history.append(f"🤖 AI: {result.move}")
        engine.quit()

def restart_game(user_color):
    """Resets board and handles Auto-Start"""
    st.session_state.board.reset()
    st.session_state.history = []
    
    if user_color == "White":
        st.session_state.ai_side = chess.BLACK
    else:
        st.session_state.ai_side = chess.WHITE
    
    # CRITICAL: If Human is Black, AI (White) moves immediately!
    if st.session_state.ai_side == chess.WHITE:
        with st.spinner("🤖 Computer is thinking..."):
            make_ai_move()

def handle_user_move(move_str):
    """Processes the user's text input"""
    try:
        move = chess.Move.from_uci(move_str)
        if move in st.session_state.board.legal_moves:
            st.session_state.board.push(move)
            st.session_state.history.append(f"👤 You: {move}")
            
            # If game isn't over, AI moves
            if not st.session_state.board.is_game_over():
                with st.spinner("🤖 Computer is thinking..."):
                    make_ai_move()
            
            # Clear text input by rerunning (Streamlit trick)
            st.rerun()
        else:
            st.error(f"❌ Illegal move: {move_str}")
    except:
        st.error("❌ Invalid format. Use uci format (e.g., e2e4, g1f3)")

# ================= 4. UI LAYOUT =================
st.title("♟️ Chess AI Web")

# --- SIDEBAR (Controls) ---
with st.sidebar:
    st.header("⚙️ Game Settings")
    
    # Play Mode Selection
    mode = st.radio("Choose your side:", ["Play as White", "Play as Black"], index=0)
    
    # New Game Button
    if st.button("🔄 Start New Game", use_container_width=True):
        color = "White" if mode == "Play as White" else "Black"
        restart_game(color)
        st.rerun()

    st.divider()
    
    # Move History
    st.subheader("📜 History")
    history_container = st.container(height=300)
    with history_container:
        for move in reversed(st.session_state.history):
            st.text(move)

# --- MAIN AREA (Board & Input) ---

# 1. Determine Board Orientation
is_flipped = (st.session_state.ai_side == chess.WHITE)

# 2. Status Message
if st.session_state.board.is_game_over():
    res = st.session_state.board.result()
    msg = "Draw"
    if res == "1-0": msg = "White Wins!"
    elif res == "0-1": msg = "Black Wins!"
    st.success(f"🏆 GAME OVER: {msg}")
elif st.session_state.board.is_check():
    st.warning("⚠️ Check!")
else:
    turn = "White" if st.session_state.board.turn == chess.WHITE else "Black"
    st.info(f"👉 Current Turn: **{turn}**")

# 3. Draw Board
board_svg = chess.svg.board(
    st.session_state.board,
    size=400,
    flipped=is_flipped,
    lastmove=st.session_state.board.peek() if st.session_state.board.move_stack else None,
    check=st.session_state.board.king(st.session_state.board.turn) if st.session_state.board.is_check() else None
)
st.image(board_svg, use_column_width=False)

# 4. Input Form (Enter key submits)
st.write("### Make your move")
with st.form(key='move_form', clear_on_submit=True):
    col1, col2 = st.columns([3, 1])
    with col1:
        move_input = st.text_input("Enter move (e.g., e2e4):", key="input_move", label_visibility="collapsed", placeholder="e2e4")
    with col2:
        submit_btn = st.form_submit_button("Move")

    if submit_btn and move_input:
        handle_user_move(move_input)

# 5. Help / Analysis Log
with st.expander("ℹ️ How to play"):
    st.markdown("""
    - **Enter moves** using algebraic notation (e.g., `e2e4` moves Pawn from e2 to e4).
    - **Castling:** `e1g1` (Kingside) or `e1c1` (Queenside).
    - **Promotion:** `a7a8q` (Promote to Queen).
    - If you choose **Play as Black**, the AI will make the first move automatically.
    """)
