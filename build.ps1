<#
.SYNOPSIS
    Packs the plugin.video.ted.talks Kodi addon into an installable zip.

.DESCRIPTION
    Reads the addon id and version from addon.xml, copies the addon source
    into a staging folder (excluding dev/test/CI files), and zips it up as
    <addon-id>-<version>.zip, ready to install via Kodi's "Install from zip file".

.PARAMETER OutputDir
    Directory to write the resulting zip file to. Defaults to the script's directory.

.EXAMPLE
    .\build.ps1
    .\build.ps1 -OutputDir C:\Temp\builds
#>

[CmdletBinding()]
param(
    [string]$OutputDir
)

$ErrorActionPreference = 'Stop'

$repoRoot = $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($OutputDir)) {
    $OutputDir = $repoRoot
}
$addonXmlPath = Join-Path $repoRoot 'addon.xml'

if (-not (Test-Path $addonXmlPath)) {
    throw "addon.xml not found at $addonXmlPath"
}

[xml]$addonXml = Get-Content $addonXmlPath -Raw
$addonId = $addonXml.addon.id
$addonVersion = $addonXml.addon.version

if ([string]::IsNullOrWhiteSpace($addonId) -or [string]::IsNullOrWhiteSpace($addonVersion)) {
    throw "Could not read addon id/version from addon.xml"
}

Write-Host "Packing $addonId version $addonVersion..."

# Files/folders to exclude from the packaged addon (dev, CI and test artifacts).
$excludeNames = @(
    '.git', '.gitignore', '.idea', '.pylintrc', '.pytest_cache', '.travis.yml',
    'build.ps1', 'build.sh', 'run_tests.sh',
    'requirements.txt', 'README', 'README.md', 'README-developers.md', 'CHANGELOG.md',
    'LICENSE.txt'
)
$excludeExtensions = @('.pyc', '.iml', '.zip')
$excludeNamePatterns = @('*_test.py', 'test_util.py')

$stagingRoot = Join-Path $repoRoot ('.build_' + $addonId)
$stagingDir = Join-Path $stagingRoot $addonId

if (Test-Path $stagingRoot) {
    Remove-Item $stagingRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $stagingDir | Out-Null

function Test-ShouldExclude {
    param([System.IO.FileSystemInfo]$Item, [string]$RelativePath)

    $topLevel = ($RelativePath -split '[\\/]')[0]
    if ($excludeNames -contains $topLevel) { return $true }
    if ($excludeNames -contains $Item.Name) { return $true }
    if ($excludeExtensions -contains $Item.Extension) { return $true }
    foreach ($pattern in $excludeNamePatterns) {
        if ($Item.Name -like $pattern) { return $true }
    }
    return $false
}

Get-ChildItem -Path $repoRoot -Recurse -File | ForEach-Object {
    $relativePath = $_.FullName.Substring($repoRoot.Length + 1)

    # Skip anything under the staging folder itself.
    if ($relativePath.StartsWith('.build_')) { return }

    if (Test-ShouldExclude -Item $_ -RelativePath $relativePath) { return }

    $destPath = Join-Path $stagingDir $relativePath
    $destDir = Split-Path $destPath -Parent
    if (-not (Test-Path $destDir)) {
        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
    }
    Copy-Item $_.FullName -Destination $destPath -Force
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$zipName = "$addonId-$addonVersion.zip"
$zipPath = Join-Path $OutputDir $zipName

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

# Both Compress-Archive and System.IO.Compression.ZipFile::CreateFromDirectory
# write entries with backslash path separators under .NET Framework on Windows,
# which many unzip tools (incl. Kodi's) reject as an invalid/broken archive.
# Build the archive entry-by-entry instead, forcing forward slashes.
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

$archiveStream = [System.IO.File]::Open($zipPath, [System.IO.FileMode]::Create)
try {
    $archive = New-Object System.IO.Compression.ZipArchive($archiveStream, [System.IO.Compression.ZipArchiveMode]::Create)
    try {
        Get-ChildItem -Path $stagingRoot -Recurse -File | ForEach-Object {
            $entryName = $_.FullName.Substring($stagingRoot.Length + 1) -replace '\\', '/'
            $entry = $archive.CreateEntry($entryName, [System.IO.Compression.CompressionLevel]::Optimal)
            $entryStream = $entry.Open()
            try {
                $fileStream = [System.IO.File]::OpenRead($_.FullName)
                try {
                    $fileStream.CopyTo($entryStream)
                } finally {
                    $fileStream.Dispose()
                }
            } finally {
                $entryStream.Dispose()
            }
        }
    } finally {
        $archive.Dispose()
    }
} finally {
    $archiveStream.Dispose()
}

Remove-Item $stagingRoot -Recurse -Force

Write-Host "Created $zipPath"
