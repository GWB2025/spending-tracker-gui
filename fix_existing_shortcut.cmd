@echo off
echo Fixing existing Spending Tracker desktop shortcut...
echo.

REM Get the current directory
set "PROJECT_DIR=%~dp0"
set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo Project directory: %PROJECT_DIR%
echo.

REM Create a VBScript to fix the shortcut
echo Creating temporary fix script...

echo Set WshShell = CreateObject("WScript.Shell") > temp_fix_shortcut.vbs
echo DesktopPath = WshShell.SpecialFolders("Desktop") >> temp_fix_shortcut.vbs
echo ShortcutPath = DesktopPath ^& "\Spending Tracker.lnk" >> temp_fix_shortcut.vbs
echo. >> temp_fix_shortcut.vbs
echo If CreateObject("Scripting.FileSystemObject").FileExists(ShortcutPath) Then >> temp_fix_shortcut.vbs
echo     Set Shortcut = WshShell.CreateShortcut(ShortcutPath) >> temp_fix_shortcut.vbs
echo     Shortcut.TargetPath = "%PROJECT_DIR%\SpendingTracker.cmd" >> temp_fix_shortcut.vbs
echo     Shortcut.WorkingDirectory = "%PROJECT_DIR%" >> temp_fix_shortcut.vbs
echo     Shortcut.IconLocation = "%PROJECT_DIR%\assets\windows_desktop_icon.ico,0" >> temp_fix_shortcut.vbs
echo     Shortcut.Description = "Launch Spending Tracker GUI - Personal Finance Manager" >> temp_fix_shortcut.vbs
echo     Shortcut.Save >> temp_fix_shortcut.vbs
echo     WScript.Echo "✅ Successfully updated existing shortcut!" >> temp_fix_shortcut.vbs
echo Else >> temp_fix_shortcut.vbs
echo     WScript.Echo "❌ No existing shortcut found. Please create one first." >> temp_fix_shortcut.vbs
echo End If >> temp_fix_shortcut.vbs

echo Running fix script...
cscript //NoLogo temp_fix_shortcut.vbs

echo Cleaning up...
del temp_fix_shortcut.vbs

echo.
echo The shortcut should now be fixed to:
echo   Target: %PROJECT_DIR%\SpendingTracker.cmd
echo   Icon:   %PROJECT_DIR%\assets\windows_desktop_icon.ico
echo.
echo You can now try using your desktop shortcut!
pause