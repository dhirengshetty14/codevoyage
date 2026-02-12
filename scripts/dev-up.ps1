Param(
  [switch]$Build,
  [int]$WorkerScale = 2
)

$composeArgs = @("up", "-d")
if ($Build) {
  $composeArgs += "--build"
}

Write-Host "Starting CodeVoyage services..." -ForegroundColor Cyan
docker compose @composeArgs

Write-Host "Scaling celery worker to $WorkerScale instance(s)..." -ForegroundColor Cyan
docker compose up -d --scale celery-worker=$WorkerScale

Write-Host "Done. Frontend: http://localhost:3000  API: http://localhost:8000/docs" -ForegroundColor Green
