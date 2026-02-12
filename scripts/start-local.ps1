Write-Host "Starting CodeVoyage services..." -ForegroundColor Cyan
docker compose up -d --build
docker compose ps
Write-Host ""
Write-Host "Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host "API:      http://localhost:8000" -ForegroundColor Green
Write-Host "Flower:   http://localhost:5555" -ForegroundColor Green
