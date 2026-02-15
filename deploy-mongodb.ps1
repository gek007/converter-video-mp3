# Deploy MongoDB to Kubernetes
Write-Host "Deploying MongoDB to Kubernetes..." -ForegroundColor Green

# Apply MongoDB manifests
Write-Host "`nApplying MongoDB ConfigMap..." -ForegroundColor Cyan
kubectl apply -f python/src/mongo/manifests/configmap.yaml

Write-Host "`nApplying MongoDB Secret..." -ForegroundColor Cyan
kubectl apply -f python/src/mongo/manifests/secret.yaml

Write-Host "`nApplying MongoDB PVC..." -ForegroundColor Cyan
kubectl apply -f python/src/mongo/manifests/pvc.yaml

Write-Host "`nApplying MongoDB Service..." -ForegroundColor Cyan
kubectl apply -f python/src/mongo/manifests/service.yaml

Write-Host "`nApplying MongoDB StatefulSet..." -ForegroundColor Cyan
kubectl apply -f python/src/mongo/manifests/statefulset.yaml

# Wait for MongoDB to be ready
Write-Host "`nWaiting for MongoDB to be ready..." -ForegroundColor Yellow
kubectl wait --for=condition=ready pod -l app=mongodb --timeout=300s

# Update converter ConfigMap
Write-Host "`nUpdating Converter ConfigMap..." -ForegroundColor Cyan
kubectl apply -f python/src/converter/manifests/configmap.yaml

# Update gateway ConfigMap
Write-Host "`nUpdating Gateway ConfigMap..." -ForegroundColor Cyan
kubectl apply -f python/src/gateway/manifests/configmap.yaml

# Restart converter deployment
Write-Host "`nRestarting Converter deployment..." -ForegroundColor Cyan
kubectl rollout restart deployment/converter

# Restart gateway deployment
Write-Host "`nRestarting Gateway deployment..." -ForegroundColor Cyan
kubectl rollout restart deployment/gateway

# Check status
Write-Host "`nWaiting for deployments to be ready..." -ForegroundColor Yellow
kubectl rollout status deployment/converter --timeout=300s
kubectl rollout status deployment/gateway --timeout=300s

Write-Host "`n=== Deployment Status ===" -ForegroundColor Green
kubectl get pods -l app=mongodb
kubectl get pods -l app=converter
kubectl get pods -l app=gateway

Write-Host "`n=== Services ===" -ForegroundColor Green
kubectl get svc mongodb

Write-Host "`nMongoDB deployment completed successfully!" -ForegroundColor Green
