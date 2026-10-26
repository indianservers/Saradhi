# Explicit developer examples. Nothing runs unless you invoke a named action.
# Run in the same PowerShell process to retain the access token in process memory.
param(
  [Parameter(Mandatory)][ValidateSet('Register','Login','Profile','CreateCart','AddItem','Quote','Confirm','AcceptMerchant','Prepare','Ready','Offer','AcceptOffer','Pickup','Complete','CreateTicket','Notifications')][string]$Action,
  [string]$BaseUrl='http://127.0.0.1:8000',
  [string]$Email,
  [string]$CartId,[string]$BranchId,[string]$VariantId,[string]$WindowId,
  [string]$QuoteId,[string]$OrderId,[string]$MerchantOrderId,[string]$TaskId,
  [string]$AssignmentId,[string]$IdempotencyKey,[int]$ExpectedVersion=1
)
$ErrorActionPreference='Stop'
$headers=@{}
if($env:QUICKBUDDY_ACCESS_TOKEN) { $headers.Authorization='Bearer '+$env:QUICKBUDDY_ACCESS_TOKEN }
function Send-Api([string]$Method,[string]$Path,$Body) {
  $arguments=@{Uri="$BaseUrl/api/v1$Path";Method=$Method;Headers=$headers;ContentType='application/json'}
  if($null -ne $Body) { $arguments.Body=$Body | ConvertTo-Json -Depth 12 }
  Invoke-RestMethod @arguments
}
switch($Action) {
  'Register' {
    if(!$Email) { throw 'Supply your own -Email; no default account is provided.' }
    $secure=Read-Host 'Choose a password of at least 12 characters' -AsSecureString
    $password=[System.Net.NetworkCredential]::new('', $secure).Password
    Send-Api POST '/auth/register' @{email=$Email;password=$password}
    $password=$null
  }
  'Login' {
    if(!$Email) { throw 'Supply -Email.' }
    $secure=Read-Host 'Password' -AsSecureString
    $password=[System.Net.NetworkCredential]::new('', $secure).Password
    $tokens=Send-Api POST '/auth/login' @{email=$Email;password=$password}
    $env:QUICKBUDDY_ACCESS_TOKEN=$tokens.access_token
    $env:QUICKBUDDY_REFRESH_TOKEN=$tokens.refresh_token
    $password=$null; $tokens=$null
    Write-Output 'Authenticated. Tokens are kept in this PowerShell process and are not printed.'
  }
  'Profile' { Send-Api GET '/me' $null }
  'CreateCart' { Send-Api POST '/carts' $null }
  'AddItem' { Send-Api POST "/carts/$CartId/items" @{branch_id=$BranchId;variant_id=$VariantId;window_id=$WindowId;quantity='1';delivery_method='pickup'} }
  'Quote' { Send-Api POST "/carts/$CartId/quote" $null }
  'Confirm' {
    if(!$IdempotencyKey) { throw 'Supply a stable -IdempotencyKey of at least 8 characters and reuse it for retries.' }
    $headers['Idempotency-Key']=$IdempotencyKey
    Send-Api POST '/orders/confirm' @{quote_id=$QuoteId}
  }
  'AcceptMerchant' { Send-Api POST "/merchant-orders/$MerchantOrderId/transition" @{target='accepted';expected_version=$ExpectedVersion} }
  'Prepare' { Send-Api POST "/merchant-orders/$MerchantOrderId/transition" @{target='preparing';expected_version=$ExpectedVersion} }
  'Ready' { Send-Api POST "/merchant-orders/$MerchantOrderId/transition" @{target='ready';expected_version=$ExpectedVersion} }
  'Offer' { Send-Api POST "/delivery-tasks/$TaskId/offer" @{} }
  'AcceptOffer' { Send-Api POST "/pilot-assignments/$AssignmentId/accept" $null }
  'Pickup' { Send-Api POST "/delivery-tasks/$TaskId/pickup" @{expected_version=$ExpectedVersion} }
  'Complete' { Send-Api POST "/delivery-tasks/$TaskId/acknowledge" @{expected_version=$ExpectedVersion} }
  'CreateTicket' { Send-Api POST '/support/tickets' @{subject='Order assistance requested';order_id=$OrderId} }
  'Notifications' { Send-Api GET '/notifications?limit=20' $null }
}
