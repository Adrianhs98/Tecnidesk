<#
.SYNOPSIS
    Automated PostgreSQL / Supabase snapshot backup script for TecniDesk.

.DESCRIPTION
    Reads DB_URL from backend/.env, invokes pg_dump, and stores timestamped SQL snapshots
    in backend/backups/.

.EXAMPLE
    .\backend\scripts\backup_supabase.ps1
#>

[CmdletBinding()]
param (
    [string]$CustomDbUrl = "",
    [string]$OutputDir = ""
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir

if (-not $OutputDir) {
    $OutputDir = Join-Path $BackendDir "backups"
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$Timestamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
$BackupFile = Join-Path $OutputDir "supabase_backup_$Timestamp.sql"

$TargetUrl = $CustomDbUrl

# Attempt loading from .env if CustomDbUrl not provided
if (-not $TargetUrl) {
    $EnvFile = Join-Path $BackendDir ".env"
    if (Test-Path $EnvFile) {
        Write-Host "[INFO] Reading configuration from $EnvFile..." -ForegroundColor Cyan
        Get-Content $EnvFile | ForEach-Object {
            $line = $_.Trim()
            if ($line -and -not $line.StartsWith("#")) {
                if ($line -match "^DB_URL=(.+)$" -or $line -match "^DATABASE_URL=(.+)$") {
                    $TargetUrl = $matches[1].Trim('"', "'")
                }
            }
        }
    }
}

if (-not $TargetUrl -and $env:DB_URL) {
    $TargetUrl = $env:DB_URL
}
if (-not $TargetUrl -and $env:DATABASE_URL) {
    $TargetUrl = $env:DATABASE_URL
}

if (-not $TargetUrl) {
    Write-Error "Neither DB_URL nor DATABASE_URL found in environment or backend/.env."
    exit 1
}

# Normalize connection string for pg_dump (strip asyncpg driver prefix)
$CleanUrl = $TargetUrl -replace "postgresql\+asyncpg://", "postgresql://"

Write-Host "[INFO] Starting database backup at $((Get-Date).ToString())..." -ForegroundColor Cyan
Write-Host "[INFO] Destination: $BackupFile" -ForegroundColor Cyan

# Check if pg_dump is accessible
$pgDumpCmd = Get-Command pg_dump -ErrorAction SilentlyContinue

if (-not $pgDumpCmd) {
    # Check default Postgres installation paths on Windows
    $CommonPaths = @(
        "C:\Program Files\PostgreSQL\*\bin\pg_dump.exe",
        "C:\Program Files (x86)\PostgreSQL\*\bin\pg_dump.exe",
        "$env:LOCALAPPDATA\Programs\PostgreSQL\*\bin\pg_dump.exe"
    )
    $FoundPaths = Resolve-Path $CommonPaths -ErrorAction SilentlyContinue
    if ($FoundPaths) {
        $pgDumpPath = $FoundPaths[-1].Path
    } else {
        Write-Error "pg_dump utility not found in PATH or standard installation directories. Please install PostgreSQL client tools."
        exit 1
    }
} else {
    $pgDumpPath = "pg_dump"
}

try {
    & $pgDumpPath "$CleanUrl" `
        --no-owner `
        --no-acl `
        --clean `
        --if-exists `
        --file="$BackupFile"

    if ($LASTEXITCODE -eq 0 -or (Test-Path $BackupFile)) {
        $FileSize = (Get-Item $BackupFile).Length / 1MB
        Write-Host "[SUCCESS] Backup completed successfully!" -ForegroundColor Green
        Write-Host ("[INFO] File size: {0:N2} MB" -f $FileSize) -ForegroundColor Green
        Write-Host "[INFO] Location: $BackupFile" -ForegroundColor Green
    } else {
        Write-Error "pg_dump exited with error code $LASTEXITCODE"
    }
} catch {
    Write-Error "Failed to execute backup: $_"
    exit 1
}
