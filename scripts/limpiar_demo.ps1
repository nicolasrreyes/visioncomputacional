# Limpia los artefactos generados por la demo para volver a empezar de cero:
# outputs/auditorias/*.json, outputs/evidencia/*.png, inputs/* (copias), outputs/tmp_upload/*.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot)

$targets = @(
    "outputs/auditorias",
    "outputs/evidencia",
    "inputs",
    "outputs/tmp_upload"
)

$archivos = foreach ($t in $targets) {
    if (Test-Path $t) { Get-ChildItem -Recurse -File $t }
}
if ($archivos.Count -eq 0) {
    Write-Host "No hay artefactos de demo que limpiar." -ForegroundColor Green
    exit 0
}

Write-Host "Se eliminaran $($archivos.Count) archivos:" -ForegroundColor Yellow
$archivos | Select-Object -First 10 | ForEach-Object { Write-Host "  - $($_.FullName)" }
if ($archivos.Count -gt 10) { Write-Host "  ... y otros $($archivos.Count - 10) mas" }

$confirma = Read-Host "Confirmar (s/N)"
if ($confirma -notmatch "^s") {
    Write-Host "Cancelado." -ForegroundColor Cyan
    exit 0
}

$archivos | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Force }
Write-Host "Listo. La demo vuelve a empezar sin auditorias previas." -ForegroundColor Green