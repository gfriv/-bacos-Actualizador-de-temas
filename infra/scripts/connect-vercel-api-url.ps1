param(
  [Parameter(Mandatory = $true)]
  [string]$ApiUrl,

  [string]$WebCwd = "apps/web",

  [string]$Scope = "guillermo-colegionazars-projects",

  [string[]]$Targets = @("production")
)

$ErrorActionPreference = "Stop"

if ($ApiUrl -notmatch "^https?://.+/api$") {
  throw "ApiUrl debe terminar en /api. Ejemplo: https://abacos-api.onrender.com/api"
}

Write-Host "Configurando NEXT_PUBLIC_API_URL=$ApiUrl en Vercel..."

$envValue = $ApiUrl
foreach ($target in $targets) {
  try {
    npx vercel env rm NEXT_PUBLIC_API_URL $target --yes --cwd $WebCwd --scope $Scope 2>$null
  } catch {
    # It is fine when the variable does not exist yet.
  }
  $envValue | npx vercel env add NEXT_PUBLIC_API_URL $target --yes --cwd $WebCwd --scope $Scope
}

Write-Host "Redespliega el frontend para aplicar la variable:"
Write-Host "npx vercel deploy apps/web --yes --project abacos-academic-update-system --prod --scope $Scope"
