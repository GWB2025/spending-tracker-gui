# Create Desktop Shortcut for Spending Tracker GUI
# This script creates a proper desktop shortcut with the custom icon

$ProjectPath = Get-Location
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Spending Tracker.lnk"

Write-Host "Creating desktop shortcut for Spending Tracker..."
Write-Host "Project path: $ProjectPath"
Write-Host "Desktop path: $DesktopPath"
Write-Host "Shortcut path: $ShortcutPath"

# Create WScript.Shell COM object
$WshShell = New-Object -comObject WScript.Shell

# Create the shortcut
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

# Set shortcut properties
$Shortcut.TargetPath = Join-Path $ProjectPath "SpendingTracker.cmd"
$Shortcut.WorkingDirectory = $ProjectPath.Path
$Shortcut.Description = "Launch Spending Tracker GUI - Personal Finance Manager"
$Shortcut.Arguments = ""

# Set the custom icon
$IconPath = Join-Path $ProjectPath "assets\windows_desktop_icon.ico"
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = "$IconPath,0"
    Write-Host "Setting custom icon: $IconPath"
} else {
    Write-Host "Warning: Custom icon not found at $IconPath"
    # Try alternative icons
    $AlternativeIcons = @(
        "assets\desktop_shortcut_icon.ico",
        "assets\simple_desktop_icon.ico",
        "assets\spending_tracker_icon.ico"
    )
    
    foreach ($AltIcon in $AlternativeIcons) {
        $AltIconPath = Join-Path $ProjectPath $AltIcon
        if (Test-Path $AltIconPath) {
            $Shortcut.IconLocation = "$AltIconPath,0"
            Write-Host "Using alternative icon: $AltIconPath"
            break
        }
    }
}

# Save the shortcut
$Shortcut.Save()

Write-Host ""
Write-Host "✅ Desktop shortcut created successfully!"
Write-Host "Shortcut location: $ShortcutPath"
Write-Host ""
Write-Host "The shortcut will:"
Write-Host "  - Run: SpendingTracker.cmd"
Write-Host "  - Start in: $ProjectPath"
Write-Host "  - Use custom icon from: assets\"
Write-Host ""
Write-Host "You can now double-click the shortcut to launch your Spending Tracker!"

# Cleanup
[System.Runtime.Interopservices.Marshal]::ReleaseComObject($WshShell) | Out-Null
[System.GC]::Collect()
[System.GC]::WaitForPendingFinalizers()