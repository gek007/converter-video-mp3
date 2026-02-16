# Kubernetes Deployment Manifests - Summary Service

This directory contains Kubernetes manifests for deploying the GenAI Summary service.

## Prerequisites

- Kubernetes cluster (minikube, AWS EKS, GKE, etc.)
- kubectl configured
- OpenAI API key

## Quick Start

### 1. Update OpenAI API Key

Edit `secret.yaml` and replace `your-openai-api-key-here` with your actual OpenAI API key:

```yaml
stringData:
  OPENAI_API_KEY: sk-your-actual-api-key-here
```

Or create the secret from command line:

```bash
kubectl create secret generic summary-secrets \
  --from-literal=OPENAI_API_KEY=sk-your-actual-api-key-here \
  --from-literal=RABBITMQ_PASS=guest \
  --namespace=video-converter \
  --dry-run=client -o yaml | kubectl apply -f -
```

### 2. Deploy to Kubernetes

```bash
# Apply all manifests
kubectl apply -f python/src/summary/manifests/

# Or apply individual files in order
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

### 3. Verify Deployment

```bash
# Check namespace
kubectl get namespace video-converter

# Check pods
kubectl get pods -n video-converter -l app=summary

# View logs
kubectl logs -n video-converter -l app=summary -f

# Check deployment status
kubectl rollout status deployment/summary -n video-converter
```

## Manifests Overview

### namespace.yaml
- Creates the `video-converter` namespace
- Isolates video converter services

### configmap.yaml
- Contains non-sensitive configuration
- MongoDB connection string
- RabbitMQ connection details
- Queue names
- OpenAI model settings
- Processing parameters

### secret.yaml
- Contains sensitive data
- OpenAI API key (REQUIRED - must be updated)
- RabbitMQ password

### deployment.yaml
- Deploys 2 replicas of the summary worker
- Resource limits: 256Mi RAM / 250m CPU (requests), 512Mi RAM / 500m CPU (limits)
- Health checks: liveness and readiness probes
- Pulls image: `gek007/summary:latest`

### service.yaml
- Headless service for monitoring
- Optional: Can be used for metrics collection

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URI` | MongoDB connection string | mongodb://admin:admin123@... |
| `RABBITMQ_HOST` | RabbitMQ hostname | rabbitmq |
| `RABBITMQ_USER` | RabbitMQ username | admin |
| `RABBITMQ_PORT` | RabbitMQ port | 5672 |
| `MP3_QUEUE` | Input queue name | mp3 |
| `SUMMARY_QUEUE` | Output queue name | summary |
| `OPENAI_API_KEY` | OpenAI API key | *REQUIRED* |
| `OPENAI_WHISPER_MODEL` | Whisper model | whisper-1 |
| `OPENAI_CHAT_MODEL` | ChatGPT model | gpt-4-turbo |
| `OPENAI_MAX_TOKENS` | Max tokens for summary | 500 |
| `OPENAI_TEMPERATURE` | Summary creativity | 0.5 |
| `MAX_AUDIO_SIZE_MB` | Max audio file size | 25 |
| `TRANSCRIPT_TIMEOUT` | Transcription timeout (s) | 300 |
| `SUMMARY_TIMEOUT` | Summarization timeout (s) | 60 |
| `LOG_LEVEL` | Logging level | INFO |

## Scaling

To scale the deployment:

```bash
# Scale to 4 replicas
kubectl scale deployment/summary --replicas=4 -n video-converter

# Or edit the deployment
kubectl edit deployment/summary -n video-converter
```

## Monitoring

### View Logs

```bash
# All pods
kubectl logs -n video-converter -l app=summary -f

# Specific pod
kubectl logs -n video-converter deployment/summary -f

# Previous container (if crashed)
kubectl logs -n video-converter deployment/summary --previous
```

### Check Resource Usage

```bash
kubectl top pods -n video-converter -l app=summary
```

## Troubleshooting

### Pod Not Starting

```bash
# Describe pod for details
kubectl describe pod -n video-converter -l app=summary

# Check events
kubectl get events -n video-converter --sort-by='.lastTimestamp'
```

### Common Issues

1. **ImagePullBackOff**
   - Image not found: Build and load image into minikube
   ```bash
   docker build -t gek007/summary:latest python/src/summary/
   minikube image load gek007/summary:latest
   ```

2. **CrashLoopBackOff**
   - Check logs for error: `kubectl logs -n video-converter -l app=summary`
   - Common cause: Missing OPENAI_API_KEY

3. **Missing API Key**
   - Update secret:
   ```bash
   kubectl create secret generic summary-secrets \
     --from-literal=OPENAI_API_KEY=sk-your-key \
     --namespace=video-converter \
     --dry-run=client -o yaml | kubectl apply -f -

   # Restart deployment
   kubectl rollout restart deployment/summary -n video-converter
   ```

### Connectivity Issues

```bash
# Test MongoDB connection
kubectl run -it --rm mongo-test --image=mongo --restart=Never -n video-converter -- \
  mongosh mongodb://admin:admin123@mongodb:27017/gateway?authSource=admin

# Test RabbitMQ connection
kubectl run -it --rm rabbitmq-test --image=rabbitmq:3.12-management --restart=Never -n video-converter -- \
  rabbitmqctl -n rabbitmq list_connections
```

## Updating the Deployment

```bash
# Apply changes to configmap/secret
kubectl apply -f configmap.yaml
kubectl apply -f secret.yaml

# Restart deployment to pick up changes
kubectl rollout restart deployment/summary -n video-converter

# Monitor rollout
kubectl rollout status deployment/summary -n video-converter
```

## Cleanup

```bash
# Delete all resources
kubectl delete -f python/src/summary/manifests/

# Or delete namespace (removes all resources in namespace)
kubectl delete namespace video-converter
```

## Production Considerations

1. **API Key Security**
   - Use proper secret management (e.g., HashiCorp Vault, AWS Secrets Manager)
   - Never commit API keys to version control
   - Rotate API keys regularly

2. **Resource Limits**
   - Adjust based on actual usage
   - Monitor and optimize over time

3. **High Availability**
   - Use multiple replicas (2-4)
   - Set up pod anti-affinity
   - Configure horizontal pod autoscaler

4. **Monitoring**
   - Add Prometheus metrics
   - Set up alerting for failures
   - Track API usage and costs

5. **Cost Management**
   - Monitor OpenAI API usage
   - Set up budget alerts
   - Implement rate limiting if needed

## See Also

- [Service README](../../README.md) - Service overview
- [Deployment Plan](../../../../plan/video_to_mp3_microservices_plan.md) - Architecture details
- [OpenAI Documentation](https://platform.openai.com/docs)
