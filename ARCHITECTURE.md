# Architecture & Code Organization

## MCS (Model–Controller–Service) Pattern

The application follows the MCS architectural pattern to maintain clean separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│              Controllers (Routers)                      │
│  • auth.py - HTTP handlers, input validation            │
│  • chat.py - HTTP handlers, output serialization        │
│  • github_oauth.py - OAuth flow HTTP handlers           │
│                                                         │
│  → Thin layer: Only parse requests and call services    │
└────────────────────┬────────────────────────────────────┘
                     ↓ Depends on
┌─────────────────────────────────────────────────────────┐
│              Services (Business Logic)                  │
│  • AuthService - Password hashing, JWT creation         │
│  • GitHubOAuthService - OAuth flow, user linking        │
│  • ChatService - Message handling, LLM integration      │
│                                                         │
│  → Medium layer: Core business logic, no HTTP           │
└────────────────────┬────────────────────────────────────┘
                     ↓ Interacts with
┌─────────────────────────────────────────────────────────┐
│              Models (Data Layer)                        │
│  • User - SQLAlchemy ORM model                          │
│  • Chat - SQLAlchemy ORM model                          │
│  • Message - SQLAlchemy ORM model                       │
│                                                         │
│  → Thin layer: Database schema definitions              │
└─────────────────────────────────────────────────────────┘
```

## Directory Structure

```
HW1/
├── models.py                  # SQLAlchemy ORM models (User, Chat, Message)
├── schemas.py                 # Pydantic request/response models
├── security.py                # JWT, password utilities (no HTTP)
├── db.py                      # Database session management
├── config.py                  # Environment settings
├── llm.py                     # LLM inference (no HTTP)
├── redis_client.py            # Redis connection (no HTTP)
│
├── dependencies.py            # ✨ NEW: Shared FastAPI dependencies
│                              #    (get_current_user, oauth2_scheme)
│
├── routers/                   # Controllers - HTTP Request Handlers
│   ├── auth.py               # Endpoints: /auth/register, /auth/token, etc.
│   ├── chat.py               # Endpoints: /chats/, /chats/{id}/messages
│   └── github_oauth.py        # Endpoints: /auth/github/login, /auth/github/callback
│
├── services/                  # ✨ NEW: Business Logic Layer
│   ├── __init__.py           # Exports AuthService
│   ├── auth_service.py       # Services: register_user, authenticate_user, create_tokens
│   ├── github_oauth_service.py # Services: exchange_code, fetch_profile, create_or_link_user
│   └── chat_service.py       # Services: list_chats, create_chat, send_message
│
├── alembic/                  # Database migrations
├── index.html                # Frontend SPA
├── docker-compose.yml        # Services definition
├── requirements.txt          # Dependencies
├── .env.example              # Configuration template
└── main.py                   # FastAPI app setup
```

## Service Layer Responsibilities

### AuthService (`services/__init__.py`)

Handles all authentication business logic:

```python
# User Registration
await AuthService.register_user(db, username, password, email)
  → Hash password with bcrypt
  → Check username uniqueness
  → Save to database
  → Return User object

# User Authentication
await AuthService.authenticate_user(db, username, password)
  → Find user by username
  → Verify password against hash
  → Return User object

# Token Creation
await AuthService.create_tokens(user_id)
  → Create JWT access token (15-min expiry)
  → Create refresh token (random 32 bytes)
  → Store refresh token in Redis (30-day TTL)
  → Return (access_token, refresh_token)

# Token Refresh
await AuthService.refresh_access_token(refresh_token)
  → Validate refresh token exists in Redis
  → Delete old refresh token
  → Create new access token
  → Create new refresh token
  → Store in Redis
  → Return (new_access_token, new_refresh_token)

# Logout
await AuthService.logout(refresh_token)
  → Delete refresh token from Redis
```

### GitHubOAuthService (`services/github_oauth_service.py`)

Handles GitHub OAuth 2.0 flow:

```python
# Generate Auth URL
GitHubOAuthService.get_github_auth_url()
  → Return GitHub authorization endpoint with client_id

# Exchange Code
await GitHubOAuthService.exchange_code_for_token(code)
  → POST to GitHub token endpoint
  → Extract access token
  → Return token

# Fetch User Profile
await GitHubOAuthService.fetch_github_user_profile(github_token)
  → GET /user from GitHub API
  → GET /user/emails from GitHub API
  → Extract primary verified email
  → Return {github_id, username, email}

# Create or Link User
await GitHubOAuthService.create_or_link_user(db, github_id, username, email)
  → Check if user exists by github_id
  → If not, check by email
  → If not, create new user
  → Otherwise, link github_id to existing user
  → Return User object

# Generate OAuth Tokens
await GitHubOAuthService.generate_oauth_tokens(user_id)
  → Create JWT access token
  → Create refresh token
  → Store in Redis
  → Return tokens
```

### ChatService (`services/chat_service.py`)

Handles chat and messaging:

```python
# List User Chats
await ChatService.list_user_chats(user_id, db)
  → Query chats where user_id matches
  → Return sorted by created_at

# Create Chat
await ChatService.create_chat(user_id, title, db)
  → Create new Chat object
  → Save to database
  → Return Chat object

# Get Chat Messages
await ChatService.get_chat_messages(chat_id, user_id, db)
  → Query messages for chat_id
  → Verify user owns the chat
  → Return messages sorted by created_at

# Send Message
await ChatService.send_message(chat_id, user_id, question, db)
  → Verify user owns the chat
  → Save user message to database
  → Call LLM synchronously (in thread pool)
  → Save assistant response to database
  → Return (question, answer)
```

## Controller (Router) Responsibilities

Controllers in `routers/` are thin HTTP handlers:

```python
# BEFORE: Controllers had 20+ lines of business logic
@router.post("/auth/register")
async def register_user(data: UserCreate, db: AsyncSession):
    existing = await db.execute(select(User).where(...))  # ❌ DB query
    if existing.scalar_one_or_none():
        raise HTTPException(...)
    user = User(username=..., hashed_password=hash_password(...))  # ❌ Logic
    db.add(user)  # ❌ DB operation
    await db.commit()
    await db.refresh(user)
    return user

# AFTER: Controllers are simple request handlers
@router.post("/auth/register")
async def register_user(data: UserCreate, db: AsyncSession):
    try:
        user = await AuthService.register_user(db, data.username, data.password, data.email)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

### Current Router Structure

**`routers/auth.py`** - Authentication endpoints
- `POST /auth/register` → AuthService.register_user()
- `POST /auth/token` → AuthService.authenticate_user() + create_tokens()
- `POST /auth/refresh` → AuthService.refresh_access_token()
- `POST /auth/logout` → AuthService.logout()
- `GET /auth/me` → Return current user (dependency)

**`routers/chat.py`** - Chat management
- `GET /chats/` → ChatService.list_user_chats()
- `POST /chats/` → ChatService.create_chat()
- `GET /chats/{id}/messages` → ChatService.get_chat_messages()
- `POST /chats/{id}/messages` → ChatService.send_message()

**`routers/github_oauth.py`** - OAuth flow
- `GET /auth/github/login` → GitHubOAuthService.get_github_auth_url()
- `GET /auth/github/callback` → Full OAuth flow with services

## Dependencies Layer

**`dependencies.py`** - Shared FastAPI dependencies

```python
# Shared dependency used by both auth.py and chat.py
async def get_current_user(token, db):
    → Verify JWT token
    → Query user from database
    → Return User object

# Shared OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")
```

Benefits:
- Avoids circular imports (auth.py and chat.py would import each other)
- Single source of truth for authentication dependency
- Easy to test in isolation

## Data Flow Examples

### Password Login

```
1. Client POST /auth/token {username, password}
   ↓
2. Router: auth.py:token()
   ├─ Parse request
   ├─ Call AuthService.authenticate_user()
   │  ├─ Query User from database
   │  ├─ Verify password with bcrypt
   │  └─ Return User object
   ├─ Call AuthService.create_tokens()
   │  ├─ Create JWT (signed with secret key)
   │  ├─ Create refresh token (random)
   │  ├─ Store in Redis with 30-day TTL
   │  └─ Return tokens
   ├─ Serialize response
   └─ Return TokenResponse {access_token, refresh_token}
   ↓
3. Client saves tokens to localStorage
```

### Send Message

```
1. Client POST /chats/1/messages {question: "hello"}
   + Header: Authorization: Bearer <jwt>
   ↓
2. FastAPI: Dependency get_current_user()
   ├─ Verify JWT signature
   ├─ Check expiry
   ├─ Query User from database
   └─ Return User object
   ↓
3. Router: chat.py:send_message()
   ├─ Parse request
   ├─ Call ChatService.send_message()
   │  ├─ Verify user owns chat
   │  ├─ Save user message to database
   │  ├─ Call LLM (sync, in thread pool)
   │  ├─ Save assistant response to database
   │  └─ Return answers
   ├─ Serialize response
   └─ Return LLMResponse {answer: "..."}
   ↓
4. Client displays message and response
```

### GitHub OAuth

```
1. Client clicks "Sign in with GitHub"
   ↓
2. Router: github_oauth.py:github_login()
   ├─ Get GitHub auth URL from service
   └─ Redirect to GitHub
   ↓
3. User authorizes on GitHub
   ↓
4. GitHub redirects to /auth/github/callback?code=...
   ↓
5. Router: github_oauth.py:github_callback()
   ├─ Call GitHubOAuthService.exchange_code_for_token()
   │  └─ POST to GitHub API, get access_token
   ├─ Call GitHubOAuthService.fetch_github_user_profile()
   │  ├─ GET /user, get profile
   │  └─ GET /user/emails, get email
   ├─ Call GitHubOAuthService.create_or_link_user()
   │  ├─ Find or create user in database
   │  └─ Return User object
   ├─ Call GitHubOAuthService.generate_oauth_tokens()
   │  ├─ Create JWT
   │  ├─ Create refresh token
   │  ├─ Store in Redis
   │  └─ Return tokens
   └─ Redirect to frontend with tokens in URL
   ↓
6. Frontend captures tokens and saves to localStorage
```

## Benefits of MCS Pattern

### Before (Monolithic Controllers)
- Controllers had 20+ lines of business logic
- Hard to test (must mock database)
- Logic mixed with HTTP concerns
- Difficult to reuse business logic
- Database queries scattered everywhere

### After (Service Layer)
- ✅ Controllers: 5-10 lines (just routing)
- ✅ Services: Pure business logic (easy to test)
- ✅ Clear separation of concerns
- ✅ Reusable business logic
- ✅ All database access centralized
- ✅ Easy to add new features
- ✅ Easy to change database backend
- ✅ Easier to add caching/optimization

## Testing Implications

### Service Layer Testing (No HTTP needed)

```python
# Test authentication service
@pytest.mark.asyncio
async def test_register_user():
    db = AsyncSession()  # Mock or real
    user = await AuthService.register_user(db, "user1", "pass", "email@test.com")
    assert user.username == "user1"
    assert user.id is not None
```

### Router Testing (Can test with TestClient)

```python
# Test HTTP endpoint
def test_register_endpoint():
    response = client.post("/auth/register", json={...})
    assert response.status_code == 200
    assert response.json()["username"] == "user1"
```

## Future Enhancements

With this structure, it's easy to:

1. **Add caching layer** - Cache at service level
2. **Add logging** - Log service calls centrally
3. **Add metrics** - Monitor service performance
4. **Add background jobs** - Queue message processing
5. **Add email verification** - New AuthService method
6. **Add pagination** - ChatService enhancements
7. **Add database abstraction** - Repository pattern
8. **Add rate limiting** - At service level
9. **Add permission checks** - At service level
10. **Add audit logging** - Track user actions

All without touching the HTTP layer!
