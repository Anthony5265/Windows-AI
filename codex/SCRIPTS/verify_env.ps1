# Verifies Node.js and Python environments
$node = node -v
$npm = npm -v
$py = python --version
Write-Host "Node:" $node
Write-Host "npm:" $npm
Write-Host "Python:" $py
