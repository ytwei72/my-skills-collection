#Requires -Version 5.1
<#
.SYNOPSIS
  Link shared Cursor skills from my-skills-collection into a project's .cursor/skills/.

.DESCRIPTION
  Creates directory junctions (no admin required on Windows) from this repo's skill
  folders into <project>/.cursor/skills/<skill-name>. Re-running is idempotent.

.PARAMETER Project
  Manifest name under manifests/ (without .json), e.g. DocsRep or patent_management.

.PARAMETER LibRoot
  Override skills library root. Default: parent of the scripts/ folder.

.EXAMPLE
  .\install-project-skills.ps1 -Project DocsRep
#>
param(
    [Parameter(Mandatory)]
    [ValidateSet('DocsRep', 'patent_management', 'my-skills-collection')]
    [string]$Project,

    [string]$LibRoot = ''
)

$ErrorActionPreference = 'Stop'

if (-not $LibRoot) {
    $LibRoot = Split-Path $PSScriptRoot -Parent
}

$manifestPath = Join-Path $LibRoot "manifests\$Project.json"
if (-not (Test-Path $manifestPath)) {
    throw "Manifest not found: $manifestPath"
}

$cfg = Get-Content $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
$projectRoot = $cfg.projectRoot
$skillsDir = Join-Path $projectRoot '.cursor\skills'

if (-not (Test-Path $projectRoot)) {
    throw "Project root not found: $projectRoot"
}

New-Item -ItemType Directory -Force -Path $skillsDir | Out-Null

function Test-IsReparsePoint([string]$Path) {
    if (-not (Test-Path $Path)) { return $false }
    $item = Get-Item -LiteralPath $Path -Force
    return [bool]($item.Attributes -band [IO.FileAttributes]::ReparsePoint)
}

foreach ($name in $cfg.linkedSkills) {
    $link = Join-Path $skillsDir $name
    $target = Join-Path $LibRoot $name

    if (-not (Test-Path $target)) {
        Write-Warning "Skip '$name': target missing at $target"
        continue
    }

    if (Test-Path $link) {
        if (Test-IsReparsePoint $link) {
            $current = (Get-Item -LiteralPath $link -Force).Target
            if ($current -eq $target) {
                Write-Host "OK (already linked): $name"
                continue
            }
            Remove-Item -LiteralPath $link -Force
        }
        else {
            Write-Warning "Skip '$name': real directory exists at $link (project-specific? remove manually first)"
            continue
        }
    }

    New-Item -ItemType Junction -Path $link -Target $target | Out-Null
    Write-Host "Linked: $name -> $target"
}

Write-Host ""
Write-Host "Done. Skills dir: $skillsDir"
Write-Host "Library: $LibRoot"
