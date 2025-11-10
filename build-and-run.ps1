# Script to build and run the Docker environment
# Run this from the take68 directory: ./build-and-run.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== TFLite Model Maker Setup ===" -ForegroundColor Green
Write-Host ""

# Check if Docker is installed
Write-Host "[1/3] Checking Docker installation..." -ForegroundColor Cyan
try {
    docker --version | Out-Null
    Write-Host "[OK] Docker is installed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Build the Docker image
Write-Host ""
Write-Host "[2/3] Building Docker image (this may take 5-15 minutes)..." -ForegroundColor Cyan
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker build failed" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Docker image built successfully" -ForegroundColor Green

# Run environment check
Write-Host ""
Write-Host "[3/3] Running environment check inside container..." -ForegroundColor Cyan
Write-Host ""
docker-compose run --rm tflmm python /workspace/check-training-env.py

Write-Host ""
Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "To train your model, run:" -ForegroundColor Yellow
Write-Host "  docker-compose run --rm tflmm python /workspace/train.py" -ForegroundColor White
Write-Host ""
Write-Host "To run a bash shell in the container:" -ForegroundColor Yellow
Write-Host "  docker-compose run --rm tflmm bash" -ForegroundColor White
