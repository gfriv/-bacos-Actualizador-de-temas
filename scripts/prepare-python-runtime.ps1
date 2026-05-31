param(
    [string]$PythonExe = "python",
    [string]$RuntimeDir = "",
    [switch]$SkipDependencyInstall
)

$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$apiDir = Join-Path $repoRoot "apps\api"
if (-not $RuntimeDir) {
    $RuntimeDir = Join-Path $repoRoot "desktop-runtime\python"
}

$runtimePath = [System.IO.Path]::GetFullPath($RuntimeDir)
$runtimeLib = Join-Path $runtimePath "Lib"
$sitePackages = Join-Path $runtimeLib "site-packages"

$pythonInfoJson = & $PythonExe -c "import json, sys, pathlib; print(json.dumps({'base_prefix': sys.base_prefix, 'version': list(sys.version_info[:3])}))"
if ($LASTEXITCODE -ne 0) {
    throw "No se pudo ejecutar Python desde '$PythonExe'."
}
$pythonInfo = $pythonInfoJson | ConvertFrom-Json
$version = $pythonInfo.version
if ($version[0] -ne 3 -or $version[1] -lt 12) {
    throw "Se requiere Python 3.12 o superior para preparar el runtime. Detectado: $($version -join '.')."
}

$basePrefix = [System.IO.Path]::GetFullPath([string]$pythonInfo.base_prefix)
if (-not (Test-Path $basePrefix)) {
    throw "No existe el directorio base de Python: $basePrefix"
}

Remove-Item -LiteralPath $runtimePath -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $runtimePath | Out-Null

$rootFiles = @(
    "python.exe",
    "pythonw.exe",
    "python3.dll",
    "python312.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll",
    "LICENSE.txt"
)

foreach ($file in $rootFiles) {
    $source = Join-Path $basePrefix $file
    if (Test-Path $source) {
        Copy-Item -LiteralPath $source -Destination (Join-Path $runtimePath $file) -Force
    }
}

foreach ($directory in @("DLLs", "Lib")) {
    $source = Join-Path $basePrefix $directory
    if (-not (Test-Path $source)) {
        throw "Falta el directorio requerido de Python: $source"
    }
    $target = Join-Path $runtimePath $directory
    New-Item -ItemType Directory -Path $target -Force | Out-Null
    Copy-Item -Path (Join-Path $source "*") -Destination $target -Recurse -Force
}

Remove-Item -LiteralPath (Join-Path $runtimeLib "site-packages") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $runtimeLib "test") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $runtimeLib "idlelib") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $runtimeLib "tkinter") -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $runtimeLib "turtledemo") -Recurse -Force -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Path $sitePackages -Force | Out-Null

if (-not $SkipDependencyInstall) {
    $lockedRequirements = Join-Path $env:TEMP "abacos-desktop-runtime-requirements.txt"
    Push-Location $apiDir
    try {
        & $PythonExe -m uv export --no-dev --format requirements.txt --frozen --no-emit-project --no-hashes --output-file $lockedRequirements | Out-Null
        if ($LASTEXITCODE -ne 0) {
            throw "No se pudo exportar uv.lock para el runtime embebido."
        }
    } finally {
        Pop-Location
    }
    & $PythonExe -m uv pip install --target $sitePackages -r $lockedRequirements
    if ($LASTEXITCODE -ne 0) {
        throw "No se pudieron instalar las dependencias Python en el runtime embebido."
    }
}

Get-ChildItem -LiteralPath $runtimePath -Recurse -Directory -Filter "__pycache__" |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
foreach ($pattern in @("*.pyc", "*.pyo")) {
    foreach ($compiledFile in Get-ChildItem -LiteralPath $runtimePath -Recurse -Filter $pattern -File) {
        Remove-Item -LiteralPath $compiledFile.FullName -Force -ErrorAction SilentlyContinue
    }
}

$sizeBytes = (Get-ChildItem -LiteralPath $runtimePath -Recurse -File | Measure-Object -Property Length -Sum).Sum
$sizeMb = [Math]::Round($sizeBytes / 1MB, 1)
Write-Host "Runtime Python preparado en $runtimePath ($sizeMb MB)."
