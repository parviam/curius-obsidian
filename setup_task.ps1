# Curius-Obsidian Sync - Task Scheduler Setup
#
# Creates a Windows Task Scheduler task to run the sync daily at 6 AM.
#
# USAGE:
#   1. Open PowerShell as Administrator
#   2. Navigate to this directory: cd "path\to\curius-obsidian"
#   3. Run: .\setup_task.ps1
#
# TO REMOVE THE TASK:
#   Unregister-ScheduledTask -TaskName "CuriusObsidianSync" -Confirm:$false

# Get the directory where this script is located
$ScriptDir = $PSScriptRoot
$BatchFile = Join-Path $ScriptDir "run_sync.bat"

# Verify the batch file exists
if (-not (Test-Path $BatchFile)) {
    Write-Error "run_sync.bat not found at: $BatchFile"
    Write-Error "Please ensure this script is in the same directory as run_sync.bat"
    exit 1
}

Write-Host "Setting up scheduled task..." -ForegroundColor Cyan
Write-Host "  Script directory: $ScriptDir"
Write-Host "  Batch file: $BatchFile"

# Define the scheduled task
$action = New-ScheduledTaskAction -Execute $BatchFile -WorkingDirectory $ScriptDir
$trigger = New-ScheduledTaskTrigger -Daily -At 6:00AM
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries

# Register the task
try {
    Register-ScheduledTask `
        -TaskName "CuriusObsidianSync" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Description "Sync Curius bookmarks to Obsidian daily" `
        -ErrorAction Stop

    Write-Host ""
    Write-Host "Task created successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "The task will run:"
    Write-Host "  - Daily at 6:00 AM"
    Write-Host "  - On wake/startup if the computer was off at 6 AM"
    Write-Host ""
    Write-Host "To verify: Open Task Scheduler and look for 'CuriusObsidianSync'"
    Write-Host "To remove: Unregister-ScheduledTask -TaskName 'CuriusObsidianSync' -Confirm:`$false"
}
catch {
    Write-Error "Failed to create scheduled task: $_"
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "  - Not running as Administrator (right-click PowerShell > Run as Administrator)"
    Write-Host "  - Task already exists (delete it first in Task Scheduler)"
    exit 1
}
