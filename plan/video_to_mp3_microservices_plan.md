---
name: Video to MP3 Microservices with GenAI Summary
overview: Build a microservice architecture for video to MP3 conversion with Python, Kubernetes, RabbitMQ, MongoDB, and MySQL. The system includes API Gateway, Video Converter, GenAI Summary Service, Notification Service, and User Authentication with a Web UI client.
todos: []
isProject: false
---

# Video to MP3 Converter with GenAI Summary - Microservice Architecture Plan

## Architecture Overview

The system follows an event-driven microservice pattern:

```mermaid
flowchart TD
    subgraph Clients
        WEB[Web UI]
    end

    subgraph Kubernetes["Kubernetes Cluster"]
        subgraph Gateway["API Gateway Service"]
            GW[API Gateway]
        end

        subgraph Converter["Video Converter Service"]
            VC[Video Converter Worker]
        end

        subgraph Summary["GenAI Summary Service"]
            GS[Summary Worker]
        end

        subgraph Notif["Notification Service"]
            NS[Notification Worker]
        end

        subgraph Auth["Authentication Service"]
            AUTH[Auth Service]
        end

        subgraph Messaging["RabbitMQ"]
            QUEUE[RabbitMQ Message Queue]
        end

        subgraph Storage["Databases"]
            MONGO[(MongoDB<br/>Video/MP3/Summaries)]
            MYSQL[(MySQL<br/>User Auth)]
        end

        subgraph External["External APIs"]
            WHISPER[Whisper API<br/>Voice-to-Text]
            OPENAI[OpenAI GPT-4.1<br/>Text Summary]
        end
    end

    WEB -->|Upload Video| GW
    WEB -->|Download MP3| GW
    WEB -->|View Summary| GW
    WEB -->|Login/Register| AUTH

    GW -->|Store Video| MONGO
    GW -->|Publish: New Video| QUEUE
    GW -->|Retrieve MP3| MONGO
    GW -->|Retrieve Summary| MONGO

    QUEUE -->|video: New Video| VC
    VC -->|Retrieve Video| MONGO
    VC -->|Store MP3| MONGO
    VC -->|mp3: Conversion Done| QUEUE

    QUEUE -->|mp3: Conversion Done| GS
    GS -->|Retrieve MP3| MONGO
    GS -->|Transcribe Audio| WHISPER
    GS -->|Generate Summary| OPENAI
    GS -->|Store Summary| MONGO
    GS -->|summary: Ready| QUEUE

    QUEUE -->|summary: Ready| NS
    NS -->|Send Email Notification| WEB

    AUTH -->|User Data| MYSQL
    GW -->|Verify JWT| AUTH
```

## Project Structure

```
converter_video_mp3/
├── services/
│   ├── api-gateway/           # FastAPI gateway service
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   ├── upload.py
│   │   │   │   ├── download.py
│   │   │   │   └── auth.py
│   │   │   ├── models/
│   │   │   ├── services/
│   │   │   └── config.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── k8s/
│   │       ├── deployment.yaml
│   │       └── service.yaml
│   │
│   ├── video-converter/       # FFmpeg-based converter worker
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── worker.py
│   │   │   ├── converter.py
│   │   │   └── config.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── k8s/
│   │       ├── deployment.yaml
│   │       └── service.yaml
│   │
│   ├── summary-service/       # GenAI summary worker
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── worker.py
│   │   │   ├── transcribe.py    # Whisper API integration
│   │   │   ├── summarize.py     # OpenAI GPT-4.1 integration
│   │   │   └── config.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── k8s/
│   │       ├── deployment.yaml
│   │       └── service.yaml
│   │
│   ├── notification-service/  # Email notification worker
│   │   ├── app/
│   │   │   ├── main.py
│   │   │   ├── worker.py
│   │   │   ├── email_sender.py
│   │   │   └── config.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── k8s/
│   │       ├── deployment.yaml
│   │       └── service.yaml
│   │
│   └── auth-service/          # User authentication service
│       ├── app/
│       │   ├── main.py
│       │   ├── routers/
│       │   │   ├── auth.py
│       │   │   └── users.py
│       │   ├── models/
│       │   │   └── user.py
│       │   ├── services/
│       │   │   └── auth.py
│       │   ├── db.py
│       │   └── config.py
│       ├── Dockerfile
│       ├── requirements.txt
│       └── k8s/
│           ├── deployment.yaml
│           └── service.yaml
│
├── web-ui/                    # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   │   ├── UploadPage.jsx
│   │   │   ├── DownloadPage.jsx
│   │   │   └── LoginPage.jsx
│   │   └── services/
│   │       └── api.js
│   ├── package.json
│   └── Dockerfile
│
├── k8s/                       # Kubernetes manifests
│   ├── mongodb/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── pvc.yaml
│   ├── mysql/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── pvc.yaml
│   ├── rabbitmq/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── configmaps/
│   │   └── app-config.yaml
│   └── secrets/
│       └── app-secrets.yaml
│
├── scripts/
│   ├── setup-local.sh          # Local setup script
│   └── deploy-k8s.sh          # Kubernetes deployment script
│
├── pyproject.toml              # Root Python config
├── docker-compose.yml          # Local development
├── README.md                   # Updated documentation
└── DEPLOYMENT.md              # Deployment guide
```

## Technology Stack

### Core Technologies
- **Python 3.12+** - All microservices
- **FastAPI** - API Gateway and Auth Service
- **Celery + RabbitMQ** - Task queue and message broker
- **FFmpeg** - Video to MP3 conversion
- **OpenAI Whisper API** - Voice-to-text transcription
- **OpenAI GPT-4.1 API** - Text summarization
- **React 18** - Web UI client
- **Kubernetes** - Orchestration and deployment
- **MongoDB** - GridFS for file storage (videos/MP3s) + summaries collection
- **MySQL** - User authentication and JWT management
- **JWT** - Authentication tokens

### Key Python Libraries
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pika` - RabbitMQ client
- `pymongo` - MongoDB driver
- `motor` - Async MongoDB driver
- `sqlalchemy` - MySQL ORM
- `bcrypt` - Password hashing
- `python-jose` - JWT handling
- `python-multipart` - File uploads
- `aiosmtplib` - Async email sending
- `openai` - OpenAI API client (Whisper + GPT-4.1)
- `httpx` - Async HTTP client for API calls
- `pydub` - Audio processing for Whisper

## Implementation Tasks

### Phase 1: Infrastructure Setup
1. Create project directory structure
2. Set up Docker Compose for local development
3. Create Kubernetes manifests for:
   - MongoDB with PersistentVolumeClaim
   - MySQL with PersistentVolumeClaim
   - RabbitMQ
   - ConfigMaps and Secrets
4. Create root pyproject.toml for workspace management

### Phase 2: Authentication Service
1. Implement user registration/login endpoints in `[services/auth-service/app/routers/auth.py](services/auth-service/app/routers/auth.py)`
2. Create User model in `[services/auth-service/app/models/user.py](services/auth-service/app/models/user.py)` with SQLAlchemy
3. Implement JWT token generation and validation
4. Set up MySQL database connection in `[services/auth-service/app/db.py](services/auth-service/app/db.py)`
5. Create Dockerfile and Kubernetes manifests

### Phase 3: API Gateway
1. Create FastAPI application in `[services/api-gateway/app/main.py](services/api-gateway/app/main.py)`
2. Implement upload endpoint in `[services/api-gateway/app/routers/upload.py](services/api-gateway/app/routers/upload.py)`:
   - Authenticate JWT
   - Store video in MongoDB GridFS
   - Publish message to RabbitMQ queue
3. Implement download endpoint in `[services/api-gateway/app/routers/download.py](services/api-gateway/app/routers/download.py)`:
   - Verify JWT and job completion
   - Retrieve MP3 from MongoDB GridFS
4. Create Dockerfile and Kubernetes manifests

### Phase 4: Video Converter Service
1. Create Celery worker in `[services/video-converter/app/worker.py](services/video-converter/app/worker.py)`
2. Implement FFmpeg conversion logic in `[services/video-converter/app/converter.py](services/video-converter/app/converter.py)`
3. Worker flow:
   - Consume message from RabbitMQ
   - Retrieve video from MongoDB
   - Convert to MP3 using FFmpeg
   - Store MP3 in MongoDB GridFS
   - Publish completion message to RabbitMQ
4. Create Dockerfile with FFmpeg installation and Kubernetes manifests

### Phase 5: GenAI Summary Service
1. Create Celery worker in `[services/summary-service/app/worker.py](services/summary-service/app/worker.py)`
2. Implement Whisper API integration in `[services/summary-service/app/transcribe.py](services/summary-service/app/transcribe.py)`:
   - Retrieve MP3 from MongoDB GridFS
   - Convert audio to suitable format for Whisper (16kHz, mono)
   - Call Whisper API for transcription
   - Return transcript text
3. Implement OpenAI GPT-4.1 integration in `[services/summary-service/app/summarize.py](services/summary-service/app/summarize.py)`:
   - Accept transcript text
   - Create prompt for summarization
   - Call OpenAI Chat Completions API with gpt-4-turbo or gpt-4o
   - Parse and return summary
4. Worker flow:
   - Consume message from RabbitMQ mp3 queue
   - Retrieve MP3 from MongoDB GridFS
   - Transcribe audio using Whisper API
   - Generate summary using OpenAI GPT-4.1
   - Store summary in MongoDB summaries collection with metadata
   - Publish completion message to RabbitMQ summary queue
5. Create Dockerfile and Kubernetes manifests
6. Configure API keys in Kubernetes Secret

### Phase 6: Notification Service
1. Create Celery worker in `[services/notification-service/app/worker.py](services/notification-service/app/worker.py)`
2. Implement email sender in `[services/notification-service/app/email_sender.py](services/notification-service/app/email_sender.py)`
3. Worker flow:
   - Consume completion message from RabbitMQ
   - Send email with download link and unique ID
4. Create Dockerfile and Kubernetes manifests

### Phase 7: Web UI
1. Initialize React app with Vite
2. Create authentication pages in `[web-ui/src/pages/LoginPage.jsx](web-ui/src/pages/LoginPage.jsx)`
3. Create upload page with progress tracking in `[web-ui/src/pages/UploadPage.jsx](web-ui/src/pages/UploadPage.jsx)`
4. Create download page with MP3 and summary display in `[web-ui/src/pages/DownloadPage.jsx](web-ui/src/pages/DownloadPage.jsx)`
   - Add summary view section
   - Display transcript text
   - Display generated summary
5. Implement API client in `[web-ui/src/services/api.js](web-ui/src/services/api.js)`
6. Create Dockerfile and Kubernetes manifests

### Phase 8: Integration & Testing
1. Update README with architecture and usage instructions
2. Create DEPLOYMENT.md with K8s setup guide
3. Create setup scripts for local and K8s deployment
4. Test end-to-end flow:
   - User registers/logs in
   - Uploads video
   - Waits for conversion
   - System generates transcript and summary
   - Receives email notification
   - Downloads MP3
   - Views transcript and summary

## Key Design Decisions

### MongoDB GridFS for Files
- Use GridFS for storing large video files and MP3s
- Store metadata in separate collection
- Unique file IDs for all operations

### RabbitMQ Queue Design
- Queue 1: `video` - Video conversion jobs
- Queue 2: `mp3` - MP3 ready for transcription/summary
- Queue 3: `summary` - Summary ready for notification
- Queue 4: `notification` - Email notifications
- Use direct exchanges for routing

### JWT Flow
1. User authenticates with Auth Service
2. Receives JWT token
3. Includes JWT in all API requests
4. Gateway validates JWT via Auth Service

### Error Handling
- Dead letter queues for failed messages
- Retry logic for conversion failures
- Email notifications for errors
- Proper HTTP status codes for all endpoints

## Configuration Management

### Environment Variables
- MongoDB connection string
- MySQL connection string
- RabbitMQ connection details
- JWT secret key
- Email SMTP settings
- FFmpeg paths
- OpenAI API key (for Whisper and GPT-4.1)
- Whisper API endpoint
- ChatGPT model (gpt-4-turbo or gpt-4o)

### Kubernetes ConfigMaps
Application configuration (non-sensitive):
- Queue names
- Database names
- Port numbers
- Retry settings

### Kubernetes Secrets
Sensitive data:
- Database passwords
- JWT secret
- SMTP credentials
- OpenAI API key

## Deployment Strategy

### Local Development
Use `docker-compose.yml` for running all services locally with:
- Hot reload for development
- Shared volume for file storage
- Local RabbitMQ, MongoDB, MySQL instances

### Kubernetes Production
- Separate namespaces for staging/production
- Horizontal Pod Autoscaling for workers
- PersistentVolumeClaims for data persistence
- Health checks and liveness probes
- Ingress controller for external access

## GenAI Summary Service Implementation Details

### Overview
The Summary Service processes MP3 audio files to generate intelligent text summaries using OpenAI's Whisper API for speech-to-text and GPT-4.1 for text summarization.

### Architecture

```mermaid
flowchart LR
    MQ[RabbitMQ<br/>mp3 queue] --> Worker[Summary Worker]
    Worker --> Retrieve[Retrieve MP3<br/>from MongoDB]
    Retrieve --> Process[Process Audio]
    Process --> Whisper[Whisper API<br/>Speech-to-Text]
    Whisper --> Transcript[Transcript Text]
    Transcript --> OpenAI[OpenAI GPT-4.1<br/>Summarization]
    OpenAI --> Summary[Summary Text]
    Summary --> Store[Store in MongoDB<br/>summaries collection]
    Store --> MQ2[RabbitMQ<br/>summary queue]
```

### MongoDB Schema - Summaries Collection

```javascript
{
  _id: ObjectId,
  mp3_fid: ObjectId,              // Reference to fs.files._id (MP3 file)
  video_fid: ObjectId,            // Reference to original video
  username: string,               // User who uploaded
  transcript: string,             // Full transcript from Whisper
  summary: string,                // Generated summary from GPT-4.1
  transcript_length: number,      // Character count of transcript
  summary_length: number,         // Character count of summary
  processing_time_ms: number,     // Total processing time
  created_at: ISODate,            // Creation timestamp
  status: string                  // "processing", "completed", "failed"
}
```

### OpenAI API Integration

#### 1. Whisper API (Speech-to-Text)
- **Endpoint**: `https://api.openai.com/v1/audio/transcriptions`
- **Model**: `whisper-1`
- **Audio Requirements**:
  - Format: MP3, WAV, M4A, etc.
  - Sample rate: 16kHz or higher
  - Size limit: 25 MB
- **Response**: JSON with `text` field containing transcript

#### 2. GPT-4.1 API (Summarization)
- **Endpoint**: `https://api.openai.com/v1/chat/completions`
- **Model**: `gpt-4-turbo` or `gpt-4o` (latest)
- **Prompt Template**:
  ```python
  prompt = f"""
  Please provide a concise summary of the following transcript.
  Focus on key points, main topics, and important conclusions.

  Transcript:
  {transcript}

  Summary:
  """
  ```
- **Parameters**:
  - `max_tokens`: 500-1000 (configurable)
  - `temperature`: 0.3-0.7 (for focused summaries)

### Configuration

#### Environment Variables
```env
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_WHISPER_MODEL=whisper-1
OPENAI_CHAT_MODEL=gpt-4-turbo
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.5

# Service Configuration
MONGO_URI=mongodb://admin:password@mongodb:27017/gateway?authSource=admin
RABBITMQ_HOST=rabbitmq
RABBITMQ_USER=admin
RABBITMQ_PASS=guest
MP3_QUEUE=mp3
SUMMARY_QUEUE=summary

# Processing Configuration
MAX_AUDIO_SIZE_MB=25
TRANSCRIPT_TIMEOUT=300
SUMMARY_TIMEOUT=60
```

### Error Handling

#### Retry Logic
- **Whisper API**: 3 retries with exponential backoff (1s, 2s, 4s)
- **GPT-4.1 API**: 3 retries with exponential backoff (2s, 4s, 8s)
- **Dead Letter Queue**: Failed messages sent to `summary.dlq` for manual inspection

#### Error Categories
1. **Audio Processing Errors**:
   - Invalid audio format
   - Corrupted audio file
   - File too large (>25 MB)

2. **API Errors**:
   - Rate limiting (429)
   - Invalid API key (401)
   - Insufficient quota (429)
   - Server errors (5xx)

3. **Database Errors**:
   - Connection failures
   - Write failures
   - GridFS retrieval errors

### Cost Optimization

#### Whisper API Pricing
- **$0.006 / minute** (whisper-1)
- Example: 10-minute video = $0.06

#### GPT-4.1 API Pricing
- **Input**: ~$0.01 / 1K tokens (gpt-4-turbo)
- **Output**: ~$0.03 / 1K tokens (gpt-4-turber)
- Example: 10-minute transcript (~1500 tokens) + 500 token summary ≈ $0.03

**Total per 10-minute video**: ~$0.09

### Monitoring & Observability

#### Metrics to Track
- Processing time per audio file
- Average transcript length
- Average summary length
- API call success rate
- Error rate by category
- Queue depth (mp3, summary)

#### Logging
```python
logger.info(f"Processing mp3_fid: {mp3_fid}")
logger.info(f"Transcript generated: {len(transcript)} chars")
logger.info(f"Summary generated: {len(summary)} chars")
logger.info(f"Total processing time: {processing_time_ms}ms")
```

### API Response Examples

#### Whisper Response
```json
{
  "text": "This is the transcript of the audio file...",
  "task": "transcribe",
  "language": "english",
  "duration": 120.5,
  "words": 245
}
```

#### GPT-4.1 Response
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "gpt-4-turbo",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "The video discusses the importance of microservice architecture..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 1500,
    "completion_tokens": 250,
    "total_tokens": 1750
  }
}
```

### Service Implementation Flow

```python
# 1. Consume message from mp3 queue
message = {
    "video_fid": "69932794033b89d77feb6915",
    "mp3_fid": "69932794033b89d77feb6916",
    "username": "kshilkrot@email.com"
}

# 2. Retrieve MP3 from MongoDB GridFS
mp3_data = fs_mp3s.get(ObjectId(message["mp3_fid"]))

# 3. Transcribe using Whisper API
transcript = whisper_client.transcribe(audio_data)

# 4. Summarize using GPT-4.1 API
summary = openai_client.chat.completions.create(
    model="gpt-4-turbo",
    messages=[{"role": "user", "content": f"Summarize: {transcript}"}]
)

# 5. Store in MongoDB
summaries_collection.insert_one({
    "mp3_fid": ObjectId(message["mp3_fid"]),
    "video_fid": ObjectId(message["video_fid"]),
    "username": message["username"],
    "transcript": transcript,
    "summary": summary.choices[0].message.content,
    "created_at": datetime.utcnow(),
    "status": "completed"
})

# 6. Publish to summary queue
channel.basic_publish(
    exchange="",
    routing_key="summary",
    body=json.dumps({
        "video_fid": message["video_fid"],
        "mp3_fid": message["mp3_fid"],
        "summary_fid": str(summary_id),
        "username": message["username"]
    })
)
```

### Testing Strategy

#### Unit Tests
- Mock Whisper API responses
- Mock OpenAI API responses
- Test error handling scenarios
- Verify MongoDB writes

#### Integration Tests
- Test with actual audio files
- Verify end-to-end flow
- Test queue message processing
- Validate database schema

#### Performance Tests
- Measure processing time for various audio lengths
- Test concurrent processing
- Validate API rate limiting handling
- Monitor memory usage

### Future Enhancements
1. **Multi-language Support**: Detect language and use appropriate Whisper model
2. **Summary Customization**: Allow users to specify summary length/style
3. **Key Topics Extraction**: Extract and tag main topics
4. **Sentiment Analysis**: Add sentiment analysis to summaries
5. **Timestamping**: Add timestamps to transcript for video synchronization