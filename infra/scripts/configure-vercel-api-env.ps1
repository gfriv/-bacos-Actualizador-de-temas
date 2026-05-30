param(
  [string]$ApiCwd = "apps/api",

  [string]$Scope = "guillermo-colegionazars-projects",

  [string]$DatabaseUrl = "",

  [string[]]$Targets = @("production")
)

$ErrorActionPreference = "Stop"

function Set-VercelEnv {
  param(
    [string]$Key,
    [string]$Value,
    [string]$Target
  )

  try {
    npx vercel env rm $Key $Target --yes --cwd $ApiCwd --scope $Scope 2>$null
  } catch {
    # It is fine when the variable does not exist yet.
  }
  $Value | npx vercel env add $Key $Target --yes --cwd $ApiCwd --scope $Scope
}

$jwtSecret = [Convert]::ToBase64String([Guid]::NewGuid().ToByteArray()) + [Convert]::ToBase64String([Guid]::NewGuid().ToByteArray())

foreach ($target in $targets) {
  if (-not [string]::IsNullOrWhiteSpace($DatabaseUrl)) {
    Set-VercelEnv -Key "DATABASE_URL" -Value $DatabaseUrl -Target $target
  }
  Set-VercelEnv -Key "JWT_SECRET" -Value $jwtSecret -Target $target
  Set-VercelEnv -Key "CORS_ORIGINS" -Value '["https://abacos-academic-update-system.vercel.app","http://localhost:3000","http://127.0.0.1:3000"]' -Target $target
  Set-VercelEnv -Key "STORAGE_BACKEND" -Value "database" -Target $target
  Set-VercelEnv -Key "UPLOAD_DIR" -Value "/tmp/uploads" -Target $target
  Set-VercelEnv -Key "GENERATED_DIR" -Value "/tmp/generated" -Target $target
  Set-VercelEnv -Key "MAX_UPLOAD_MB" -Value "25" -Target $target
  Set-VercelEnv -Key "LLM_PROVIDER" -Value "mock" -Target $target
  Set-VercelEnv -Key "OLLAMA_PULL_ENABLED" -Value "false" -Target $target
  Set-VercelEnv -Key "ANALYSIS_LLM_ENABLED" -Value "false" -Target $target
  Set-VercelEnv -Key "EXTERNAL_AI_PROVIDERS_ENABLED" -Value "false" -Target $target
  Set-VercelEnv -Key "EXTERNAL_AI_DATA_PROCESSING_CONFIRMED" -Value "false" -Target $target
  Set-VercelEnv -Key "WEB_SEARCH_PROVIDER" -Value "disabled" -Target $target
  Set-VercelEnv -Key "EXTERNAL_WEB_SEARCH_ENABLED" -Value "false" -Target $target
  Set-VercelEnv -Key "RUN_MIGRATIONS_ON_STARTUP" -Value "true" -Target $target
  Set-VercelEnv -Key "DEMO_ACCESS_ENABLED" -Value "false" -Target $target
}

Write-Host "Variables de abacos-api configuradas. Despliega con:"
Write-Host "npx vercel deploy apps/api --yes --project abacos-api --prod --scope $Scope"
