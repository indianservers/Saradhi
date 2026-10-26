[CmdletBinding()]
param()
$ErrorActionPreference = 'Continue'
$checks = [ordered]@{
  'Python 3.12+' = { python --version }
  'Node 24+' = { node --version }
  'npm' = { npm --version }
  'PostgreSQL client' = { psql --version }
  'Redis CLI' = { redis-cli --version }
  'Docker' = { docker --version }
  'Terraform' = { terraform version }
  'Flutter' = { flutter --version }
  'Git' = { git --version }
}
foreach ($name in $checks.Keys) {
  $commandName = switch ($name) {
    'Python 3.12+' { 'python' }
    'Node 24+' { 'node' }
    'npm' { 'npm' }
    'PostgreSQL client' { 'psql' }
    'Redis CLI' { 'redis-cli' }
    'Docker' { 'docker' }
    'Terraform' { 'terraform' }
    'Flutter' { 'flutter' }
    'Git' { 'git' }
  }
  $found = Get-Command $commandName -ErrorAction SilentlyContinue
  if (-not $found) { Write-Output ("MISSING  {0}" -f $name); continue }
  try { $result = & $checks[$name] 2>&1 | Select-Object -First 1; Write-Output ("FOUND    {0}: {1}" -f $name, $result) }
  catch { Write-Output ("ERROR    {0}: {1}" -f $name, $_.Exception.Message) }
}
foreach ($path in @('.venv\Scripts\python.exe', 'node_modules', '.env')) {
  if (Test-Path $path) { Write-Output ("FOUND    {0}" -f $path) } else { Write-Output ("MISSING  {0}" -f $path) }
}
