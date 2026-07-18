!macro PREINSTALL
  DetailPrint "Stopping learnbot-mcp-backend..."
  nsExec::Exec '"powershell.exe" -NoProfile -Command "Stop-Process -Name learnbot-mcp-backend -Force -ErrorAction SilentlyContinue; Stop-Process -Name learnbot-mcp-native -Force -ErrorAction SilentlyContinue; taskkill /F /IM learnbot-mcp-backend.exe /T 2>$null"'
  Sleep 1000
!macroend

!macro PREUNINSTALL
  DetailPrint "Stopping learnbot-mcp-backend..."
  nsExec::Exec '"powershell.exe" -NoProfile -Command "Stop-Process -Name learnbot-mcp-backend -Force -ErrorAction SilentlyContinue; Stop-Process -Name learnbot-mcp-native -Force -ErrorAction SilentlyContinue; taskkill /F /IM learnbot-mcp-backend.exe /T 2>$null"'
  Sleep 1000
!macroend
