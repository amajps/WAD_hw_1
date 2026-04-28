# HW1 — FastAPI LLM Chat Application

A production-ready LLM chat application with GitHub OAuth authentication, multi-chat support, and local LLM inference.

**Frontend Mode:** Single Page Application (SPA)  
**Architecture Pattern:** Model–Controller–Service (MCS)  
**Auth Tokens:** JWT (stateless access) + Redis-backed refresh tokens (30-day TTL)

## ⭐ Key Features

- ✅ **GitHub OAuth 2.0** authentication with automatic user linking
- ✅ **JWT Access Tokens** (15-min) + **Redis Refresh Tokens** (30-day TTL)
- ✅ **Multiple Chat Threads** with persistent history per user
- ✅ **LLM Integration** with graceful fallback to intelligent mock responses
- ✅ **Async PostgreSQL** with SQLAlchemy ORM and Alembic migrations
- ✅ **Complete SPA Frontend** (750+ lines vanilla JavaScript, no framework)
- ✅ **CORS Support** for seamless frontend-backend communication
- ✅ **Auto-Refresh Tokens** with automatic token rotation

## 📸 Screenshots

### 1. GitHub OAuth Login
Sign in with GitHub - the OAuth button redirects to GitHub for authorization
![GitHub OAuth Login](./docs/screenshots/1-github-oauth.png)

### 2. GitHub Authorization
Authorize the application to access your GitHub profile
![GitHub Authorization](./docs/screenshots/2-github-auth.png)

### 3. Chat Interface & LLM Responses
Full chat interface with LLM responses, typing indicators, and message history
![Chat Interface](./docs/screenshots/3-chat-interface.png)

## 🛠 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI 0.110.0 + Uvicorn |
| **Database** | PostgreSQL + SQLAlchemy 2.0+ (async) |
| **Migrations** | Alembic |
| **Authentication** | JWT (PyJWT) + bcrypt + GitHub OAuth 2.0 |
| **Session Storage** | Redis |
| **LLM** | llama-cpp-python (optional, with mock fallback) |
| **Configuration** | pydantic-settings + python-dotenv |
| **Frontend** | Vanilla JavaScript (HTML5, CSS3, ES6+) |
| **CORS** | FastAPI CORSMiddleware |

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Git

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/HW1.git
cd HW1
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your GitHub OAuth credentials:

```env
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback
FRONTEND_URL=http://localhost:8080
```

### 3. Start Services

```bash
docker-compose up -d
pip install -r requirements.txt
alembic upgrade head
```

### 4. Run Application

**Terminal 1 - Backend:**
```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
python3 -m http.server 8080
```

### 5. Open in Browser

```
http://localhost:8080/index.html
```

Click **Sign in with GitHub** and start chatting! 🎉

## 🔌 API Endpoints

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Register new user |
| `POST` | `/auth/token` | Login with password |
| `POST` | `/auth/refresh` | Refresh access token |
| `GET` | `/auth/github/login` | Start GitHub OAuth |
| `GET` | `/auth/github/callback` | GitHub OAuth callback |

### Chat Management (Protected)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/chats/` | List all user's chats |
| `POST` | `/chats/` | Create new chat |
| `GET` | `/chats/{id}/messages` | Get messages from chat |
| `POST` | `/chats/{id}/messages` | Send message & get LLM response |

## 📂 Project Structure

```
HW1/
├── main.py                    # FastAPI app setup
├── config.py                  # Settings from environment
├── models.py                  # SQLAlchemy ORM models
├── schemas.py                 # Pydantic request/response models
├── security.py                # JWT & password utilities
├── db.py                      # Database session management
├── llm.py                     # LLM inference + mock responses
├── redis_client.py            # Redis connection
│
├── routers/
│   ├── auth.py               # Authentication endpoints
│   ├── github_oauth.py        # GitHub OAuth endpoints
│   └── chat.py               # Chat & message endpoints
│
├── index.html                # SPA Frontend (vanilla JS)
├── docker-compose.yml         # PostgreSQL + Redis
├── alembic/                  # Database migrations
├── requirements.txt          # Python dependencies
├── .env.example              # Configuration template
├── .gitignore               # Git ignore rules
├── LICENSE                  # MIT License
├── CONTRIBUTING.md          # Contribution guidelines
└── README.md                # This file
```

## 🔐 Authentication

### Password-based Login
1. User registers with username + password (bcrypt hashed)
2. Login returns JWT + refresh token
3. Refresh token stored in Redis (30-day TTL)

### GitHub OAuth 2.0
1. User clicks "Sign in with GitHub"
2. Redirected to GitHub authorization
3. Backend exchanges code for access token
4. User profile fetched from GitHub API
5. User created/linked in database
6. JWT + refresh token generated
7. Tokens saved to localStorage
8. Automatically redirected to chat interface

## 📖 Full Documentation

See **REPORT.md** for:
- Detailed architecture breakdown
- Code organization & patterns
- Database schema
- UI design & screenshots
- API detailed specifications
- Testing instructions
- Troubleshooting guide

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines

## 📝 License

MIT License - see [LICENSE](LICENSE)

---

**Ready to chat?** Start with Quick Start above! 🚀

## Installation & Setup

### 1. Prerequisites

- Python 3.9+
- Docker & Docker Compose (for PostgreSQL + Redis)
- Git
- GitHub OAuth App credentials (optional, or use password auth)

### 2. GitHub OAuth App Setup (Optional)

For GitHub login support:

1. Go to https://github.com/settings/developers
2. Click **New OAuth App**
3. Fill in:
   - **Application name:** HW1 LLM Chat
   - **Homepage URL:** `http://localhost:8000`
   - **Authorization callback URL:** `http://localhost:8000/auth/github/callback`
4. Save your **Client ID** and **Client Secret**

### 3. Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/HW1.git
cd HW1
```

### 4. Environment Configuration

```bash
cp .env.example .env
```

Edit `.env` with your values:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/hw1
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
JWT_SECRET_KEY=your-secure-random-key-here-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30

# GitHub OAuth (from step 2, optional)
GITHUB_CLIENT_ID=your_client_id_from_github
GITHUB_CLIENT_SECRET=your_client_secret_from_github
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback

# Frontend URL (for OAuth redirects)
FRONTEND_URL=http://localhost:8080

# LLM (optional - path to GGUF model file)
LLAMA_MODEL_PATH=model.gguf
```

### 5. Start Services (Docker)

```bash
docker-compose up -d
```

Verify services:
```bash
docker-compose ps
# Should show: PostgreSQL running, Redis running
```

### 6. Install Python Dependencies

```bash
pip install -r requirements.txt
```

If you get permission errors on Linux:
```bash
pip install --break-system-packages -r requirements.txt
```

### 7. Apply Database Migrations

```bash
alembic upgrade head
```

### 8. Start Backend

```bash
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### 9. Start Frontend (in another terminal)

```bash
cd /home/kali/HW1
python3 -m http.server 8080
```

### 10. Open in Browser

```
http://localhost:8080/index.html
```

### 7. Run Backend

```bash
uvicorn main:app --reload
```

Backend runs at `http://localhost:8000`  
API documentation at `http://localhost:8000/docs`

### 8. Run Frontend

Open `index.html` in your browser, or serve via HTTP:

```bash
python -m http.server 8080
```

Visit `http://localhost:8080/index.html` and click **Sign in with GitHub**

## Quick Start (Complete Flow)

```bash
# Clone and setup
cd HW1
cp .env.example .env
# Edit .env with GitHub OAuth credentials

# Start services (PostgreSQL + Redis)
docker-compose up -d
docker-compose ps  # verify

# Install dependencies
pip install -r requirements.txt

# Apply migrations
alembic upgrade head

# Terminal 1: Run backend
uvicorn main:app --reload
# Backend ready at http://localhost:8000

# Terminal 2: Serve frontend
python -m http.server 8080
# Frontend ready at http://localhost:8080/index.html

# In browser: http://localhost:8080/index.html
# Click "Sign in with GitHub" → authorize → start chatting
```

## API Endpoints

### Authentication

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/auth/register` | Register new user (username + password) |
| `POST` | `/auth/token` | Login (returns access + refresh tokens) |
| `POST` | `/auth/refresh` | Refresh access token |
| `GET` | `/auth/github/login` | Start GitHub OAuth |
| `GET` | `/auth/github/callback` | GitHub OAuth callback (auto-handled) |

### Chat Endpoints (Protected)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/chats` | List user's chats |
| `POST` | `/chats` | Create new chat |
| `GET` | `/chats/{id}/messages` | Get messages in chat |
| `POST` | `/chats/{id}/messages` | Send message, get LLM response |

**Protected routes require:** `Authorization: Bearer <access_token>` header

### Health Check

| Method | Path |
|--------|------|
| `GET` | `/health` |

## Project Structure

```
HW1/
├── main.py                    # FastAPI app entry, route registration
├── config.py                  # Settings from environment
├── models.py                  # SQLAlchemy ORM (User, Chat, Message)
├── schemas.py                 # Pydantic request/response models
├── security.py                # JWT & password utilities (bcrypt)
├── db.py                      # Database session management
├── llm.py                     # LLM inference wrapper
├── redis_client.py            # Redis connection
│
├── routers/
│   ├── auth.py               # Register, login, refresh endpoints
│   ├── github_oauth.py        # GitHub OAuth endpoints
│   └── chat.py               # Chat & message endpoints
│
├── index.html                # SPA Frontend (750+ lines)
│
├── docker-compose.yml         # PostgreSQL + Redis services
├── alembic.ini               # Migration configuration
├── alembic/versions/         # Database migration scripts
├── requirements.txt          # Python dependencies
├── .env.example              # Configuration template
└── .env                      # Local environment (git-ignored)
```

## Architecture

### MCS Pattern (Model–Controller–Service)

```
Routers (Controllers)          Services                    Models
├── auth.py                    ├── security.py             ├── User
├── github_oauth.py            ├── llm.py                  ├── Chat
└── chat.py                    └── redis_client.py         └── Message

Request → Router → Service Logic → Database
```

**Models** (`models.py`): SQLAlchemy ORM definitions  
**Controllers** (`routers/`): FastAPI endpoint handlers  
**Services** (`security.py`, `llm.py`, etc.): Reusable business logic

### Authentication Flow

```
┌─ Password Login
│  POST /auth/register → hash password → save user
│  POST /auth/token → verify password → JWT + refresh token (Redis)
│
├─ GitHub OAuth
│  GET /auth/github/login → Redirect to GitHub
│  GET /auth/github/callback → Exchange code → Fetch user → JWT + refresh token
│
└─ Token Refresh
   POST /auth/refresh → Validate refresh token in Redis → New JWT + token
```

**Access Token** (JWT): Stateless, 15-minute expiry, included in Authorization header  
**Refresh Token** (Random): Stored in Redis with 30-day TTL, used to get new access token  
**Redis Role**: Session storage for refresh tokens with automatic expiration

## Database Schema

### Users Table
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  username VARCHAR(128) UNIQUE NOT NULL,
  email VARCHAR(256) UNIQUE,
  hashed_password VARCHAR(256),
  github_id VARCHAR(128) UNIQUE,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Chats Table
```sql
CREATE TABLE chats (
  id SERIAL PRIMARY KEY,
  title VARCHAR(256) NOT NULL,
  user_id INTEGER NOT NULL REFERENCES users(id),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Messages Table
```sql
CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  chat_id INTEGER NOT NULL REFERENCES chats(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  role VARCHAR(16) NOT NULL,  -- 'user' or 'assistant'
  text TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Frontend

A single-page application (vanilla JavaScript, no framework) featuring:

- **GitHub OAuth button** — Redirects to GitHub, captures tokens
- **Chat interface** — Sidebar with chat list, main area with messages
- **Token management** — Saves tokens to localStorage, auto-refreshes
- **Message display** — Shows user and LLM responses
- **Responsive design** — Works on desktop and mobile

**Key Functions in `index.html`:**
- `handleGitHubLogin()` — OAuth redirect
- `apiCall()` — HTTP requests with JWT header + auto-refresh
- `sendMessage()` — Send message to LLM
- `renderApp()` — Render chat interface

## Testing with cURL

```bash
# Health check
curl http://localhost:8000/health

# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"user1","password":"pass123","email":"user1@example.com"}'

# Login
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user1&password=pass123"

# List chats (with JWT)
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/chats

# Create chat
curl -X POST http://localhost:8000/chats \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Chat"}'

# Send message
curl -X POST http://localhost:8000/chats/1/messages \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is 2+2?"}'
```

## Troubleshooting

**"Cannot connect to PostgreSQL"**
```bash
docker-compose logs postgres
docker-compose restart postgres
```

**"Cannot connect to Redis"**
```bash
docker-compose logs redis
docker-compose restart redis
```

**"GitHub client ID not configured"**
- Check `.env` has `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET`
- Restart backend: `Ctrl+C` then `uvicorn main:app --reload`

**"No such file: model.gguf"**
- Download a GGUF model from [Hugging Face](https://huggingface.co/models?library=gguf)
- Or update `LLAMA_MODEL_PATH` in `.env`

**"Token refresh failed"**
- Check Redis is running: `docker-compose ps`
- Logout and login again

## Stopping Services

```bash
docker-compose down
```

## See Also

- **REPORT.md** — Project design, code organization, UI description, database schema
# Option 1: Direct open
open index.html

# Option 2: Python HTTP server
python -m http.server 8080
# Then visit http://localhost:8080/index.html
```

Click **Sign in with GitHub** to authenticate and start chatting!

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/register` | Register new user (username + password) |
| `POST` | `/auth/token` | Get access + refresh tokens (username/password login) |
| `POST` | `/auth/refresh` | Refresh access token using refresh token |
| `GET` | `/auth/github/login` | Redirect to GitHub OAuth authorization |
| `GET` | `/auth/github/callback` | GitHub OAuth callback (auto-redirects after login) |

### Chat Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/chats` | List all user's chats |
| `POST` | `/chats` | Create a new chat |
| `GET` | `/chats/{chat_id}/messages` | Get all messages in a chat |
| `POST` | `/chats/{chat_id}/messages` | Send a message and get LLM response |

### Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |

## Frontend

A complete SPA frontend is included in `index.html`. Features:

- **GitHub OAuth Integration:** Click "Sign in with GitHub" to authenticate
- **Multi-chat support:** Create and manage multiple conversation threads
- **Real-time messaging:** Send questions and receive LLM-generated responses
- **Token management:** Automatic access token refresh via refresh token
- **Responsive design:** Works on desktop and tablet

The frontend uses vanilla JavaScript (no framework) and communicates with the API via standard fetch. Tokens are stored in localStorage.

### Frontend Usage

After starting the backend with `uvicorn main:app --reload`:

1. **Option A:** Open `index.html` directly in a browser
2. **Option B:** Serve with Python HTTP server:
   ```bash
   python -m http.server 8080
   # Visit http://localhost:8080/index.html
   ```

3. Click **Sign in with GitHub**
4. You'll be redirected to GitHub for authorization
5. After authorization, tokens are saved automatically
6. Create a new chat or select an existing one
7. Type a question and hit Enter or click Send
8. The LLM response appears below your message

## Architecture

```
main.py                 # FastAPI app setup + middleware
├── routers/
│   ├── auth.py        # User registration, token generation, JWT validation
│   ├── github_oauth.py # GitHub OAuth flow
│   └── chat.py        # Chat and message endpoints
├── models.py          # SQLAlchemy ORM models (User, Chat, Message)
├── schemas.py         # Pydantic request/response schemas
├── security.py        # Password hashing, JWT encode/decode
├── llm.py             # LLM inference service (llama-cpp wrapper)
├── db.py              # Database session management
├── redis_client.py    # Redis connection
└── config.py          # Environment settings
```

## Authentication Flow

### Password Login
```
POST /auth/register → Create user (bcrypt hashed password)
POST /auth/token → Authenticate → Issue JWT + Refresh token
  → Access token stored client-side
  → Refresh token stored in Redis (30-day TTL)
```

### GitHub OAuth Login
```
GET /auth/github/login → Redirect to GitHub
GitHub → Callback to /auth/github/callback?code=...
→ Exchange code for GitHub access token
→ Fetch user profile + email
→ Create/find user in DB
→ Issue JWT + Refresh token
→ Redirect to frontend with tokens
```

### Protected Routes
- All chat endpoints require valid JWT in `Authorization: Bearer <token>` header
- JWT validation happens in `get_current_user()` dependency

## Database Schema

### users
- `id` (PK)
- `username` (unique)
- `email` (unique, nullable)
- `hashed_password` (nullable, for password-based auth)
- `github_id` (unique, nullable, for OAuth)
- `is_active` (boolean)
- `created_at` (timestamp)

### chats
- `id` (PK)
- `title` (string)
- `user_id` (FK → users)
- `created_at` (timestamp)

### messages
- `id` (PK)
- `chat_id` (FK → chats)
- `user_id` (FK → users, nullable)
- `role` ("user" or "assistant")
- `text` (message content)
- `created_at` (timestamp)

## Usage Example (cURL)

### 1. Register & Login (Password)
```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123", "email": "alice@example.com"}'

# Login
curl -X POST http://localhost:8000/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=secret123"

# Response: {"access_token": "...", "refresh_token": "...", "token_type": "bearer"}
```

### 2. Or Use GitHub OAuth
```bash
# Open in browser:
http://localhost:8000/auth/github/login

# You'll be redirected to GitHub, authorize, then redirected back with tokens
```

### 3. Create Chat
```bash
curl -X POST http://localhost:8000/chats \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Chat"}'

# Response: {"id": 1, "title": "My First Chat", "created_at": "..."}
```

### 4. Send Message
```bash
curl -X POST http://localhost:8000/chats/1/messages \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of France?"}'

# Response: {"answer": "The capital of France is Paris."}
```

## Notes

- **LLM Model:** The app expects a GGUF model file. Download one from [Hugging Face](https://huggingface.co/models?library=gguf) (e.g., `mistral-7b-instruct-v0.1.Q4_K_M.gguf`).
- **Stateless Access Tokens:** JWT access tokens don't require database lookups.
- **Refresh Tokens in Redis:** Enables instant revocation and 30-day expiration.
- **GitHub OAuth:** Requires a GitHub OAuth App. Follow the setup steps above.
- **Async Operations:** All DB queries are non-blocking; suitable for concurrent users.

## Stopping Services

```bash
docker-compose down
```

## Troubleshooting

**"GitHub client ID is not configured"**
- Ensure `GITHUB_CLIENT_ID` and `GITHUB_CLIENT_SECRET` are set in `.env`

**"Redis client not initialized"**
- Check Redis is running: `docker-compose ps`
- Verify `REDIS_URL` in `.env`

**"No such file: model.gguf"**
- Download a GGUF model or update `LLAMA_MODEL_PATH` to a valid path
- Model is loaded on first request; startup takes time
