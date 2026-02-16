#!/bin/bash
# Deployment script for Summary Service

set -e

NAMESPACE="video-converter"
SERVICE_NAME="summary"

echo "🚀 Deploying Summary Service to Kubernetes..."

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY environment variable not set"
    echo "Please set it before running this script:"
    echo "  export OPENAI_API_KEY=sk-your-key-here"
    echo ""
    echo "Or the script will use the placeholder value from secret.yaml"
fi

# Create namespace
echo "📦 Creating namespace: $NAMESPACE"
kubectl apply -f namespace.yaml

# Create configmap
echo "⚙️  Creating configmap"
kubectl apply -f configmap.yaml

# Create or update secret
if [ -n "$OPENAI_API_KEY" ]; then
    echo "🔑 Creating secret with provided API key"
    kubectl create secret generic summary-secrets \
        --from-literal=OPENAI_API_KEY="$OPENAI_API_KEY" \
        --from-literal=RABBITMQ_PASS=guest \
        --namespace=$NAMESPACE \
        --dry-run=client -o yaml | kubectl apply -f -
else
    echo "🔑 Creating secret from file (ensure secret.yaml has valid API key)"
    kubectl apply -f secret.yaml
fi

# Create deployment
echo "🚀 Creating deployment"
kubectl apply -f deployment.yaml

# Create service (optional, for monitoring)
echo "🌐 Creating service"
kubectl apply -f service.yaml

# Wait for deployment to be ready
echo "⏳ Waiting for deployment to be ready..."
kubectl rollout status deployment/$SERVICE_NAME -n $NAMESPACE --timeout=120s

# Show pod status
echo ""
echo "✅ Deployment complete!"
echo ""
echo "Pod status:"
kubectl get pods -n $NAMESPACE -l app=$SERVICE_NAME

echo ""
echo "📋 Logs:"
echo "  kubectl logs -n $NAMESPACE -l app=$SERVICE_NAME -f"
echo ""
echo "🔍 To check details:"
echo "  kubectl describe pod -n $NAMESPACE -l app=$SERVICE_NAME"
