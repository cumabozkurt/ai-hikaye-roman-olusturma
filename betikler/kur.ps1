# AI Hikaye & Roman Oluşturma: becerileri kullanıcı düzeyinde kurar (Windows PowerShell).
# Kullanım: powershell -ExecutionPolicy Bypass -File betikler\kur.ps1 [-Hedef claude|codex|opencode|hepsi]
param([ValidateSet("claude", "codex", "opencode", "hepsi")][string]$Hedef = "hepsi")
$ErrorActionPreference = "Stop"
$Kok = Split-Path -Parent $PSScriptRoot

function Kur([string]$Ad, [string]$Klasor) {
    New-Item -ItemType Directory -Force -Path $Klasor | Out-Null
    $beceriler = Get-ChildItem -Directory (Join-Path $Kok "skills")
    foreach ($b in $beceriler) {
        $hedef = Join-Path $Klasor $b.Name
        if ((Test-Path $hedef) -and ((Get-Item $hedef).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            Write-Host "Atlandı (bağlantı): $hedef"; continue
        }
        if (Test-Path $hedef) { Remove-Item -Recurse -Force $hedef }
        Copy-Item -Recurse $b.FullName $hedef
        Get-ChildItem -Recurse -Directory -Filter "__pycache__" $hedef | Remove-Item -Recurse -Force
    }
    Write-Host "✓ ${Ad}: $($beceriler.Count) beceri → $Klasor"
}

$ev = $env:USERPROFILE
$opencode = if ($env:XDG_CONFIG_HOME) { Join-Path $env:XDG_CONFIG_HOME "opencode\skills" } else { Join-Path $ev ".config\opencode\skills" }
switch ($Hedef) {
    "claude"   { Kur "Claude Code" (Join-Path $ev ".claude\skills") }
    "codex"    { Kur "OpenAI Codex" (Join-Path $ev ".agents\skills") }
    "opencode" { Kur "OpenCode" $opencode }
    "hepsi"    {
        Kur "Claude Code" (Join-Path $ev ".claude\skills")
        Kur "OpenAI Codex" (Join-Path $ev ".agents\skills")
        Kur "OpenCode" $opencode
    }
}
Write-Host "Yazım projenizde ajanları ve kancaları kurmak için ajanınızda /hikaye-kurulum çalıştırın."
