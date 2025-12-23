param(
    [string]$TargetPath = '',
    [string]$ShortcutName = 'VALKYRIE BALLISTICS.lnk',
    [string]$IconPath = ''
)

# Resolve repo root (set current location to repository root)
Set-Location (Join-Path $PSScriptRoot '..')

# Prefer the distributed exe if present
if ([string]::IsNullOrWhiteSpace($TargetPath)) {
    $exePath = Join-Path (Get-Location) 'dist\VALKYRIE_BALLISTICS\VALKYRIE_BALLISTICS.exe'
    if (Test-Path $exePath) {
        $TargetPath = $exePath
        $Arguments = ''
        $WorkingDir = Split-Path $exePath
    } else {
        # Fall back to running the repo with Python
        $mainPy = Join-Path (Get-Location) 'main.py'
        if (Test-Path $mainPy) {
            $pythonCmd = (Get-Command python -ErrorAction SilentlyContinue)
            if ($null -eq $pythonCmd) {
                Write-Error "Python not found in PATH. Please provide a TargetPath to the built executable or ensure python is installed."
                exit 2
            }
            $TargetPath = $pythonCmd.Path
            $Arguments = "`"$mainPy`""
            $WorkingDir = Get-Location
        } else {
            Write-Error "Neither the built exe nor main.py were found. Build the project first or provide -TargetPath."
            exit 1
        }
    }
} else {
    $Arguments = ''
    $WorkingDir = Split-Path $TargetPath
}

# Prepare icon: prefer provided IconPath, otherwise try to create an .ico from Logo\logo.png
if ([string]::IsNullOrWhiteSpace($IconPath)) {
    $possiblePng = Join-Path (Get-Location) 'Logo\logo.png'
    $possibleIco = Join-Path (Get-Location) 'Logo\logo.ico'
    if (Test-Path $possibleIco) {
        $IconPath = $possibleIco
    } elseif (Test-Path $possiblePng) {
        # Try to convert PNG to ICO using System.Drawing
        try {
            Add-Type -AssemblyName System.Drawing
            $bmp = [System.Drawing.Bitmap]::FromFile($possiblePng)
            $icon = [System.Drawing.Icon]::FromHandle($bmp.GetHicon())
            $fs = New-Object System.IO.FileStream($possibleIco,[System.IO.FileMode]::Create)
            $icon.Save($fs)
            $fs.Close()
            $icon.Dispose()
            $bmp.Dispose()
            $IconPath = $possibleIco
        } catch {
            Write-Host "Warning: Could not convert $possiblePng to .ico: $_"
            $IconPath = ''
        }
    }
}

# Create the shortcut on the current user's Desktop
$wsh = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath('Desktop')

# Ensure we don't accidentally leave or create a folder on the Desktop with the
# same base name as the shortcut. If a folder exists named like the shortcut
# (without the .lnk), remove it so only the single shortcut remains.
$baseName = [IO.Path]::GetFileNameWithoutExtension($ShortcutName)
$conflictingFolder = Join-Path $desktop $baseName
if (Test-Path $conflictingFolder -PathType Container) {
    try {
        Remove-Item -LiteralPath $conflictingFolder -Recurse -Force -ErrorAction Stop
        Write-Host "Removed existing Desktop folder: $conflictingFolder"
    } catch {
        Write-Host ("Warning: could not remove Desktop folder {0}: {1}" -f $conflictingFolder, $_)
    }
}

$shortcutPath = Join-Path $desktop $ShortcutName
$lnk = $wsh.CreateShortcut($shortcutPath)
$lnk.TargetPath = $TargetPath
if (-not [string]::IsNullOrEmpty($Arguments)) { $lnk.Arguments = $Arguments }
$lnk.WorkingDirectory = $WorkingDir
# Prefer explicit icon; fall back to exe icon
if (-not [string]::IsNullOrWhiteSpace($IconPath) -and (Test-Path $IconPath)) {
    try {
        $lnk.IconLocation = $IconPath
    } catch {
        Write-Host ("Warning: failed to set IconLocation to {0}: {1}" -f $IconPath, $_)
    }
} else {
    try {
        $lnk.IconLocation = $TargetPath
    } catch {
        # ignore
    }
}
$lnk.Save()
Write-Host "Shortcut created: $shortcutPath"
