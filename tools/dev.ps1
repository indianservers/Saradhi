param(
  [Parameter(Position=0)][ValidateSet('verify','install','api','web','mobile','flutter-init','worker','worker-smoke','worker-health','test','integration','migrate','migrate-test','lint','format','infra','database','contracts')][string]$Task = 'verify',
  [string]$App = 'company_admin'
)
$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
$python = Join-Path (Get-Location) '.venv\Scripts\python.exe'
function CheckExit { if ($LASTEXITCODE -ne 0) { throw "Command failed with exit code $LASTEXITCODE" } }
$webApps = @('company_admin','city_operations','support_console')
$mobileApps = @('customer_app','pilot_app','merchant_app')
switch ($Task) {
  'verify' {
    foreach ($tool in @('python','node','npm.cmd','flutter','dart','docker','psql','redis-server','adb','java')) {
      $found = Get-Command $tool -ErrorAction SilentlyContinue
      if ($found) { Write-Output "$tool : $($found.Source)" } else { Write-Output "$tool : MISSING" }
    }
    Get-CimInstance Win32_Service | Where-Object Name -Match 'postgres' | Select-Object Name,State
    Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue | Where-Object LocalPort -In 5432,6379 | Select-Object LocalAddress,LocalPort
  }
  'install' {
    if (!(Test-Path $python)) { python -m venv .venv; CheckExit }
    & $python -m pip install -r requirements.lock; CheckExit
    & $python -m pip install --no-deps -e .; CheckExit
    npm.cmd ci; CheckExit
    if (Get-Command flutter -ErrorAction SilentlyContinue) {
      foreach ($mobile in $mobileApps) { Push-Location "apps/$mobile"; try { flutter pub get; CheckExit } finally { Pop-Location } }
    } else { Write-Warning 'Flutter missing: mobile dependency installation skipped.' }
  }
  'api' { & $python -m uvicorn backend.api.app.main:app --reload --host 127.0.0.1 --port 8000 --no-access-log; CheckExit }
  'web' {
    if ($App -notin $webApps) { throw 'Select company_admin, city_operations or support_console' }
    npm.cmd run dev -w "@quickbuddy/$App"; CheckExit
  }
  'mobile' {
    if ($App -notin $mobileApps) { throw 'Select customer_app, pilot_app or merchant_app' }
    $port = 8080 + [array]::IndexOf($mobileApps, $App)
    Push-Location "apps/$App"
    try { flutter run -d chrome --web-port $port --dart-define=API_BASE_URL=http://localhost:8000; CheckExit } finally { Pop-Location }
  }
  'flutter-init' {
    if ($App -notin $mobileApps) { throw 'Select customer_app, pilot_app or merchant_app' }
    if (!(Get-Command flutter -ErrorAction SilentlyContinue)) { throw 'Flutter SDK required; no global installation attempted.' }
    $target = (Resolve-Path "apps/$App").Path
    $staging = Join-Path (Get-Location) "tools/generators/.flutter-$App-$([guid]::NewGuid().ToString('N'))"
    flutter create --platforms=android,ios,web --org com.quickbuddy --project-name $App $staging; CheckExit
    # Copy only SDK-generated runners. Never replace user sources or platform projects.
    foreach ($entry in @('android','ios','web','.metadata')) {
      if (!(Test-Path (Join-Path $target $entry))) { Copy-Item -LiteralPath (Join-Path $staging $entry) -Destination $target -Recurse }
    }
    Push-Location $target
    try { flutter pub get; CheckExit; flutter analyze; CheckExit; flutter test; CheckExit } finally { Pop-Location }
    Write-Output "SDK staging retained for inspection: $staging"
  }
  'worker' { & '.venv/Scripts/arq.exe' backend.workers.main.WorkerSettings; CheckExit }
  'worker-smoke' { & $python -m backend.scripts.worker_smoke; CheckExit }
  'worker-health' { & '.venv/Scripts/arq.exe' --check backend.workers.main.WorkerSettings; CheckExit }
  'test' { & $python -m pytest; CheckExit; npm.cmd run typecheck; CheckExit }
  'lint' { & $python -m ruff check backend tools tests; CheckExit; & $python -m ruff format --check backend tools tests; CheckExit; npm.cmd run typecheck; CheckExit; npm.cmd run format:check; CheckExit }
  'format' { & $python -m ruff check --fix backend tools tests; CheckExit; & $python -m ruff format backend tools tests; CheckExit; npm.cmd run format; CheckExit }
  'infra' { docker compose up -d redis; CheckExit }
  'database' { & $python -m backend.scripts.check_database; CheckExit }
  'migrate' { & $python -m backend.scripts.migrate; CheckExit }
  'migrate-test' { & $python -m backend.scripts.migrate --test; CheckExit }
  'integration' { & $python -m pytest tests/integration -v; CheckExit }
  'contracts' { & $python -m backend.scripts.export_openapi; CheckExit; npm.cmd run contracts; CheckExit }
}
