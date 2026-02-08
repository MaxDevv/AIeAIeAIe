from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import os
from openai import OpenAI
import base64, random, time
import json_repair


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

peers = []
responded_users = set()
presenter_rotation_timer = None
current_presenter_index = 0
current_presenter = None

# Game state - persists across disconnects
game_participants = {}  # userId -> {username, peerId}
game_in_progress = False




# Initialize OpenAI client with OpenRouter
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=open("/home/max/Code/QuHacks/.env.apikey", "r").read()
)

userResponses = []
successPercentage = 0
startingPrompts = ["Your party is very very verrrry sleepy, and will die of sleep soon."]
promptHistory = [random.choice(startingPrompts)]

# Track pending video processing
pending_uploads = set()
all_responded_event_sent = False

# Ensure recordings directory exists
os.makedirs('recordings', exist_ok=True)

def extractResponse(videoFilePath):
    with open(videoFilePath, "rb") as video_file:
        b64Vid =  base64.b64encode(video_file.read()).decode('utf-8')
    response = client.chat.completions.create(
        model="google/gemini-3-flash-preview",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Provide a verbatim transcription of this video's audio and a short description of the item(s) presented in the video."
                    },
                    {
                        "type": "video_url",
                        "video_url": {
                            "url": f"data:video/mp4;base64,{b64Vid}"
                        }
                    }
                ]
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "video_analysis",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "transcription": {
                            "type": "string"
                        },
                        "items": {
                            "type": "array",
                            "items": {
                                "type": "string"
                            },
                            "minItems": 0,
                            "maxItems": 10
                        }
                    },
                    "required": ["transcription", "items"],
                    "additionalProperties": False
                }
            }
        },
        extra_body = {
                
        "generation_config": {
        "media_resolution": "MEDIA_RESOLUTION_HIGH"
        }
        }
    )
    return json_repair.loads(response.choices[0].message.content)


def cycle(currentSituation):
    global successPercentage
    
    sysPrompt = """
    You are an evil ai who has thrust these players into an intersting situation.
    Each player has been instructed to locate one or more items in thier home and come up with an action using these items.
    
    You are to devlop this situation into a new situation, you must do 3 things.
    1. Simulate then describe the actions of each player as thier solutions interact and collide (30 - 150 words), as a story of how the situation plays out.
    2. Then present a new sitation based on the events of the previous situation.
    3. How much to add or subtract to the players' winning percentage (a number determining how close the players are to winning; beating the scenario), you can add or subtract up to 20 percent, but you must return a positive or negeative number.
    """
    prompt = f"""
    The current situation: "{currentSituation}"
    
    {"\n".join([f"{i['name']}'s actions: {i['action']}, the items presented by the player: {i['items']}" for i in userResponses])}
    
    The players are {successPercentage}% of the way to winning."""
    
    response = client.chat.completions.create(
        model="google/gemini-2.5-flash",
        messages=[
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": sysPrompt
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "video_analysis",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "simulation_of_situation_evolution": {
                            "type": "string"
                        },
                        "new_situation": {
                            "type": "string"
                        },
                        "success_percentage_update": {
                            "type": "number",
                            "minimum": -20,
                            "maximum": 20
                        }
                    },
                    "required": ["simulation_of_situation_evolution", "new_situation", "success_percentage_update"],
                    "additionalProperties": False
                }
            }
        }
    )
    
    data = json_repair.loads(response.choices[0].message.content)
    
    promptHistory.append(data["new_situation"])
    successPercentage += data["success_percentage_update"]
    
    # Clear user responses for next round
    userResponses.clear()
    
    return data


@socketio.on('join-room')
def handleJoin(data):
    print("user joined: ", data)
    user_id = data.get('userId')
    username = data.get('username')
    
    # Store peer with all user info including peerId if provided
    peer_info = {
        'userId': user_id,
        'username': username,
        'peerId': data.get('peerId'),
        'sid': request.sid
    }
    # Remove existing entry for this user if any
    global peers, game_participants
    peers = [p for p in peers if p.get('userId') != user_id]
    peers.append(peer_info)
    
    # Add to game participants (persists across disconnects during game)
    if user_id and username:
        game_participants[user_id] = {
            'username': username,
            'peerId': data.get('peerId')
        }
    
    emit('all-peers', peers, broadcast=True)
    

@socketio.on('add-peer')
def handleAddPeer(data):
    print("[ADD-PEER] Received:", data)
    global peers, game_participants, current_presenter
    user_id = data.get('userId')
    username = data.get('username', 'Unknown')
    peer_id = data.get('peerId')
    
    print(f"[ADD-PEER] user_id={user_id}, peer_id={peer_id}, username={username}")
    
    # Find and update peer with peerId, or add if not exists
    found = False
    for peer in peers:
        if peer.get('userId') == user_id:
            peer['peerId'] = peer_id
            found = True
            print(f"[ADD-PEER] Updated existing peer")
            break
    
    # If peer not found, create new entry
    if not found:
        peers.append({
            'userId': user_id,
            'username': username,
            'peerId': peer_id,
            'sid': request.sid
        })
        print(f"[ADD-PEER] Created new peer entry")
    
    # ALWAYS update game_participants with peerId
    if user_id:
        game_participants[user_id] = {
            'username': username,
            'peerId': peer_id
        }
        print(f"[ADD-PEER] Updated game_participants: {game_participants}")
    
    # CRITICAL: Update current_presenter if this user is the current presenter
    if current_presenter and current_presenter.get('userId') == user_id:
        current_presenter['peerId'] = peer_id
        print(f"[ADD-PEER] Updated current_presenter peerId: {current_presenter}")
    
    emit('all-peers', peers)

@socketio.on('start-presenting')
def handlePresenting(data):
    global current_presenter, peers
    peer_id = data.get('peerId')
    user_id = data.get('userId')  # Need userId to know whose peerId this is
    
    # Update current_presenter with the peerId if this is the current presenter
    if current_presenter and peer_id:
        current_presenter['peerId'] = peer_id
        print(f"[START-PRESENTING] Updated current_presenter peerId: {peer_id}")
    
    # CRITICAL: Also update the peers list so all-peers has correct peerId
    if user_id and peer_id:
        for peer in peers:
            if peer.get('userId') == user_id:
                peer['peerId'] = peer_id
                print(f"[START-PRESENTING] Updated peers list for {user_id}: {peer_id}")
                break
    
    emit('user-presenting', peer_id, broadcast=True)
    emit('all-peers', peers, broadcast=True)

@socketio.on('get-all-peers')
def handleGetAllPeers():
    emit('all-peers', peers)

@socketio.on('stop-presenting')
def handle_stop():
    emit('presenter-stopped', broadcast=True)
    

@socketio.on('start-game')
def handleStartGame():
    global responded_users, readiness, game_participants, game_in_progress, pending_uploads, all_responded_event_sent
    
    # Reset state
    responded_users = set()
    current_presenter_index = 0
    readiness = {}
    game_in_progress = True
    pending_uploads = set()
    all_responded_event_sent = False
    userResponses.clear()
    
    # Build game_participants from current peers
    game_participants = {}
    for p in peers:
        uid = p.get('userId')
        if uid:
            game_participants[uid] = {
                'username': p.get('username', 'Unknown'),
                'peerId': p.get('peerId')
            }
    
    print(f"Starting game with {len(game_participants)} participants: {game_participants}")
    
    # Notify clients that game is starting with the prompt
    emit('starting-game', promptHistory[-1], broadcast=True)
    # Don't start presenter rotation yet - wait for prompt timer to finish

@socketio.on('prompt-timer-finished')
def handlePromptTimerFinished():
    """Called when the prompt timer finishes on the client side"""
    global game_in_progress
    print("Prompt timer finished - starting presenter rotation")
    if game_in_progress and current_presenter is None:
        start_presenter_rotation()

def run_ai_cycle_when_ready():
    """Wait for all videos to be processed then run AI cycle"""
    global all_responded_event_sent
    
    # Wait up to 60 seconds for all uploads to complete
    for _ in range(60):
        if len(pending_uploads) == 0:
            break
        print(f"Waiting for {len(pending_uploads)} videos to be processed...")
        socketio.sleep(1)
    
    all_responded_event_sent = False
    process_ai_cycle()

def start_presenter_rotation():
    global current_presenter_index, current_presenter, game_participants, all_responded_event_sent
    
    # Use game_participants instead of peers (persists across disconnects)
    remaining_participants = [
        {'userId': uid, 'username': info['username'], 'peerId': info.get('peerId')}
        for uid, info in game_participants.items()
        if uid not in responded_users
    ]
    
    print(f"Starting presenter rotation. Total participants: {len(game_participants)}, Remaining: {len(remaining_participants)}")
    print(f"All participants: {game_participants}")
    
    if not remaining_participants:
        # All users have presented (mark as responded)
        print("All users have presented!")
        current_presenter = None
        all_responded_event_sent = True
        # Notify clients to go to thinking page
        socketio.emit('all-users-responded')
        # Start AI processing in background (will wait for all videos)
        socketio.start_background_task(run_ai_cycle_when_ready)
        return
    
    # Select next presenter (round-robin)
    presenter = remaining_participants[0]
    
    # Get latest peerId from game_participants
    uid = presenter.get('userId')
    latest_peer_id = game_participants.get(uid, {}).get('peerId')
    
    # Update current_presenter with latest peerId
    current_presenter = {
        'userId': uid,
        'username': presenter.get('username'),
        'peerId': latest_peer_id
    }
    current_presenter_index = (current_presenter_index + 1) % len(remaining_participants)
    
    print(f"[START-ROTATION] Selected presenter: {current_presenter}")
    
    # Mark as responded
    responded_users.add(uid)
    
    # Broadcast the next presenter (to all connected clients)
    socketio.emit('next-presenter', current_presenter)
    
    # Schedule next rotation in 30 seconds using socketio's background task
    socketio.start_background_task(rotation_timer_task)

def process_ai_cycle():
    """Process AI cycle after all users have responded"""
    global successPercentage
    
    print("Starting AI processing...")
    
    # Wait a moment for any final uploads to complete
    socketio.sleep(5)
    
    try:
        print(f"Running AI cycle with {len(userResponses)} responses")
        print(f"Current situation: {promptHistory[-1]}")
        
        if len(userResponses) == 0:
            print("No user responses to process")
            # Still need to continue the game - emit ready with same prompt
            socketio.emit('ai-processing-complete', {
                'new_prompt': promptHistory[-1],
                'success_percentage': successPercentage
            })
            return
        
        # Run the cycle
        result = cycle(promptHistory[-1])
        
        print(f"AI cycle complete. New situation: {promptHistory[-1]}")
        print(f"Success percentage: {successPercentage}%")
        
        # Notify all clients that AI processing is done
        socketio.emit('ai-processing-complete', {
            'new_prompt': promptHistory[-1],
            'success_percentage': successPercentage,
            'simulation': result.get('simulation_of_situation_evolution', '')
        })
    except Exception as e:
        print(f"Error in AI cycle: {e}")
        import traceback
        traceback.print_exc()
        # Still emit completion so clients don't get stuck
        socketio.emit('ai-processing-complete', {
            'new_prompt': promptHistory[-1],
            'success_percentage': successPercentage,
            'error': str(e)
        })

def rotation_timer_task():
    """Background task that waits 30 seconds then triggers next rotation"""
    print("Rotation timer started - waiting 30 seconds...")
    socketio.sleep(30)  # Use socketio.sleep instead of time.sleep
    print("Rotation timer finished - triggering next presenter")
    start_presenter_rotation()

@socketio.on('user-finished-responding')
def handleUserFinished(data):
    user_id = data.get('userId')
    if user_id:
        responded_users.add(user_id)

@socketio.on('get-current-presenter')
def handleGetCurrentPresenter():
    global current_presenter, game_participants
    print(f"[GET-CURRENT-PRESENTER] requested by {request.sid}")
    if current_presenter:
        # Get latest peerId from game_participants
        user_id = current_presenter.get('userId')
        latest_peer_id = game_participants.get(user_id, {}).get('peerId')
        print(f"[GET-CURRENT-PRESENTER] current_presenter userId={user_id}, latest peerId={latest_peer_id}")
        
        response = {
            'userId': user_id,
            'username': current_presenter.get('username'),
            'peerId': latest_peer_id  # Use latest from game_participants
        }
        print(f"[GET-CURRENT-PRESENTER] Sending: {response}")
        emit('next-presenter', response)
    else:
        print("[GET-CURRENT-PRESENTER] No current presenter to send")

readiness = {}

@socketio.on('disconnect')
def handleDisconnect():
    global readiness, peers
    sid = request.sid
    # Remove from readiness if present
    if sid in readiness:
        del readiness[sid]
    # Remove from peers list (active connections only)
    peers = [p for p in peers if p.get('sid') != sid]
    print(f"User disconnected: {sid}")
    # Note: We don't remove from game_participants - they can reconnect

@socketio.on('ai-response-read')
def handleAiResponseRead():
    global readiness
    sid = request.sid
    readiness[sid] = True
    print(f"User {sid} has read the AI response")
    
    # Check if all connected peers have read the response
    all_ready = len(readiness) >= len(peers) and all(readiness.values())
    
    if all_ready:
        print("All users have read the AI response!")
        readiness = {}  # Reset for next round
        socketio.emit('all-ready-for-next-round')
    


@app.route('/upload', methods=['POST'])
def uploadVideo():
    print(f"[UPLOAD] Request received")
    print(f"[UPLOAD] Content-Type: {request.content_type}")
    print(f"[UPLOAD] Files keys: {list(request.files.keys())}")
    print(f"[UPLOAD] Form keys: {list(request.form.keys())}")
    
    if 'video' not in request.files:
        print("[UPLOAD] ERROR: No 'video' key in request.files")
        print(f"[UPLOAD] request.files = {request.files}")
        return jsonify({'error': 'No video file'}), 400
    
    video = request.files['video']
    username = request.form.get('username', 'Unknown')
    
    print(f"[UPLOAD] Video filename: '{video.filename}'")
    print(f"[UPLOAD] Username from form: '{username}'")
    
    if video.filename == '':
        print("[UPLOAD] ERROR: Empty filename")
        return jsonify({'error': 'Empty filename'}), 400
    
    # Track this upload as pending
    pending_uploads.add(username)
    
    filename = f'presentation_{username}_{int(time.time())}.webm'
    filepath = os.path.join('recordings', filename)
    
    try:
        video.save(filepath)
        print(f"[UPLOAD] SUCCESS: Saved to {filepath}")
        print(f"[UPLOAD] Pending uploads: {len(pending_uploads)}")
        
        # Process video with AI in background
        socketio.start_background_task(process_video_response, username, filepath)
        
        return jsonify({'success': True, 'filename': filename})
    except Exception as e:
        print(f"[UPLOAD] ERROR saving file: {e}")
        pending_uploads.discard(username)
        return jsonify({'error': str(e)}), 500

def process_video_response(username, filepath):
    """Process a video response with AI in the background"""
    global all_responded_event_sent
    print(f"[PROCESS] Starting to process video for {username}")
    try:
        print(f"[PROCESS] Calling extractResponse for {username}")
        result = extractResponse(filepath)
        print(f"[PROCESS] Extracted from {username}: {result}")
        
        # Add to responses
        userResponses.append({
            "name": username,
            "transcription": result.get("transcription", ""),
            "items": result.get("items", []),
            "action": result.get("transcription", "")  # Use transcription as action for now
        })
        
        # Remove from pending
        pending_uploads.discard(username)
        print(f"[PROCESS] Added response from {username}. Total: {len(userResponses)}, Pending: {len(pending_uploads)}")
        
        # Check if all videos are processed and all users have responded
        if all_responded_event_sent and len(pending_uploads) == 0:
            print("[PROCESS] All videos processed - triggering AI cycle")
            socketio.start_background_task(run_ai_cycle_when_ready)
    except Exception as e:
        print(f"[PROCESS] ERROR processing video for {username}: {e}")
        import traceback
        traceback.print_exc()
        pending_uploads.discard(username)

@app.route('/ai-cycle', methods=['POST'])
def run_ai_cycle():
    """Run the AI cycle after all users have responded"""
    global successPercentage
    
    try:
        print(f"Running AI cycle with {len(userResponses)} responses")
        print(f"Current situation: {promptHistory[-1]}")
        
        if len(userResponses) == 0:
            return jsonify({'error': 'No user responses to process'}), 400
        
        # Run the cycle
        result = cycle(promptHistory[-1])
        
        print(f"AI cycle complete. New situation: {promptHistory[-1]}")
        print(f"Success percentage: {successPercentage}%")
        
        return jsonify({
            'success': True,
            'new_prompt': promptHistory[-1],
            'success_percentage': successPercentage,
            'simulation': result
        })
    except Exception as e:
        print(f"Error in AI cycle: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000, debug=True)