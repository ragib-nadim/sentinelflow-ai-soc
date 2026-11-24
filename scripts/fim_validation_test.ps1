# SentinelFlow AI SOC: File Integrity Monitoring (FIM) Validation Script
# Simulates File Creation (Rule 554), Modification (Rule 550), and Deletion (Rule 553)

$testFile = 'E:\Personal Projects\sentinelflow-ai-soc\monitored_directory\test.txt'

Write-Host "[+] Creating monitored file: $testFile" -ForegroundColor Green
"created $(Get-Date -Format o)" | Set-Content $testFile
Start-Sleep -Seconds 7

Write-Host "[*] Modifying monitored file checksum..." -ForegroundColor Yellow
"modified $(Get-Date -Format o)" | Add-Content $testFile
Start-Sleep -Seconds 7

Write-Host "[-] Deleting monitored file..." -ForegroundColor Red
Remove-Item $testFile
Start-Sleep -Seconds 7

Write-Host "[✓] FIM lifecycle test complete. Verify events in Wazuh & Grafana." -ForegroundColor Cyan
