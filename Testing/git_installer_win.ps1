function Test-GitInstalled {
    $gitPath = Get-Command git -ErrorAction SilentlyContinue
    return $gitPath -ne $null
}

# Function to download and install Git
function Install-Git {
    $installerPath = "$env:TEMP\git-installer.exe"
    $installerUrl = "https://github.com/git-for-windows/git/releases/download/v2.31.1.windows.1/Git-2.31.1-64-bit.exe" # Update URL to the latest version

    Write-Host "Downloading Git installer..."
    Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath

    Write-Host "Installing Git..."
    Start-Process -FilePath $installerPath -Args "/VERYSILENT" -Wait

    Remove-Item -Path $installerPath
}

# Main script logic
if (Test-GitInstalled) {
    Write-Host "Git is already installed."
} else {
    Install-Git
    if (Test-GitInstalled) {
        Write-Host "Git successfully installed."
    } else {
        Write-Host "Failed to install Git."
    }
}
