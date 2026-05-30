param(
    [string]$ProjectName = "abacos-verify",
    [switch]$SkipWeb
)

$ErrorActionPreference = "Stop"
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$composeFile = Join-Path $repoRoot "infra\docker-compose.yml"
$services = @("postgres", "redis", "api", "worker")
if (-not $SkipWeb) {
    $services += "web"
}

$dockerBin = "C:\Program Files\Docker\Docker\resources\bin"
if (-not (Get-Command docker -ErrorAction SilentlyContinue) -and (Test-Path (Join-Path $dockerBin "docker.exe"))) {
    $env:Path = "$dockerBin;$env:Path"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw "Docker no esta disponible en PATH. Instala Docker Desktop o ejecuta este script en un runner con Docker."
}

Push-Location $repoRoot
try {
    docker compose -p $ProjectName -f $composeFile config --quiet
    docker compose -p $ProjectName -f $composeFile build api worker web
    docker compose -p $ProjectName -f $composeFile up -d $services

    $healthy = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/health" -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200 -and $response.Content -match '"status"\s*:\s*"ok"') {
                $healthy = $true
                break
            }
        } catch {
            Start-Sleep -Seconds 2
        }
    }

    if (-not $healthy) {
        docker compose -p $ProjectName -f $composeFile logs api worker
        throw "La API no respondio correctamente a /api/health dentro del tiempo esperado."
    }

    if (-not $SkipWeb) {
        $webReady = $false
        for ($i = 0; $i -lt 30; $i++) {
            try {
                $response = Invoke-WebRequest -Uri "http://127.0.0.1:3000/login" -UseBasicParsing -TimeoutSec 3
                if ($response.StatusCode -eq 200) {
                    $webReady = $true
                    break
                }
            } catch {
                Start-Sleep -Seconds 2
            }
        }
        if (-not $webReady) {
            docker compose -p $ProjectName -f $composeFile logs web
            throw "El frontend no respondio correctamente en http://127.0.0.1:3000/login."
        }
    }

    Write-Host "Docker verificado correctamente para $ProjectName."
} finally {
    docker compose -p $ProjectName -f $composeFile down -v --remove-orphans
    Pop-Location
}
