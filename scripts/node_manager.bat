<# :
@echo off
title BOINC RPC - Node Manager
color 0A
powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((Get-Content '%~f0') -join [Environment]::NewLine)"
exit /b
#>

$configFile = "$env:USERPROFILE\.config\boinc-rpc\config.json"

function Pause-Script {
    Write-Host "`nPress Enter to continue..." -ForegroundColor DarkGray
    Read-Host | Out-Null
}

if (!(Test-Path $configFile)) {
    Write-Host "[Error] config.json not found." -ForegroundColor Red
    Write-Host "Please run the main BOINC RPC program at least once to generate it." -ForegroundColor Yellow
    Pause-Script
    exit
}

while ($true) {
    Clear-Host
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "       BOINC RPC - Node Manager" -ForegroundColor Cyan
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host "1. Add a new node"
    Write-Host "2. Delete an existing node"
    Write-Host "3. Exit"
    Write-Host "------------------------------------------" -ForegroundColor Cyan

    $choice = Read-Host "What do you want to do? (1-3)"

    if ($choice -eq '1') {
        Write-Host "`n--- ADD A NODE ---" -ForegroundColor Yellow
        $ip = Read-Host "1. What is the IP address? (e.g. 192.168.1.50)"
        $pwd = Read-Host "2. What is the BOINC password?"
        $name = Read-Host "3. What name do you want to give it? (e.g. Laptop)"

        $json = Get-Content $configFile -Raw | ConvertFrom-Json
        $newNode = [PSCustomObject]@{ name = $name; host = $ip; port = 31416; password_path = ""; password = $pwd }

        # On force la conversion en tableau au cas où il n'y aurait qu'un seul noeud
        $nodes = @($json.nodes)
        $nodes += $newNode
        $json.nodes = $nodes

        $json | ConvertTo-Json -Depth 10 | Set-Content $configFile
        Write-Host "`n[Success] The node has been added successfully!" -ForegroundColor Green
        Write-Host "Restart the BOINC RPC app to apply changes." -ForegroundColor Yellow
        Pause-Script
    }
    elseif ($choice -eq '2') {
        Write-Host "`n--- DELETE A NODE ---" -ForegroundColor Yellow
        $json = Get-Content $configFile -Raw | ConvertFrom-Json
        $nodes = @($json.nodes)

        if ($nodes.Count -eq 0) {
            Write-Host "No nodes configured yet." -ForegroundColor Yellow
            Pause-Script
            continue
        }

        # Affiche la liste des PC existants avec un numéro
        for ($i = 0; $i -lt $nodes.Count; $i++) {
            Write-Host "[$i] $($nodes[$i].name) ($($nodes[$i].host))"
        }

        Write-Host "[q] Cancel"
        $index = Read-Host "`nWhich node do you want to delete? (Enter number)"

        if ($index -eq 'q') {
            continue
        }

        # Vérifie que l'utilisateur a bien rentré un chiffre valide
        if ($index -match '^\d+$' -and [int]$index -ge 0 -and [int]$index -lt $nodes.Count) {
            $idx = [int]$index
            $nodeName = $nodes[$idx].name
            $newNodes = @()
            
            # Recrée le tableau JSON sans le noeud supprimé
            for ($i = 0; $i -lt $nodes.Count; $i++) {
                if ($i -ne $idx) {
                    $newNodes += $nodes[$i]
                }
            }
            $json.nodes = $newNodes
            $json | ConvertTo-Json -Depth 10 | Set-Content $configFile
            Write-Host "`n[Success] Node '$nodeName' has been deleted!" -ForegroundColor Green
            Write-Host "Restart the BOINC RPC app to apply changes." -ForegroundColor Yellow
        } else {
            Write-Host "`n[Error] Invalid selection." -ForegroundColor Red
        }
        Pause-Script
    }
    elseif ($choice -eq '3') {
        break
    }
}