param(
  [string]$Service = ""
)

if ([string]::IsNullOrWhiteSpace($Service)) {
  docker compose logs -f --tail=200
} else {
  docker compose logs -f --tail=200 $Service
}
