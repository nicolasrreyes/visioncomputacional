# Levanta la demo completa en localhost: API (uvicorn :8000) + Dashboard (streamlit :8501)
# y abre el navegador. Detener despues Ctrl+C o cerrando las ventanas del proceso.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot)

$apiPort = 8000
$stPort = 8501

Write-Host "== Auditoria Visual de Inventario: demo ==" -ForegroundColor Cyan

# 1. Dependencias (idempotente)
python -m pip install -r requirements.txt --quiet
if (-not $?) { throw "Fallo la instalacion de dependencias (pip)." }

# 2. Backend API
Write-Host "[1/3] Levantando API en http://127.0.0.1:$apiPort ..." -ForegroundColor Yellow
# --host 0.0.0.0 expone la API a la red local (necesaria para el telefono por adb/tunel).
$api = Start-Process python -ArgumentList "-m", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "$apiPort" -WorkingDirectory (Split-Path $PSScriptRoot) -PassThru -WindowStyle Hidden
$ok = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Seconds 1
    try {
        if ((Invoke-RestMethod "http://127.0.0.1:$apiPort/health" -TimeoutSec 2).status -eq "ok") { $ok = $true; break }
    } catch { }
}
if (-not $ok) {
    Stop-Process -Id $api.Id -Force -ErrorAction SilentlyContinue
    throw "La API no respondio en 40s. Revisa los logs."
}
$lanIp = $null
try {
    $lanIp = (Get-NetIPAddress -AddressFamily IPv4 -ErrorAction Stop |
        Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" -and -not $_.PrefixOrigin -in @("WellKnown") } |
        Sort-Object { $_.InterfaceMetric } | Select-Object -First 1 -ExpandProperty IPAddress)
} catch { }
Write-Host "    API lista (PID $($api.Id))." -ForegroundColor Green
if ($lanIp) {
    Write-Host "    Expuesta en la red: http://$lanIp`:$apiPort  (si Windows te pregunta, acepta el Firewall)." -ForegroundColor DarkGray
}

# 3. Dashboard
Write-Host "[2/3] Levantando Dashboard en http://127.0.0.1:$stPort ..." -ForegroundColor Yellow
$st = Start-Process python -ArgumentList "-m", "streamlit", "run", "dashboard/streamlit_app.py", "--server.headless", "true", "--server.port", "$stPort" -WorkingDirectory (Split-Path $PSScriptRoot) -PassThru -WindowStyle Hidden
Start-Sleep -Seconds 4

Write-Host "[3/3] Abriendo navegador..." -ForegroundColor Yellow
Start-Process "http://127.0.0.1:$stPort"

Write-Host ""
Write-Host "Demo lista!" -ForegroundColor Green
Write-Host "  Dashboard : http://127.0.0.1:$stPort (PID $($st.Id))"
Write-Host "  Camara    : http://127.0.0.1:$apiPort/rtc?zona_id=estanteria_b  (PID $($api.Id))"
Write-Host ""
Write-Host "Telefono como camara (Android + USB, adb):" -ForegroundColor Cyan
Write-Host "    1. activa 'Depuracion USB' en el celular y conectalo por USB."
Write-Host "    2. en otra consola:  adb reverse tcp:$apiPort tcp:$apiPort"
Write-Host "    3. en el celular abre:  http://localhost:$apiPort/rtc?zona_id=estanteria_b"
Write-Host "       (localhost en el celular = contexto seguro => la camara SI se enciende)."
Write-Host "  Sin adb, usa un tunel HTTPS (ngrok http $apiPort) y abre su URL https en el celular."
Write-Host "  Guion completo: docs/DEMO.md"
Write-Host ""
Write-Host "Sugerencia: antes de la presentacion corre una carga manual de imagen" -ForegroundColor Cyan
Write-Host "para que el modelo (340 MB) quede cargado en memoria."
Write-Host ""
Write-Host "Para detener: Stop-Process -Id $($api.Id),$($st.Id) -Force"