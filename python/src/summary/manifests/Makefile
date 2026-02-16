.PHONY: help deploy deploy-kustomize delete logs status scale clean

# Default target
help:
	@echo "Summary Service - Kubernetes Deployment"
	@echo ""
	@echo "Available targets:"
	@echo "  make deploy          - Deploy using kubectl"
	@echo "  make deploy-kustomize - Deploy using kustomize"
	@echo "  make delete          - Delete all resources"
	@echo "  make logs            - Show logs from all pods"
	@echo "  make status          - Show deployment status"
	@echo "  make scale N=4       - Scale deployment to N replicas"
	@echo "  make restart         - Restart deployment"
	@echo "  make clean           - Remove .env.secrets file"

# Deploy using kubectl
deploy:
	@echo "Deploying summary service..."
	@if [ -z "$(OPENAI_API_KEY)" ]; then \
		echo "⚠️  OPENAI_API_KEY not set. Using value from secret.yaml"; \
		kubectl apply -f .; \
	else \
		echo "Using OPENAI_API_KEY from environment"; \
		kubectl create namespace video-converter --dry-run=client -o yaml | kubectl apply -f -; \
		kubectl create configmap summary-config --namespace=video-converter --from-file=configmap.yaml --dry-run=client -o yaml | kubectl apply -f -; \
		kubectl create secret generic summary-secrets \
			--from-literal=OPENAI_API_KEY=$(OPENAI_API_KEY) \
			--from-literal=RABBITMQ_PASS=guest \
			--namespace=video-converter \
			--dry-run=client -o yaml | kubectl apply -f -; \
		kubectl apply -f deployment.yaml; \
		kubectl apply -f service.yaml; \
	fi
	@echo "Waiting for deployment..."
	kubectl rollout status deployment/summary -n video-converter --timeout=120s
	@echo "✅ Deployment complete!"

# Deploy using kustomize
deploy-kustomize:
	@echo "Deploying summary service using kustomize..."
	@if [ ! -f .env.secrets ]; then \
		echo "❌ .env.secrets file not found. Copy .env.secrets.example and add your API key:"; \
		echo "   cp .env.secrets.example .env.secrets"; \
		exit 1; \
	fi
	kubectl apply -k .
	@echo "Waiting for deployment..."
	kubectl rollout status deployment/summary -n video-converter --timeout=120s
	@echo "✅ Deployment complete!"

# Delete all resources
delete:
	@echo "Deleting summary service..."
	kubectl delete -f .
	@echo "✅ Deletion complete!"

# Show logs
logs:
	kubectl logs -n video-converter -l app=summary -f --tail=50

# Show status
status:
	@echo "=== Namespace ==="
	kubectl get namespace video-converter
	@echo ""
	@echo "=== Pods ==="
	kubectl get pods -n video-converter -l app=summary
	@echo ""
	@echo "=== Deployment ==="
	kubectl get deployment summary -n video-converter
	@echo ""
	@echo "=== Recent Events ==="
	kubectl get events -n video-converter --sort-by='.lastTimestamp' | tail -10

# Scale deployment
scale:
	@if [ -z "$(N)" ]; then \
		echo "Usage: make scale N=4"; \
		exit 1; \
	fi
	kubectl scale deployment/summary --replicas=$(N) -n video-converter
	@echo "✅ Scaled to $(N) replicas"

# Restart deployment
restart:
	kubectl rollout restart deployment/summary -n video-converter
	@echo "✅ Deployment restarted"

# Clean local files
clean:
	rm -f .env.secrets
	@echo "✅ Cleaned .env.secrets file"

# Build and load Docker image (for minikube)
build:
	@echo "Building Docker image..."
	docker build -f ../../Dockerfile -t gek007/summary:latest ../../
	@echo "Loading image into minikube..."
	minikube image load gek007/summary:latest
	@echo "✅ Image built and loaded"
