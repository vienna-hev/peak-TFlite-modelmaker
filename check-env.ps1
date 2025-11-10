# Quick environment check without building (assumes image already built)
# Run this after .\build-and-run.ps1 has been run once

$ErrorActionPreference = "Stop"

Write-Host "=== Quick Environment Check ===" -ForegroundColor Green
Write-Host ""

docker-compose run --rm tflmm python /workspace/check-training-env.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Environment is ready for training!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next step: Run the training script" -ForegroundColor Cyan
    Write-Host "  docker-compose run --rm tflmm python /workspace/train.py" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "✗ Environment check failed. See messages above." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  1. Ensure images and XML annotations are in workspace/data/" -ForegroundColor White
    Write-Host "  2. Check filenames match (image_001.jpg <-> image_001.xml)" -ForegroundColor White
    Write-Host "  3. Verify XML files are valid Pascal VOC format" -ForegroundColor White
    exit 1
}
