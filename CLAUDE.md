# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Video to MP3 Converter** - Event-driven microservice architecture with Python/Flask services, orchestrated via Kubernetes.

**Tech Stack**:
- **Backend**: Python 3.12+, Flask, PyJWT, Flask-MySQLdb, Flask-PyMongo, Pika (RabbitMQ)
- **Databases**: MySQL (user auth), MongoDB (file storage/GridFS)
- **Message Queue**: RabbitMQ (planned)
- **Containerization**: Docker (basic setup for auth service)
- **Package Management**: uv (per-service pyproject.toml)

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React UI  │────▶│  API Gateway│────▶│   Auth Srv  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                  │   │                  │
       │                  ▼   ▼                  ▼
       │            ┌─────────────┐       ┌──────────┐
       │            │  MongoDB    │◄──────│  MySQL   │
       │            │  (GridFS)   │       └──────────┘
       │            └─────────────┘
       │                  │
       ▼                  ▼
 ┌───────────┐      ┌─────────────┐
 │  RabbitMQ │─────▶│  Summary    │
 └───────────┘      │    Srv      │
       │            └─────────────┘
       ▼
 ┌─────────────┐
 │  Converter  │
 └─────────────┘
```

**Data Stores**:
- **MySQL** (`auth` DB) - User credentials, authentication data
- **MongoDB** (`videos` DB for summary, `gateway` DB for gateway) - Video/MP3 files (GridFS), summaries

### Services Overview

| Service | Location | Port | Status | Description |
|---------|----------|------|--------|-------------|
| Auth Service | `/python/src/auth/` | 5000 | ✅ Complete | User login, JWT validation |
| API Gateway | `/python/src/gateway/` | 5001 | 🚧 Partial | Central entry point, file I/O, JWT validation, GridFS |
| Summary Service | `/python/src/summary/` | 5002 | ✅ Complete | AI-powered file summarization |
| Video Converter | - | - | ❌ Not Started | FFmpeg-based video to MP3 conversion |
| Notification Service | - | - | ❌ Not Started | Email notifications for job completion |
| Web UI | - | - | ❌ Not Started | React frontend for upload/download |

### Data Flow

1. **Upload Flow**: Client → Gateway (file upload) → RabbitMQ → Video Converter
2. **Processing**: Converter pulls from RabbitMQ → processes via FFmpeg → stores MP3 to MongoDB
3. **Summary**: Summary Service processes files via external AI API → stores to MongoDB
4. **Download Flow**: Client → Gateway → MongoDB GridFS retrieve

## File Structure

```
converter-video-mp3/
├── CLAUDE.md                           # This file - project guidance
├── README.md                           # Project overview
├── main.py                             # Root entry point (placeholder)
├── FLOW.JPG                            # Architecture diagram
├── converter-video-mp3.code-workspace  # VSCode workspace config
├── plan/
│   └── video_to_mp3_microservices_plan.md  # Architecture planning document
└── python/
    └── src/
        ├── auth/                       # Authentication service
        │   ├── service.py              # Flask auth service (login, validate)
        │   ├── Dockerfile              # Container configuration
        │   ├── requirements.txt        # Python dependencies
        │   ├── pyproject.toml          # UV package manager config
        │   ├── uv.lock                 # Exact dependency versions
        │   ├── init.sql                # Database initialization script
        │   ├── .env                    # Environment configuration
        │   ├── .env.local              # Local environment overrides
        │   └── manifests/              # Kubernetes deployment files
        │       ├── auth-deploy.yaml    # Deployment configuration
        │       ├── configmap.yaml      # ConfigMap for environment variables
        │       ├── secret.yaml         # Secret configuration
        │       └── service.yaml        # Kubernetes service definition
        ├── gateway/                    # API Gateway service
        │   ├── service.py              # Flask gateway service (incomplete)
        │   ├── pyproject.toml          # UV package manager config
        │   ├── uv.lock                 # Exact dependency versions
        │   ├── .env                    # Environment configuration
        │   └── .env.local              # Local environment overrides
        └── summary/                    # Summary service
            └── service.py              # AI summarization service
```

## Running Services

**Prerequisites**: MySQL, MongoDB, RabbitMQ running locally or via minikube

```bash
# Install dependencies (service-specific with uv)
cd python/src/auth && uv sync
cd python/src/gateway && uv sync

# Or use pip with requirements.txt (auth service)
pip install -r python/src/auth/requirements.txt

# Run services individually
python python/src/auth/service.py       # Port 5000
python python/src/gateway/service.py    # Port 5001
python python/src/summary/service.py    # Port 5002

# Docker (auth service only currently)
docker build -f python/src/auth/Dockerfile -t auth-service python/src/auth/
docker run -p 5000:5000 --env-file python/src/auth/.env auth-service
```

**uv Package Manager** (per-service configuration):
```bash
cd python/src/auth  # or gateway
uv sync              # Install dependencies
uv add package-name  # Add new dependency
uv lock              # Update lock file
```

## Database Configuration

### MySQL (Auth Service)
Environment variables in `python/src/auth/.env`:
```env
MYSQL_HOST=localhost
MYSQL_USER=auth_user
MYSQL_PASSWORD=Auth123
MYSQL_DB=auth
MYSQL_PORT=3306
JWT_SECRET=your-secret-key
```

**User Table Schema** (created by `init.sql`):
```sql
CREATE TABLE user (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
)
```

### MongoDB (Gateway/Summary Services)

**Gateway**: `mongodb://host.minikube.internal:27017/gateway`
**Summary**: `mongodb://host.minikube.internal:27017/videos`

#### MongoDB Schema

**GridFS Collections** (for file storage):

`fs.files` - File metadata:
```javascript
{
  _id: ObjectId,
  filename: string,           // Original filename
  contentType: string,        // MIME type (e.g., "video/mp4", "audio/mpeg")
  length: number,             // File size in bytes
  uploadDate: ISODate,        // Upload timestamp
  chunkSize: number,          // Chunk size (default: 261120)
  metadata: {
    file_type: string,        // "video" or "mp3"
    user_id: string,          // User who uploaded
    converted_from: ObjectId, // For MP3s: ID of original video (optional)
    status: string            // "processing", "completed", "failed"
  }
}
```

`fs.chunks` - File data chunks:
```javascript
{
  _id: ObjectId,
  files_id: ObjectId,         // Reference to fs.files._id
  n: number,                  // Chunk index
  data: BinData               // Chunk data
}
```

`summaries` - File summaries:
```javascript
{
  _id: ObjectId,
  file_id: ObjectId,          // Reference to fs.files._id (optional)
  filename: string,           // Original filename (optional)
  summary: string,            // AI-generated summary (5-6 sentences)
  category: string,           // AI-inferred category (1-3 words)
  context_truncated: boolean, // True if input was truncated
  created_at: ISODate         // Creation timestamp
}
```

## Code Conventions

### Service Structure Pattern
```python
# Single-file implementation per service (service.py)
from flask import Flask, request, jsonify
from dotenv import load_dotenv

load_dotenv(".env")
load_dotenv(".env.local", override=True)

app = Flask(__name__)

# Environment-based configuration
import os
mysql_host = os.getenv('MYSQL_HOST', 'localhost')
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/videos')

# Run on specific port
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
```

### API Patterns

**JWT Validation (Gateway → Auth Service)**:
```python
headers = {'Authorization': request.headers.get('Authorization')}
response = requests.post('http://auth-service:5000/validate', headers=headers)
if response.status_code != 200:
    return jsonify({'error': 'Invalid token'}), 401
```

**MongoDB GridFS (File Storage)**:
```python
from flask_pymongo import PyMongo
import gridfs

server.config["MONGO_URI"] = os.getenv("MONGO_URI")
mongo = PyMongo(server)
fs = gridfs.GridFS(mongo.db)

# Store file
file_id = fs.put(file_data, filename=name, contentType=content_type)

# Retrieve file
file_data = fs.get(file_id).read()
```

**RabbitMQ (Message Publishing - Planned)**:
```python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters("rabbitmq"))
channel = connection.channel()
channel.queue_declare(queue='video_uploads')
channel.basic_publish(exchange='', routing_key='video_uploads', body=message)
connection.close()
```

### Error Response Format
```python
return jsonify({'error': 'Descriptive error message'}), status_code
# Common status codes: 200, 201, 400, 401, 404, 500
```

### Authentication Flow
1. User logs in via Auth Service → receives JWT token
2. Client includes `Authorization: Bearer <token>` header in requests
3. Gateway validates token by calling Auth Service `/validate` endpoint
4. Protected routes return 401 if validation fails

## Implementation Status

### ✅ Complete
- **Auth Service**: Full Flask service with MySQL integration
  - POST `/login` - User login (Basic Auth), returns JWT token
  - POST `/validate` - JWT token validation
  - JWT expires in 1 day (86400 seconds)
  - Default user: `kshilkrot@email.com` / `Admin123`

- **Summary Service**: AI-powered file summarization
  - POST `/summaries` - Generate file summary via external AI API
  - Configurable via environment variables (AI_SUMMARY_URL, AI_SUMMARY_API_KEY, AI_SUMMARY_TIMEOUT, AI_SUMMARY_MAX_CHARS)

### 🚧 In Progress
- **API Gateway** (`/python/src/gateway/service.py`)
  - MongoDB connection setup (done)
  - RabbitMQ connection setup (done)
  - Missing: `/upload`, `/download/<filename>` endpoints
  - Missing: JWT validation via auth service
  - Missing: File handling with GridFS

### ❌ Not Started
- Video Converter Service (FFmpeg integration)
- Notification Service (email notifications)
- React Web UI
- Docker images for gateway/summary services
- User registration endpoint

## Key Dependencies

**Core Libraries**:
| Package | Version | Purpose |
|---------|---------|---------|
| flask | >=3.1.2 | Web framework |
| flask-mysqldb | >=2.0.0 | MySQL integration |
| flask-pymongo | >=3.0.1 | MongoDB integration |
| pyjwt | >=2.11.0 | JWT token handling |
| pika | >=1.3.2 | RabbitMQ client |
| requests | >=2.32.5 | HTTP requests |
| python-dotenv | >=0.9.9 | Environment variable loading |

## Security Notes

### ⚠️ Critical Issues
- **Password Storage**: Currently stored in **plaintext** - must implement bcrypt hashing
- **No CORS**: CORS headers not configured for cross-origin requests
- **No File Validation**: Upload endpoints don't validate file types/sizes

### Recommendations
- Implement `bcrypt` or `argon2` for password hashing
- Add file type validation (accept only video formats)
- Add file size limits (e.g., max 500MB)
- Configure CORS for React frontend origin
- Add rate limiting on auth endpoints
- Use HTTPS in production

## TODO / Next Steps

### High Priority
1. **Complete API Gateway**: Implement `/upload` and `/download/<filename>` endpoints
2. **Security**: Implement password hashing with bcrypt
3. **File Validation**: Add file type/size validation on upload

### Medium Priority
4. **Video Converter Service**: Implement FFmpeg-based conversion
5. **Docker**: Create Dockerfiles for gateway and summary services
6. **CORS**: Configure CORS for frontend integration

### Low Priority
7. **Notification Service**: Email notifications for job completion
8. **React UI**: Frontend for file upload/download
9. **Kubernetes**: Deployment manifests for all services
10. **Testing**: Unit and integration tests

## Development Workflow

1. **Local Development**: Run services directly with Python
2. **Docker**: Containerize individual services for testing
3. **Kubernetes**: Production deployment (auth service manifests ready)
4. **Configuration**: Environment-specific via `.env` and `.env.local` files per service

---

## Code Architecture Summary

### Design Patterns Used
- **Microservice Pattern**: Each service has single responsibility
- **API Gateway Pattern**: Central entry point for routing requests
- **Event-Driven (Planned)**: RabbitMQ for async communication between services
- **Repository Pattern (Implicit)**: Database access abstracted within services

### Inter-Service Communication
- **Synchronous**: HTTP/REST (Gateway → Auth Service for validation)
- **Asynchronous (Planned)**: RabbitMQ messaging (Gateway → Converter)
- **External APIs**: AI Service for summarization

### Data Management
- **Polyglot Persistence**: MySQL for relational data (users), MongoDB for document/file storage
- **GridFS**: MongoDB GridFS for large file storage (videos, MP3s)
- **Separation of Concerns**: Each service manages its own data

### Current Limitations
1. No health check endpoints
2. No monitoring/observability
3. No centralized logging
4. No service discovery (hardcoded URLs)
5. No retry logic for failed requests
6. No graceful shutdown handling
7. No API versioning

### Configuration Management
- Per-service `.env` and `.env.local` files
- Kubernetes ConfigMaps and Secrets (auth service ready)
- AI service endpoint configured as environment variable

---

**Note**: This is a work-in-progress microservice project. While the authentication and summary services are functional, many planned components from the architecture document are not yet implemented. The codebase follows basic Flask patterns but needs enhancement for production readiness.
