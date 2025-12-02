import json
import os, asyncio

import traceback
import httpx
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from fastapi.responses import FileResponse # UPDATED: To serve the HTML file
from fastapi.staticfiles import StaticFiles # NEW: To serve static files (CSS, JS)
from sqlalchemy.orm import Session
from typing import List, Dict
from collections import Counter
from starlette.concurrency import run_in_threadpool
from collections import Counter
import models, schemas, auth
from database import engine, Base, get_db, SessionLocal
# from ml_model import analyze_emotion 
# from content_moderation import is_toxic
from summarizer import generate_summary_async , generate_mood_async

# from dotenv import load_dotenv
# load_dotenv()

# Create tables in the database if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Real-Time Affective Chatroom")

# --- Static Files Setup ---
STATIC_DIR = "static"

# NEW: Ensure the static directory exists before trying to mount it.
# This prevents the 'RuntimeError: Directory 'static' does not exist' on first run.
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

# Mount the 'static' directory to serve CSS and JS files
# This tells FastAPI that any request to a path starting with /static
# should be looked for in a directory named 'static' in the root.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# --- Anti-Spam (Rate Limiting) ---
message_timestamps: Dict[str, List[datetime]] = {}
MESSAGE_LIMIT = 5
TIME_WINDOW = timedelta(seconds=10)



# --- IMPROVED Connection Manager (Debugging Version) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user: str):
        self.active_connections[user] = websocket
        print(f"[Manager] ✅ User '{user}' connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, user: str):
        if user in self.active_connections:
            del self.active_connections[user]
            print(f"[Manager] ❌ User '{user}' disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        count = len(self.active_connections)
        print(f"[Manager] 📢 Broadcasting to {count} users...")
        
        if count == 0:
            print("[Manager] ⚠️ WARNING: No active connections found! The user might have disconnected.")
            return

        # Create a list of broken connections to remove
        broken_connections = []

        for user, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
                print(f"[Manager] ➡️ Sent to {user}")
            except Exception as e:
                print(f"[Manager] 🔴 FAILED to send to {user}: {e}")
                broken_connections.append(user)
        
        # Clean up broken connections
        for user in broken_connections:
            self.disconnect(user)

    async def send_private_message(self, message: str, user: str):
        if user in self.active_connections:
            try:
                await self.active_connections[user].send_text(message)
            except Exception as e:
                print(f"[Manager] 🔴 Failed to send private message to {user}: {e}")
                self.disconnect(user)
manager = ConnectionManager()



def _update_message_emotion_in_db(message_id: int, emotion: str) -> bool:
    """
    A SYNCHRONOUS, BLOCKING function to be run in a threadpool.
    It creates its own DB session, updates one message, and closes the session.
    Returns True on success, False on failure.
    """
    db = None
    try:
        print(f"[Task {message_id}]: DB-Thread: Creating new DB session...")
        db = SessionLocal()
        print(f"[Task {message_id}]: DB-Thread: Querying for message...")
        db_message = db.query(models.Message).filter(models.Message.id == message_id).first()
        
        if db_message:
            print(f"[Task {message_id}]: DB-Thread: Message found, updating emotion to {emotion}...")
            db_message.emotion = emotion
            db.commit()
            print(f"[Task {message_id}]: DB-Thread: DB update complete.")
            return True
        else:
            print(f"[Task {message_id}]: DB-Thread: ERROR - Message ID {message_id} not found in DB.")
            return False
            
    except Exception as e:
        print(f"[Task {message_id}]: DB-Thread: ERROR - Exception during DB update: {e}")
        if db:
            db.rollback()
        traceback.print_exc()
        return False
    finally:
        if db:
            db.close()
            print(f"[Task {message_id}]: DB-Thread: DB session closed.")

async def update_emotion(message_id: int, text: str):
    """
    ASYNC Background Task:
    1. Calls the slow emotion API (async).
    2. Calls the blocking DB update in a threadpool (async-aware).
    3. Broadcasts the emotion update to all clients (async).
    """
    print(f"[Task {message_id}]: Starting emotion update for: '{text}'")
    
    # 1. Call the slow emotion API (Async)
    EMOTION_API_URL = os.environ.get("EMOTION_API_URL")
    emotion = "unknown"
    
    if not EMOTION_API_URL:
        print(f"[Task {message_id}]: ERROR - EMOTION_API_URL is not set!")
        return

    try:
        print(f"[Task {message_id}]: Calling API: {EMOTION_API_URL}")
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{EMOTION_API_URL}/analyze", 
                json={"text": text},
                timeout=30.0
            )
        
        if response.status_code == 200:
            emotion = response.json().get("emotion", "unknown")
            print(f"[Task {message_id}]: API call SUCCESS, emotion: {emotion}")
        else:
            print(f"[Task {message_id}]: ERROR - API call failed with status: {response.status_code}")
            return # Stop if API call fails
            
    except Exception as e:
        print(f"[Task {message_id}]: ERROR - Exception during API call: {e}")
        traceback.print_exc()
        return # Stop if API call fails

    # 2. Update the message in the DB (Run blocking code in threadpool)
    print(f"[Task {message_id}]: Handing off to DB thread...")
    db_success = await run_in_threadpool(_update_message_emotion_in_db, message_id, emotion)
    
    if not db_success:
        print(f"[Task {message_id}]: Stopping task, DB update failed.")
        return # Stop if DB update failed

    # 3. Broadcast *only* the update (Async)
    try:
        update_data = {
            "type": "emotion_update",
            "message_id": message_id,
            "emotion": emotion
        }
        print(f"[Task {message_id}]: Broadcasting emotion update...")
        await manager.broadcast(json.dumps(update_data))
        print(f"[Task {message_id}]: Broadcast complete. Task finished.")
    except Exception as e:
        print(f"[Task {message_id}]: ERROR - Exception during broadcast: {e}")
        traceback.print_exc()

# --- API Endpoints ---

# UPDATED: The root endpoint now serves the main index.html file
@app.get("/")
async def get_root():
    return FileResponse('index.html')

# NEW: Endpoint to serve the summary.html page
@app.get("/summary-page")
async def get_summary_page():
    return FileResponse('summary.html')

@app.post("/signup", response_model=schemas.UserOut)
def signup(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.username == user_in.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed = auth.hash_password(user_in.password)
    user = models.User(username=user_in.username, password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@app.post("/login", response_model=schemas.Token)
def login(form_data: schemas.UserCreate, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    access_token = auth.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user



@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket, 
    # background_tasks: BackgroundTasks,  <-- REMOVE THIS
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    # 1. Authenticate user
    try:
        user = auth.get_user_from_token(token, db)
        if not user: raise HTTPException(status_code=401)
    except:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    await websocket.accept()
        
    # 2. Connect user and announce entry
    await manager.connect(websocket, user.username)
    join_announcement = json.dumps({
        "type": "chat_message", 
        "id": f"system-{datetime.utcnow().isoformat()}",
        "username": "System", 
        "content": f"{user.username} has joined the chat.",
        "timestamp": datetime.utcnow().isoformat(),
        "emotion": "neutral"
    })
    await manager.broadcast(join_announcement)
    
    try:
        while True:
            # 3. Wait for a new message
            data = await websocket.receive_text()
            now = datetime.utcnow()

            # 4. Check for Mute / Rate Limiting
            if user.is_muted:
                await manager.send_private_message(json.dumps({
                    "type": "system_alert", "content": "You are currently muted and cannot send messages."
                }), user.username)
                continue
            
            # 5. STEP 1: MANDATORY TOXICITY CHECK
            TOXICITY_API_URL = os.environ.get("TOXICITY_API_URL")
            is_message_toxic = False
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{TOXICITY_API_URL}/analyze", 
                        json={"text": data},
                        timeout=30.0 
                    )
                    if response.status_code == 200:
                        is_message_toxic = response.json().get("is_toxic", False)
            except Exception as e:
                print(f"Error calling toxicity API: {e}")

            if is_message_toxic:
                # ... (toxicity logic remains the same) ...
                user.warning_count += 1
                warning_msg = f"Message blocked. Warning {user.warning_count}."
                if user.warning_count >= 3:
                     user.is_muted = True
                db.commit()
                await manager.send_private_message(json.dumps({
                    "type": "system_alert", "content": warning_msg
                }), user.username)
                continue 

            # 6. STEP 2: SAVE & BROADCAST IMMEDIATELY
            db_message = models.Message(user_id=user.id, content=data, emotion="unknown")
            db.add(db_message)
            db.commit()
            db.refresh(db_message)
            
            message_data = {
                "type": "chat_message",
                "id": db_message.id,
                "username": user.username,
                "content": db_message.content,
                "timestamp": db_message.timestamp.isoformat(),
                "emotion": db_message.emotion
            }
            await manager.broadcast(json.dumps(message_data))

            print(f"[WebSocket]: Creating ASYNC task for message ID {db_message.id}")

            # 7. STEP 3: RUN SLOW EMOTION CHECK (THE FIX)
            # Use asyncio.create_task instead of background_tasks
            asyncio.create_task(update_emotion(db_message.id, data))

    except WebSocketDisconnect:
        manager.disconnect(user.username)
        # ... (disconnect logic) ...
    finally:
        if user and user.username in manager.active_connections:
            manager.disconnect(user.username)

# --- Data Endpoints (Unchanged) ---
@app.get("/messages", response_model=List[schemas.MessageOut])
def get_messages(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    messages = db.query(models.Message).order_by(models.Message.timestamp.asc()).all()
    result = []
    for msg in messages:
        if msg.user:
            result.append(schemas.MessageOut(
                id=msg.id, user_id=msg.user_id, content=msg.content,
                timestamp=msg.timestamp, username=msg.user.username,
                emotion=msg.emotion
            ))
    return result

# # --- UPDATED /mood ENDPOINT ---
# @app.get("/mood", response_model=schemas.MoodOut)
# async def get_overall_mood(
#     db: Session = Depends(get_db),
#     current_user: models.User = Depends(auth.get_current_user)
# ):
#     # 1. Fetch recent messages (e.g., last 30 for better context)
#     recent_messages = db.query(models.Message).order_by(models.Message.timestamp.desc()).limit(30).all()
#     recent_messages.reverse()

#     if not recent_messages:
#         return schemas.MoodOut(mood="neutral")

#     # 2. Format messages into a transcript for the LLM
#     transcript = "\n".join(
#         f"{msg.user.username}: {msg.content}" 
#         for msg in recent_messages if msg.user
#     )

#     # 3. Call the new LLM-based mood analysis function
#     dominant_mood = await generate_mood_async(transcript)
    
#     return schemas.MoodOut(mood=dominant_mood)


# --- UPDATED /mood ENDPOINT (No LLM) ---
@app.get("/mood", response_model=schemas.MoodOut)
async def get_overall_mood(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    # 1. Fetch recent messages (e.g., last 30)
    recent_messages = db.query(models.Message).order_by(models.Message.timestamp.desc()).limit(30).all()

    if not recent_messages:
        return schemas.MoodOut(mood="neutral")

    # 2. Create a list of all emotions from these messages
    # We will ignore "unknown" and "neutral" so they don't
    # accidentally win the vote.
    emotion_list = [
        msg.emotion 
        for msg in recent_messages 
        if msg.emotion and msg.emotion not in ["unknown", "neutral"]
    ]

    # 3. If the list is empty (all messages were neutral/unknown),
    # just return "neutral".
    if not emotion_list:
        return schemas.MoodOut(mood="neutral")

    # 4. Use Counter to find the most common emotion (the "majority vote")
    # Counter(emotion_list) creates a dict like {'joy': 5, 'anger': 2}
    # .most_common(1) gets the top one: [('joy', 5)]
    # [0][0] extracts the emotion name: 'joy'
    try:
        dominant_mood = Counter(emotion_list).most_common(1)[0][0]
    except IndexError:
        # This happens if the list was empty, but we already checked
        dominant_mood = "neutral"
    
    return schemas.MoodOut(mood=dominant_mood)


# --- Summary Endpoint (Unchanged) ---
@app.get("/summary", response_model=schemas.SummaryOut)
async def get_chat_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    recent_messages = db.query(models.Message).order_by(models.Message.timestamp.desc()).limit(50).all()
    recent_messages.reverse() 

    if not recent_messages:
        return schemas.SummaryOut(summary="There are no recent messages to summarize.")

    transcript = "\n".join(
        f"{msg.user.username}: {msg.content}" 
        for msg in recent_messages if msg.user
    )

    summary_text = await generate_summary_async(transcript)
    
    return schemas.SummaryOut(summary=summary_text)

