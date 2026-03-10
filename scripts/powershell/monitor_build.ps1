# Monitor build progress
$exe_path = "c:\Users\antho\Windows-AI\dist\WindowsAI.exe"
$max_wait = 600  # 10 minutes
$check_interval = 10  # 10 seconds
$elapsed = 0

Write-Host "Starting build monitoring..."
Write-Host "Will check every $check_interval seconds for up to $max_wait seconds"
Write-Host ""

while ($elapsed -lt $max_wait) {
    if (Test-Path $exe_path) {
        $size_mb = (Get-Item $exe_path).Length / 1MB
        Write-Host "[SUCCESS] Build completed!"
        Write-Host "File: $exe_path"
        Write-Host "Size: $([math]::Round($size_mb, 2)) MB"
        Write-Host ""
        Write-Host "The executable is ready to use!"
        exit 0
    }
    
    # Check build artifacts
    if (Test-Path "c:\Users\antho\Windows-AI\build") {
        $build_files = @(Get-ChildItem "c:\Users\antho\Windows-AI\build" -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
        Write-Host "[$elapsed/$max_wait] Building... ($build_files artifacts)"
    } else {
        Write-Host "[$elapsed/$max_wait] Initializing build..."
    }
    
    Start-Sleep -Seconds $check_interval
    $elapsed += $check_interval
}

Write-Host "[TIMEOUT] Build did not complete within $max_wait seconds"
if (Test-Path "c:\Users\antho\Windows-AI\build.log") {
    Write-Host ""
    Write-Host "Last 20 lines of build log:"
    Get-Content "c:\Users\antho\Windows-AI\build.log" -Tail 20
}

exit 1
