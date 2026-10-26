param([ValidateSet('start','stop','status')][string]$Task='status')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$configPath=Join-Path $root '.local/postgres-toolchain.json'
if (!(Test-Path -LiteralPath $configPath)) { throw 'Missing project-local toolchain file; no server installation attempted.' }
$config=Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
$data=(Resolve-Path -LiteralPath (Join-Path $root '.local/postgres-data')).Path
if (!$data.StartsWith($root+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)) { throw 'Cluster data directory must be inside this project.' }
$pgctl=Join-Path $config.bin 'pg_ctl.exe'
switch($Task) {
  'status' { & $pgctl -D $data status; if($LASTEXITCODE -ne 0) { Write-Output 'Quickbuddy cluster is stopped.' } }
  'start' {
    & $pgctl -D $data status 2>$null
    if($LASTEXITCODE -eq 0) { Write-Output 'Quickbuddy cluster is already running.'; exit 0 }
    $listener=Get-NetTCPConnection -LocalPort 5433 -State Listen -ErrorAction SilentlyContinue
    if($listener) { throw 'Port 5433 is already in use; existing listener was not modified.' }
    $args='-D "'+$data+'" -p 5433 -h 127.0.0.1'
    Start-Process -FilePath (Join-Path $config.bin 'postgres.exe') -ArgumentList $args -WindowStyle Hidden -RedirectStandardOutput (Join-Path $root '.local/postgres-stdout.log') -RedirectStandardError (Join-Path $root '.local/postgres-stderr.log')
    Write-Output 'Project PostgreSQL started on loopback port 5433. Use status/database checks to verify.'
  }
  'stop' { & $pgctl -D $data stop -m fast; if($LASTEXITCODE -ne 0) { throw 'Project cluster stop failed.' } }
}
