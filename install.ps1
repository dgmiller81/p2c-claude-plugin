<#
.SYNOPSIS
  p2c installer — installs the p2c skill, agents, and commands into a Claude Code
  configuration directory.

.DESCRIPTION
  Interactive:
    irm https://raw.githubusercontent.com/dgmiller81/p2c-claude-plugin/main/install.ps1 | iex

  Non-interactive (download first, then pass arguments):
    irm https://raw.githubusercontent.com/dgmiller81/p2c-claude-plugin/main/install.ps1 -OutFile install.ps1
    ./install.ps1 -Scope User
    ./install.ps1 -Scope Project -ProjectDir C:\src\myrepo
    ./install.ps1 -Scope User -Uninstall

.NOTES
  Prompts read from the host, so `irm | iex` still works interactively.
#>

[CmdletBinding()]
param(
  [ValidateSet('User', 'Project')]
  [string]$Scope,

  [string]$ProjectDir,

  [switch]$Uninstall,

  [switch]$Yes,

  [string]$Ref = 'main'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$Repo    = 'dgmiller81/p2c-claude-plugin'
$Tarball = "https://codeload.github.com/$Repo/zip/refs/heads/$Ref"

function Write-Info { param([string]$Message) Write-Host "  $Message" }
function Write-Ok   { param([string]$Message) Write-Host "  $Message" -ForegroundColor Green }
function Write-Warn { param([string]$Message) Write-Host "  $Message" -ForegroundColor Yellow }
function Stop-WithError {
  param([string]$Message)
  Write-Host "error: $Message" -ForegroundColor Red
  exit 1
}

$AgentNames = @(
  'business-analyst', 'lead-architect', 'lead-developer', 'lead-qa-coordinator',
  'lead-ux-designer', 'product-owner', 'research-marketing', 'scrum-master'
)

# ---------------------------------------------------------------- prompting

function Select-Scope {
  Write-Host ''
  Write-Host 'Where should p2c be installed?' -ForegroundColor White
  Write-Host ''
  Write-Host '  1) This user      ' -NoNewline; Write-Host "$HOME\.claude" -ForegroundColor DarkGray
  Write-Host '     Available in every project you open.'
  Write-Host ''
  Write-Host '  2) One project    ' -NoNewline; Write-Host '<project>\.claude' -ForegroundColor DarkGray
  Write-Host '     Scoped to a single repo. Commit it and your whole team gets p2c.'
  Write-Host ''

  while ($true) {
    $reply = Read-Host 'Choose 1 or 2 [1]'
    if ([string]::IsNullOrWhiteSpace($reply)) { $reply = '1' }
    switch ($reply.Trim()) {
      '1' { return 'User' }
      '2' { return 'Project' }
      default { Write-Warn 'Enter 1 or 2.' }
    }
  }
}

# ---------------------------------------------------------------- resolve target

if (-not $Scope) {
  if ($Yes) { Stop-WithError 'the -Yes switch requires -Scope User or -Scope Project' }
  $Scope = Select-Scope
}

switch ($Scope) {
  'User' {
    $Dest  = Join-Path $HOME '.claude'
    $Label = 'this user'
  }
  'Project' {
    if (-not $ProjectDir) {
      if ($Yes) {
        $ProjectDir = (Get-Location).Path
      } else {
        $reply = Read-Host "Project directory [$((Get-Location).Path)]"
        $ProjectDir = if ([string]::IsNullOrWhiteSpace($reply)) { (Get-Location).Path } else { $reply.Trim() }
      }
    }
    if (-not (Test-Path -LiteralPath $ProjectDir -PathType Container)) {
      Stop-WithError "not a directory: $ProjectDir"
    }
    $ProjectDir = (Resolve-Path -LiteralPath $ProjectDir).Path
    $Dest  = Join-Path $ProjectDir '.claude'
    $Label = "project $ProjectDir"
  }
}

# ---------------------------------------------------------------- uninstall

function Remove-P2c {
  $removed = $false

  $skillDir = Join-Path $Dest 'skills\p2c'
  if (Test-Path -LiteralPath $skillDir) {
    Remove-Item -LiteralPath $skillDir -Recurse -Force
    Write-Ok 'removed skills\p2c'
    $removed = $true
  }

  $agentDir = Join-Path $Dest 'agents'
  $agentHit = $false
  foreach ($name in $AgentNames) {
    $p = Join-Path $agentDir "$name.md"
    if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force; $agentHit = $true }
  }
  if ($agentHit) { Write-Ok 'removed p2c agents'; $removed = $true }

  $cmdDir = Join-Path $Dest 'commands'
  if (Test-Path -LiteralPath $cmdDir) {
    $cmds = Get-ChildItem -LiteralPath $cmdDir -Filter 'p2c-*.md' -File -ErrorAction SilentlyContinue
    if ($cmds) {
      $cmds | Remove-Item -Force
      Write-Ok 'removed p2c- commands'
      $removed = $true
    }
  }

  if (-not $removed) { Write-Warn "nothing to remove in $Dest" }
}

if ($Uninstall) {
  Write-Host ''
  Write-Host "Uninstalling p2c from $Label" -ForegroundColor White
  Write-Host "  $Dest" -ForegroundColor DarkGray
  Write-Host ''
  if (-not $Yes) {
    $reply = Read-Host 'Proceed? [y/N]'
    if ($reply -notmatch '^[yY]') { Write-Host 'Aborted.'; exit 0 }
  }
  Remove-P2c
  Write-Host ''
  Write-Ok 'Done. Restart Claude Code.'
  exit 0
}

# ---------------------------------------------------------------- fetch

Write-Host ''
Write-Host "Installing p2c for $Label" -ForegroundColor White
Write-Host "  source: $Repo@$Ref" -ForegroundColor DarkGray
Write-Host "  target: $Dest" -ForegroundColor DarkGray
Write-Host ''

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("p2c-" + [System.Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $tmp -Force | Out-Null

try {
  Write-Info 'Downloading...'
  $zip = Join-Path $tmp 'p2c.zip'
  try {
    Invoke-WebRequest -Uri $Tarball -OutFile $zip -UseBasicParsing
  } catch {
    Stop-WithError "download failed - check the ref '$Ref' exists and you have network access"
  }

  Expand-Archive -LiteralPath $zip -DestinationPath $tmp -Force

  $src = Get-ChildItem -LiteralPath $tmp -Recurse -Directory |
         Where-Object { $_.FullName -like '*\plugins\p2c' } |
         Select-Object -First 1
  if (-not $src -or -not (Test-Path -LiteralPath (Join-Path $src.FullName 'skills\p2c'))) {
    Stop-WithError 'archive layout unexpected - plugins\p2c not found'
  }

  # ------------------------------------------------------------ confirm overwrite

  $skillDir = Join-Path $Dest 'skills\p2c'
  if ((Test-Path -LiteralPath $skillDir) -and -not $Yes) {
    Write-Warn "An existing p2c install is present at $skillDir"
    $reply = Read-Host 'Overwrite it? [y/N]'
    if ($reply -notmatch '^[yY]') { Write-Host 'Aborted. Nothing changed.'; exit 0 }
  }

  # ------------------------------------------------------------ install

  foreach ($sub in @('skills', 'agents', 'commands')) {
    New-Item -ItemType Directory -Path (Join-Path $Dest $sub) -Force | Out-Null
  }

  if (Test-Path -LiteralPath $skillDir) { Remove-Item -LiteralPath $skillDir -Recurse -Force }
  New-Item -ItemType Directory -Path $skillDir -Force | Out-Null
  Copy-Item -Path (Join-Path $src.FullName 'skills\p2c\*') -Destination $skillDir -Recurse -Force
  Write-Ok "skill        -> $skillDir"

  Copy-Item -Path (Join-Path $src.FullName 'agents\*.md') -Destination (Join-Path $Dest 'agents') -Force
  Write-Ok "agents (8)   -> $(Join-Path $Dest 'agents')"

  # Flat installs have no ':' namespacing, so prefix commands to avoid collisions.
  $count = 0
  Get-ChildItem -LiteralPath (Join-Path $src.FullName 'commands') -Filter '*.md' -File | ForEach-Object {
    Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $Dest "commands\p2c-$($_.Name)") -Force
    $count++
  }
  Write-Ok "commands ($count) -> $(Join-Path $Dest 'commands')  (as /p2c-*)"

  # ------------------------------------------------------------ deps

  Write-Host ''
  $py = Get-Command python -ErrorAction SilentlyContinue
  if (-not $py) { $py = Get-Command python3 -ErrorAction SilentlyContinue }

  $hasYaml = $false
  if ($py) {
    & $py.Source -c 'import yaml' 2>$null
    $hasYaml = ($LASTEXITCODE -eq 0)
  }

  if ($hasYaml) {
    Write-Ok "PyYAML present ($(& $py.Source --version 2>&1))"
  } else {
    Write-Warn 'PyYAML not found. trace.py and estimate_cost.py need it:'
    Write-Info '  pip install pyyaml'
  }

  # ------------------------------------------------------------ done

  Write-Host ''
  Write-Host 'Installed.' -NoNewline -ForegroundColor White
  Write-Host ' Restart Claude Code, then try /p2c-help.'
  Write-Host ''
  if ($Scope -eq 'Project') {
    Write-Info 'Commit .claude\ to share p2c with your team.'
    Write-Host ''
  }
  Write-Host "Prefer '/p2c:help' style namespacing? Install as a plugin instead -" -ForegroundColor DarkGray
  Write-Host 'run these inside Claude Code (they replace this flat install):' -ForegroundColor DarkGray
  Write-Host "  /plugin marketplace add $Repo"
  Write-Host '  /plugin install p2c@p2c-marketplace'
  Write-Host ''
  $uninstallHint = if ($Scope -eq 'Project') {
    "./install.ps1 -Scope Project -ProjectDir '$ProjectDir' -Uninstall"
  } else {
    './install.ps1 -Scope User -Uninstall'
  }
  Write-Host "Uninstall: $uninstallHint" -ForegroundColor DarkGray
  Write-Host ''
}
finally {
  if (Test-Path -LiteralPath $tmp) { Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue }
}
