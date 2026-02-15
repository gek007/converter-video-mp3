# Rebuild and redeploy converter and gateway services
Write-Host "Rebuilding and redeploying services..." -ForegroundColor Green

# Set Minikube Docker environment
Write-Host "`nSetting up Minikube Docker environment..." -ForegroundColor Cyan
& minikube -p minikube docker-env --shell powershell | Invoke-Expression

# Build converter image
Write-Host "`nBuilding converter image..." -ForegroundColor Cyan
docker build -t gek007/converter:latest -f python/src/converter/Dockerfile python/src/converter

# Build gateway image
Write-Host "`nBuilding gateway image..." -ForegroundColor Cyan
docker build -t gek007/gateway:latest -f python/src/gateway/Dockerfile python/src/gateway

# Apply updated ConfigMaps and Secrets
Write-Host "`nApplying updated ConfigMaps and Secrets..." -ForegroundColor Cyan
kubectl apply -f python/src/converter/manifests/configmap.yaml
kubectl apply -f python/src/converter/manifests/secret.yaml
kubectl apply -f python/src/gateway/manifests/configmap.yaml
kubectl apply -f python/src/gateway/manifests/secret.yaml

# Restart deployments
Write-Host "`nRestarting converter deployment..." -ForegroundColor Cyan
kubectl rollout restart deployment/converter

Write-Host "`nRestarting gateway deployment..." -ForegroundColor Cyan
kubectl rollout restart deployment/gateway

# Wait for rollout to complete
Write-Host "`nWaiting for deployments to be ready..." -ForegroundColor Yellow
kubectl rollout status deployment/converter --timeout=300s
kubectl rollout status deployment/gateway --timeout=300s

# Check status
Write-Host "`n=== Deployment Status ===" -ForegroundColor Green
kubectl get pods -l app=converter
kubectl get pods -l app=gateway

Write-Host "`nDeployment completed!" -ForegroundColor Green
