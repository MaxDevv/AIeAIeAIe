*__AI GENERATED!!!__*
# AIeAIeAIe 🤖🎮

A multiplayer interactive party game where players team up to solve AI-generated situations using random household items. Players present their creative solutions via video, and an AI evaluates their ideas, simulates the outcome, and generates new challenging scenarios.

![Game Screenshot](https://placehold.co/800x400.png?text=AIeAIeAIe+Gamex)

## 🎯 What is AIeAIeAIe?

AIeAIeAIe is a unique multiplayer experience that combines:
- **Real-time video streaming** (WebRTC/PeerJS)
- **AI-powered situation generation** (Google Gemini via OpenRouter)
- **Creative problem-solving** with household items
- **Collaborative storytelling** where player actions interact and collide

Players join a party, receive a challenging scenario from an "evil AI," scramble to find items in their homes, and present their solutions on camera. The AI then simulates how these solutions interact and presents a new situation based on the outcome.

## 🚀 Features

- **Real-time Multiplayer**: Join parties with friends using Socket.IO for signaling
- **Video Presentation**: Stream your solution to all players using WebRTC/PeerJS
- **AI Game Master**: Powered by Google's Gemini AI for creative scenario generation
- **Video Analysis**: AI processes player recordings to extract transcriptions and identify items
- **Dynamic Storytelling**: Each round builds on the previous, creating an evolving narrative
- **Retro Pixel Art UI**: Stylish gradient backgrounds with pixel-perfect typography

## 🏗️ Architecture

```
┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│   Frontend      │      │    Backend      │      │   AI Services   │
│   (SvelteKit)   │◄────►│   (Flask +      │◄────►│  (OpenRouter +  │
│                 │ WS   │   Socket.IO)    │ HTTP │   Gemini)       │
│ - WebRTC/PeerJS │      │                 │      │                 │
│ - Video capture │      │ - Room mgmt     │      │ - Video analysis│
│ - Game UI       │      │ - AI prompting  │      │ - Scenario gen  │
└─────────────────┘      └─────────────────┘      └─────────────────┘
```

### Tech Stack

**Frontend:**
- [SvelteKit](https://kit.svelte.dev/) - Modern web framework
- [Socket.IO Client](https://socket.io/) - Real-time communication
- [PeerJS](https://peerjs.com/) - WebRTC peer-to-peer connections
- [Vite](https://vitejs.dev/) - Build tooling

**Backend:**
- [Flask](https://flask.palletsprojects.com/) - Python web framework
- [Flask-SocketIO](https://flask-socketio.readthedocs.io/) - WebSocket support
- [OpenAI Python SDK](https://github.com/openai/openai-python) - AI API client
- [json-repair](https://github.com/mangiucugna/json_repair) - LLM output parsing

**AI Services:**
- [OpenRouter](https://openrouter.ai/) - Unified AI API
- [Google Gemini 2.5 Flash](https://deepmind.google/technologies/gemini/) - Text generation
- [Google Gemini 3 Flash Preview](https://deepmind.google/technologies/gemini/) - Video analysis

## 🎮 Game Flow

1. **Welcome** → Player enters username
2. **Party Lobby** → Players gather, host starts game
3. **Prompt Screen** → AI presents a situation (30s timer)
4. **Scramble Time** → Players find items in their homes
5. **Presentation** → Each player has 30s to present their solution on camera
6. **Processing** → AI analyzes all video responses
7. **AI Response** → AI simulates outcomes and presents new situation
8. **Repeat** → Continue until players win or lose!

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- An OpenRouter API key ([Get one here](https://openrouter.ai/keys))

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install flask flask-socketio flask-cors openai json-repair

# Or if there's a requirements.txt
pip install -r requirements.txt

# Set up your API key
echo "your-openrouter-api-key" > ../.env.apikey

# Run the server
python server.py
```

The backend will start on `http://localhost:3000`.

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

The frontend will start on `http://localhost:5173` (or another port if 5173 is in use).

### Environment Configuration

Create a `.env.apikey` file in the project root with your OpenRouter API key:

```
sk-or-v1-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

> ⚠️ **Security Note**: The `.env.apikey` file is gitignored. Never commit API keys to version control!

## 🎲 How to Play

1. Open the game in your browser (`http://localhost:5173`)
2. Enter a username and click "Join Game"
3. Wait in the party lobby for friends to join
4. Click "Start Game" when everyone is ready
5. Read the AI's situation prompt carefully
6. When the timer starts, find item(s) in your home to solve the challenge
7. Present your solution on camera when it's your turn (30 seconds)
8. Watch the AI simulate how everyone's solutions interact
9. Receive a new situation and keep playing!

### Win Condition

Work together to increase your "success percentage" to 100%! The AI can add or subtract up to 20% each round based on your creativity and how well your solutions work together.

## 📁 Project Structure

```
AIeAIeAIe/
├── backend/
│   ├── server.py          # Main Flask/SocketIO server
│   ├── .venv/             # Python virtual environment
│   └── recordings/        # Saved video presentations
├── frontend/
│   ├── src/
│   │   ├── routes/        # SvelteKit pages
│   │   │   ├── welcome/       # Landing page
│   │   │   ├── party/         # Party lobby
│   │   │   ├── prompt/        # Situation display
│   │   │   ├── user-responding/  # Video presentation
│   │   │   ├── thinking/      # AI processing screen
│   │   │   └── ai-response/   # AI results display
│   │   ├── lib/
│   │   └── app.html
│   ├── package.json
│   └── vite.config.js
├── .env.apikey            # API key (gitignored)
├── .gitignore
└── README.md
```

## 🔌 API Endpoints

### HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload video recording for AI analysis |
| `/ai-cycle` | POST | Manually trigger AI processing cycle |

### Socket.IO Events

**Client → Server:**
- `join-room` - Join game party
- `start-game` - Host starts the game
- `add-peer` - Register PeerJS ID
- `start-presenting` - Begin video presentation
- `stop-presenting` - End presentation
- `prompt-timer-finished` - Prompt timer completed
- `ai-response-read` - Player read AI response
- `get-current-presenter` - Request current presenter info

**Server → Client:**
- `all-peers` - List of connected players
- `starting-game` - Game is starting with initial prompt
- `next-presenter` - Next player's turn to present
- `all-users-responded` - All players have presented
- `ai-processing-complete` - AI finished processing responses
- `all-ready-for-next-round` - All players ready to continue
- `user-presenting` - Notification of active presenter
- `presenter-stopped` - Presenter finished

## 🤖 AI Prompts

The game uses two main AI interactions:

### 1. Video Analysis (Gemini 3 Flash Preview)
```
Extract from video:
- Transcription of audio
- List of items presented
```

### 2. Scenario Generation (Gemini 2.5 Flash)
```
System: You are an evil AI creating challenging situations...

Given:
- Current situation
- Each player's action and items
- Current success percentage

Generate:
- Simulation of how solutions interact (30-150 words)
- New situation based on outcomes
- Success percentage update (-20 to +20)
```

## 🚧 Known Limitations & Future Improvements

- **Video recording format**: Currently uses WebM; may not work on all browsers
- **No persistence**: Game state is lost on server restart
- **Single room**: No support for multiple simultaneous games
- **No authentication**: Anyone can join with any username

### Planned Features

- [ ] Sound effects and text-to-speech with robotic voice
- [ ] Discord integration for voice chat
- [ ] Public hosting/deployment
- [ ] User accounts and persistent stats
- [ ] Multiple game rooms
- [ ] Mobile app version

## 🐛 Troubleshooting

### Camera/Microphone not working
- Ensure you're using HTTPS or localhost (browsers block camera on HTTP)
- Check browser permissions for camera/microphone access
- Try refreshing the page

### Can't connect to other players
- Ensure all players are on the same network or using the same server
- Check that the backend is running on port 3000
- Verify firewall settings allow WebRTC connections

### AI not responding
- Check your OpenRouter API key is valid
- Verify you have credits on OpenRouter
- Check backend logs for error messages

## 🤝 Contributing

This project was built as a hackathon project. Contributions are welcome! Please feel free to submit issues or pull requests.

## 📝 License

This project is open source. Feel free to use, modify, and distribute as you see fit.

## 🏆 Credits

Built with ❤️ using:
- [Svelte](https://svelte.dev/)
- [Flask](https://flask.palletsprojects.com/)
- [Socket.IO](https://socket.io/)
- [PeerJS](https://peerjs.com/)
- [OpenRouter](https://openrouter.ai/)
- [Google Gemini](https://deepmind.google/technologies/gemini/)

---

**Ready to outsmart the evil AI? Gather your friends and start playing!** 🎉
