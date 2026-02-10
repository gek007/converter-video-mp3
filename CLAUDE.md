# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Video to MP3 Converter** - Event-driven microservice architecture with Python/Flask services, orchestrated via Kubernetes.

**Tech Stack**:
- **Backend**: Python 3.12+, Flask, PyJWT, Flask-MySQLdb, Flask-PyMongo, Pika (RabbitMQ)
- **Databases**: MySQL (user auth), MongoDB (file storage/GridFS)
- **Message Queue**: RabbitMQ (planned)
- **Containerization**: Docker (basic setup for auth service)
- **Package Management**: uv (pyproject.toml configured)

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   React UI  │────▶│  API Gateway│────▶│   Auth Srv  │
└─────────────┘     └─────────────┘     └─────────────┘
                          │                      │
                          ▼                      ▼
                    ┌─────────────┐     ┌─────────────┐
                    │    RabbitMQ │────▶│  Converter  │
                    └─────────────┘     └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │  Summary Srv│
                    └─────────────┘
```

### Services Overview

| Service | Location | Port | Status | Description |
|---------|----------|------|--------|-------------|
| Auth Service | `/python/src/auth/` | 5000 | ✅ Complete | User registration/login, JWT generation/validation |
| API Gateway | `/python/src/gateway/` | 5001 | 🚧 Partial | Central entry point, file I/O, JWT validation, GridFS |
| Summary Service | `/python/src/summary/` | 5002 | ✅ Complete | AI-powered file summarization, categories |
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
system_design/
├── python/
│   └── src/
│       ├── auth/
│       │   ├── service.py          # Flask auth service (login, register, validate)
│       │   ├── Dockerfile
│       │   └── requirements.txt
│       ├── gateway/
│       │   └── server.py           # API gateway (incomplete - upload/download pending)
│       └── summary/
│           └── service.py          # AI summarization service
├── plan/
│   └── video_to_mp3_microservices_plan.md  # Architecture planning document
├── pyproject.toml                  # uv package manager config
├── .env                            # Database credentials
├── main.py                         # Entry point
└── CLAUDE.md                       # This file
```

## Running Services

**Prerequisites**: MySQL, MongoDB, RabbitMQ running locally or via minikube

```bash
# Set up environment
cp .env.example .env  # Configure DB credentials

# Install dependencies (service-specific)
pip install -r python/src/auth/requirements.txt
pip install -r python/src/gateway/requirements.txt

# Run services individually
python python/src/auth/service.py       # Port 5000
python python/src/gateway/server.py     # Port 5001
python python/src/summary/service.py    # Port 5002

# Docker (auth service only currently)
docker build -f python/src/auth/Dockerfile -t auth-service .
docker run -p 5000:5000 --env-file .env auth-service
```

## Database Configuration

**MySQL** (auth service):
```
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DB=auth
MYSQL_PORT=3306
```

**MongoDB** (gateway/summary):
- Connection: `mongodb://host.minikube.internal:27017/videos`
- Uses GridFS for file storage
- Collections: `fs.files`, `fs.chunks`, `summaries`, `categories`

## Code Conventions

**Service Structure**:
- Single-file implementation per service (`service.py` or `server.py`)
- Flask app with individual port configuration
- Environment-based config via `os.getenv()`

**API Patterns**:
```python
# JWT validation pattern (gateway)
headers = {'Authorization': request.headers.get('Authorization')}
response = requests.get('http://auth-service:5000/validate', headers=headers)

# MongoDB GridFS pattern (gateway)
mongo_client = MongoClient(mongo_uri)
db = mongo_client.get_database()
fs = gridfs.GridFS(db)
file_id = fs.put(file_data, filename=name, contentType=content_type)

# RabbitMQ pattern (planned)
connection = pika.BlockingConnection(pika.ConnectionParameters(host))
channel = connection.channel()
channel.queue_declare(queue='video_uploads')
channel.basic_publish(exchange='', routing_key='video_uploads', body=message)
```

**Error Response Format**:
```python
return jsonify({'error': 'message'}), status_code
```

**Authentication Flow**:
1. Register/Login → Auth service returns JWT
2. Client includes `Authorization: Bearer <token>` header
3. Gateway validates token via auth service `/validate` endpoint
4. Protected routes return 401 if validation fails

## Key Dependencies

**Core**: `flask>=3.1.2`, `flask-mysqldb>=2.0.0`, `flask-pymongo>=3.0.1`, `pyjwt>=2.11.0`, `pika>=1.3.2`

## Implementation Status

### ✅ Complete
- **Auth Service**: Full Flask service with MySQL integration
  - POST `/register` - User registration (username, email, password)
  - POST `/login` - User login, returns JWT token
  - GET `/validate` - JWT token validation
  - JWT expires in 1 day (86400 seconds)

- **Summary Service**: AI-powered file summarization
  - POST `/summarize` - Generate file summary via external AI API
  - GET `/summaries` - List all summaries
  - GET `/summary/<id>` - Get specific summary
  - POST `/categories` - Create custom category
  - GET `/categories` - List all categories
  - External AI endpoint: `https://aigcmock-production.up.railway.app/ai/summary`

### 🚧 In Progress
- **API Gateway** (`/python/src/gateway/server.py`)
  - JWT validation via auth service integration (done)
  - MongoDB connection setup (done)
  - Missing: `/upload`, `/download/<filename>` endpoints
  - Missing: RabbitMQ message publishing

### ❌ Not Started
- Video Converter Service (FFmpeg integration)
- Notification Service (email notifications)
- React Web UI
- Kubernetes deployment manifests
- User registration endpoint in gateway
- Docker images for gateway/summary services

## Running Services

**Prerequisites**: MySQL, MongoDB, RabbitMQ running locally or via minikube

```bash
# Set up environment
cp .env.example .env  # Configure DB credentials

# Install dependencies (service-specific)
pip install -r python/src/auth/requirements.txt
pip install -r python/src/gateway/requirements.txt

# Run services individually
python python/src/auth/service.py       # Port 5000
python python/src/gateway/server.py     # Port 5001
python python/src/summary/service.py    # Port 5002

# Docker (auth service only currently)
docker build -f python/src/auth/Dockerfile -t auth-service .
docker run -p 5000:5000 --env-file .env auth-service
```

**uv Package Manager** (configured in pyproject.toml):
```bash
uv pip install -r requirements.txt
uv pip freeze
uv sync
uv add package-name
```

## Database Configuration

### MySQL (Auth Service)
Environment variables in `.env`:
```env
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=root
MYSQL_DB=auth
MYSQL_PORT=3306
```

**User Table Schema** (created by auth service):
```sql
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
)
```

### MongoDB (Gateway/Summary Services)
- **Connection**: `mongodb://host.minikube.internal:27017/videos`
- **Database**: `videos`

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

`categories` - Custom categories:
```javascript
{
  _id: ObjectId,
  name: string,               // Category name
  description: string,        // Category description (optional)
  created_at: ISODate         // Creation timestamp
}
```

**GridFS Usage Pattern**:
```python
import gridfs
from pymongo import MongoClient

client = MongoClient(mongo_uri)
db = client.get_database()
fs = gridfs.GridFS(db)

# Store video file
video_id = fs.put(
    file_data,
    filename="video.mp4",
    contentType="video/mp4",
    metadata={"file_type": "video", "user_id": "123"}
)

# Store MP3 file (converted)
mp3_id = fs.put(
    mp3_data,
    filename="video.mp3",
    contentType="audio/mpeg",
    metadata={
        "file_type": "mp3",
        "user_id": "123",
        "converted_from": video_id,
        "status": "completed"
    }
)

# Retrieve file by ID
file = fs.get(file_id)
data = file.read()
metadata = file.metadata
```

## Code Conventions

### Service Structure Pattern
```python
# Single-file implementation per service
from flask import Flask, request, jsonify
app = Flask(__name__)

# Environment-based configuration
mysql_host = os.getenv('MYSQL_HOST', 'localhost')
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/videos')

# Run on specific port
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

### API Patterns

**JWT Validation (Gateway → Auth Service)**:
```python
headers = {'Authorization': request.headers.get('Authorization')}
response = requests.get('http://auth-service:5000/validate', headers=headers)
if response.status_code != 200:
    return jsonify({'error': 'Invalid token'}), 401
```

**MongoDB GridFS (File Storage)**:
```python
from pymongo import MongoClient
import gridfs

mongo_client = MongoClient(mongo_uri)
db = mongo_client.get_database()
fs = gridfs.GridFS(db)

# Store file
file_id = fs.put(file_data, filename=name, contentType=content_type)

# Retrieve file
file_data = fs.get(file_id).read()
```

**RabbitMQ (Message Publishing - Planned)**:
```python
import pika

connection = pika.BlockingConnection(pika.ConnectionParameters(host))
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
1. User registers/logs in via Auth Service → receives JWT token
2. Client includes `Authorization: Bearer <token>` header in requests
3. Gateway validates token by calling Auth Service `/validate` endpoint
4. Protected routes return 401 if validation fails

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
3. **Kubernetes**: Production deployment (planned)
4. **Configuration**: Environment-specific via `.env` files, ConfigMaps, Secrets

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
- Root `.env` for shared database credentials
- Service-specific environment variables
- Kubernetes ConfigMaps and Secrets (planned)
- AI service endpoint configured as environment variable

---

**Note**: This is a work-in-progress microservice project. While the authentication and summary services are functional, many planned components from the architecture document are not yet implemented. The codebase follows basic Flask patterns but needs enhancement for production readiness.
