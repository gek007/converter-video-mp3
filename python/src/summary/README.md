# Summary Service

GenAI-powered service for transcribing MP3 audio files and generating intelligent summaries using OpenAI's Whisper API and GPT-4.1.

## Features

- **Speech-to-Text**: Transcribes MP3 audio files using OpenAI Whisper API
- **Text Summarization**: Generates concise summaries using OpenAI GPT-4.1
- **Event-Driven**: Consumes messages from RabbitMQ `mp3` queue
- **MongoDB Storage**: Stores transcripts and summaries in MongoDB `summaries` collection
- **Async Processing**: Handles multiple concurrent audio files

## Architecture

```
RabbitMQ (mp3 queue)
    ↓
Summary Worker
    ↓
┌─────────────────────────────────────┐
│  1. Retrieve MP3 from MongoDB       │
│  2. Transcribe with Whisper API     │
│  3. Summarize with GPT-4.1 API      │
│  4. Store in MongoDB               │
│  5. Publish to summary queue       │
└─────────────────────────────────────┘
    ↓
RabbitMQ (summary queue)
```

## Configuration

### Environment Variables

```env
# MongoDB
MONGO_URI=mongodb://admin:admin123@mongodb:27017/gateway?authSource=admin

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_USER=admin
RABBITMQ_PASS=guest
MP3_QUEUE=mp3
SUMMARY_QUEUE=summary

# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_WHISPER_MODEL=whisper-1
OPENAI_CHAT_MODEL=gpt-4-turbo
OPENAI_MAX_TOKENS=500
OPENAI_TEMPERATURE=0.5

# Processing
MAX_AUDIO_SIZE_MB=25
TRANSCRIPT_TIMEOUT=300
SUMMARY_TIMEOUT=60
```

## Message Format

### Input (from mp3 queue)

```json
{
  "video_fid": "69932794033b89d77feb6915",
  "mp3_fid": "69932794033b89d77feb6916",
  "username": "kshilkrot@email.com"
}
```

### Output (to summary queue)

```json
{
  "video_fid": "69932794033b89d77feb6915",
  "mp3_fid": "69932794033b89d77feb6916",
  "summary_fid": "69932794033b89d77feb6917",
  "username": "kshilkrot@email.com"
}
```

## MongoDB Schema

### Summaries Collection

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

## Installation

### Local Development

```bash
# Install dependencies
cd python/src/summary-service
uv sync

# Set environment variables
cp .env.example .env
# Edit .env with your API keys

# Run worker
uv run worker.py
```

### Docker

```bash
# Build image
docker build -t gek007/summary-service:latest .

# Run container
docker run -d \
  --env-file .env \
  --name summary-service \
  gek007/summary-service:latest
```

### Kubernetes

```bash
# Update secret with your OpenAI API key
kubectl create secret generic summary-service-secrets \
  --from-literal=OPENAI_API_KEY=sk-your-key-here \
  --dry-run=client -o yaml | kubectl apply -f -

# Apply manifests
kubectl apply -f python/src/summary-service/k8s/

# Check pods
kubectl get pods -l app=summary-service

# View logs
kubectl logs -l app=summary-service -f
```

## API Costs

### Whisper API
- **$0.006 / minute** (whisper-1)
- Example: 10-minute video = $0.06

### GPT-4.1 API
- **Input**: ~$0.01 / 1K tokens (gpt-4-turbo)
- **Output**: ~$0.03 / 1K tokens (gpt-4-turbo)
- Example: 10-minute transcript (~1500 tokens) + 500 token summary ≈ $0.03

**Total per 10-minute video**: ~$0.09

## Monitoring

### Key Metrics

- Processing time per audio file
- Average transcript length
- Average summary length
- API call success rate
- Queue depth

### Logging

```python
logger.info(f"Processing mp3_fid: {mp3_fid}")
logger.info(f"Transcript generated: {len(transcript)} chars")
logger.info(f"Summary generated: {len(summary)} chars")
logger.info(f"Total processing time: {processing_time_ms}ms")
```

## Error Handling

### Retry Logic
- **Whisper API**: 3 retries with exponential backoff (1s, 2s, 4s)
- **GPT-4.1 API**: 3 retries with exponential backoff (2s, 4s, 8s)

### Error Categories
1. **Audio Processing Errors**
   - Invalid audio format
   - Corrupted audio file
   - File too large (>25 MB)

2. **API Errors**
   - Rate limiting (429)
   - Invalid API key (401)
   - Insufficient quota (429)
   - Server errors (5xx)

3. **Database Errors**
   - Connection failures
   - Write failures
   - GridFS retrieval errors

## Testing

### Unit Tests
```bash
# Run tests
pytest tests/
```

### Integration Tests
```bash
# Test with actual audio file
python -m pytest tests/integration/test_worker.py
```

## Troubleshooting

### Common Issues

1. **"Audio file too large"**
   - Solution: Compress audio or split into segments
   - Max size: 25 MB (Whisper API limit)

2. **"Rate limit exceeded"**
   - Solution: Implement exponential backoff
   - Reduce concurrent processing

3. **"Invalid API key"**
   - Solution: Verify OPENAI_API_KEY in secrets
   - Check API key has required permissions

4. **"Transcription timeout"**
   - Solution: Increase TRANSCRIPT_TIMEOUT
   - Check network connectivity

## Future Enhancements

- [ ] Multi-language support
- [ ] Customizable summary length/style
- [ ] Key topics extraction
- [ ] Sentiment analysis
- [ ] Timestamping for video synchronization
- [ ] Batch processing support
