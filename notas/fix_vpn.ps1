# 1. Definir los datos de la VM
$ip = "68.221.172.53"
$dns = "tools.ilvsilver.com"
$index = 21

# 2. Forzar la ruta por la VPN (índice 21)
Write-Host "Configurando ruta de red..." -ForegroundColor Cyan
Remove-NetRoute -DestinationPrefix "$ip/32" -Confirm:$false -ErrorAction SilentlyContinue
New-NetRoute -DestinationPrefix "$ip/32" -InterfaceIndex $index -RouteMetric 1

# 3. Añadir el host al archivo de Windows
Write-Host "Configurando nombre de host..." -ForegroundColor Cyan
$hostPath = "C:\Windows\System32\drivers\etc\hosts"
$entry = "$ip $dns"
if (!(Select-String -Path $hostPath -Pattern $dns)) {
    Add-Content -Path $hostPath -Value "`n$entry"
    Write-Host "Listo: Host añadido." -ForegroundColor Green
} else {
    Write-Host "El host ya estaba en el archivo." -ForegroundColor Yellow
}