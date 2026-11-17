# Prepare the vendor updater and patched firmware locally. No USB/device writes.
[CmdletBinding()]
param(
    [string]$OfficialZip,
    [string]$OutputDirectory = (Join-Path $PSScriptRoot 'Firmware Package'),
    [switch]$NoLaunch
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$SourceUrl = 'https://retro-bit.com/sitepad-data/uploads/2025/07/V2-USB-Receiver-Pro-Controller-1.1-Firmware-Switch-2-Compatibility.zip'
$ArchiveHash = '69ac4480738d2c5c3929dd92ce89cd1cf91ec204f866a6f830987c40d3dcd6c3'
$StockHash = '12c69fc5ebd2e76e40394428960548b79fe44e5a69d728691a8ad52b478bd55a'
$UpdaterHash = '27f11a4bb3becc5426025025fe376d45f9b6da54f41a347750466f069592b4d7'
$DecodedHash = '996a4eaed2ea0fd570b4960e6a1d85d15f0a0f1e747d63173e3e179d0158df76'
$FirmwareHash = '951904f60c5730deaeb92db09039a9c594e2c70e9d8e34b3c14bcbf103dcea54'
$FirmwareName = 'retrobit_usb_pro_1.1_polymega.bxw'
$ArchiveRoot = 'V2 USB Receiver - Pro Controller - 1.1 Firmware - Switch 2 Compatibility/V2 USB Receiver - SEGA Controller - 1.0 Firmware/'
$InstructionsName = 'Retro-Bit V2 USB Receiver for Pro Controllers - Firmware Installation.pdf'
$UpdaterFiles = @('BxUpdateLib.dll', 'BxUsbUpdate.exe', 'hidapi.dll', 'ucrtbased.dll', 'vcruntime140d.dll', 'wolfssl.dll')

# This table is generated from the Python patch builder when packaging a release.
$PatchTableJson = @'
@@PATCH_TABLE_JSON@@
'@

$FirmwareReadme = @'
Retro-Bit Saturn Pro on Polymega

USE AT YOUR OWN RISK. Unofficial firmware; supplied AS IS without
warranty or promised repair/replacement. Flashing can brick the receiver;
recovery is not guaranteed. V2 USB RECEIVER ONLY, never the controller itself,
Saturn-port receiver, or V1 receiver.

INSTALL
Read the included Retro-Bit installation PDF and follow its receiver-update
procedure on Windows. In BxUsbUpdate.exe, select the .bxw in this package's
Firmware folder. Keep the receiver connected until the update finishes.
After updating, re-sync (pair) the receiver with the controller before playing.
The updater and PDF were downloaded from Retro-Bit; they are not an endorsement
of this modified image. Keep the original stock download for possible recovery.

USE
Use USB mode with two green lights on Polymega (three on Mac).
Hold a shortcut, then release:
- Start + Right: Street Fighter layout (C/Z swap).
- Start + Up: SEGA layout. Relative to Street Fighter layout, X/A/B actions
  move to A/B/C and C's action moves to X. Y/Z/ZL/ZR keep the same outputs.
Repeat the active shortcut for stock. The other selects its layout directly;
they do not stack. Reconnecting the receiver restores stock.
Duplicate shoulder L/R follow C/Z. For analog games, enable Analog in
Polymega's own in-game controller settings.

SEGA layout targets games whose A/B/C actions fall on physical X/A/B.
These are manual presets; the receiver does not identify games. These custom
presets have not been separately confirmed on other hosts.

Version 1.0 uses the same firmware bytes as alpha.6. Both layouts were tested
and reported working on the author's receiver with Polymega on November 16,
2026. If alpha.6 is already installed, no new flash is needed. This is one
setup's result; recovery after a failed flash remains untested.

Project, full risk notice, and technical details:
https://github.com/SuperWes/retro-bit-2.4-wireless-pro-controller-polymega-custom-firmware
'@

function Get-BytesHash([byte[]]$Bytes) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        return [BitConverter]::ToString($sha.ComputeHash($Bytes)).Replace('-', '').ToLowerInvariant()
    } finally { $sha.Dispose() }
}

function Assert-That([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

function Convert-Hex([string]$Hex) {
    Assert-That ($Hex.Length % 2 -eq 0) 'Invalid patch data.'
    $result = New-Object byte[] ($Hex.Length / 2)
    for ($i = 0; $i -lt $result.Length; $i++) {
        $result[$i] = [Convert]::ToByte($Hex.Substring($i * 2, 2), 16)
    }
    return ,$result
}

function Read-Entry($Archive, [string]$Name) {
    $entry = $Archive.GetEntry($ArchiveRoot + $Name)
    Assert-That ($null -ne $entry) "Missing official package file: $Name"
    $stream = $entry.Open()
    $buffer = New-Object IO.MemoryStream
    try {
        $stream.CopyTo($buffer)
        return ,$buffer.ToArray()
    } finally {
        $stream.Dispose()
        $buffer.Dispose()
    }
}

$stage = $null
$zipStream = $null
$archive = $null
try {
    $destination = [IO.Path]::GetFullPath($OutputDirectory)
    Assert-That (-not (Test-Path -LiteralPath $destination)) "Output already exists: $destination. Use the prepared updater there, or move that folder before running this again."
    Write-Host 'USE AT YOUR OWN RISK. V2 USB receiver only. Recovery is not guaranteed.'
    if ($OfficialZip) {
        $zipBytes = [IO.File]::ReadAllBytes([IO.Path]::GetFullPath($OfficialZip))
    } else {
        Write-Host 'Downloading the official package directly from Retro-Bit...'
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        $client = New-Object Net.WebClient
        try { $zipBytes = $client.DownloadData($SourceUrl) }
        finally { $client.Dispose() }
    }
    Assert-That ((Get-BytesHash $zipBytes) -eq $ArchiveHash) 'The official ZIP does not match the supported version. Nothing was installed.'
    Add-Type -AssemblyName System.IO.Compression
    $zipStream = [IO.MemoryStream]::new($zipBytes, $false)
    $archive = [IO.Compression.ZipArchive]::new($zipStream, [IO.Compression.ZipArchiveMode]::Read)
    $stock = Read-Entry $archive 'Firmware/RB V2 USB Analog Controller_1.1_20250612.bxw'
    $updater = Read-Entry $archive 'Update Program/BxUsbUpdate.exe'
    Assert-That ($stock.Length -eq 32768 -and (Get-BytesHash $stock) -eq $StockHash) 'Wrong stock firmware.'
    Assert-That ((Get-BytesHash $updater) -eq $UpdaterHash) 'Wrong updater executable.'

    Write-Host 'Preparing the Polymega firmware...'
    $encode = New-Object byte[] 256
    [Array]::Copy($updater, 0x4124, $encode, 0, 256)
    Assert-That (@($encode | Select-Object -Unique).Count -eq 256) 'Invalid byte permutation.'
    $decode = New-Object byte[] 256
    for ($i = 0; $i -lt 256; $i++) { $decode[$encode[$i]] = $i }
    $decoded = New-Object byte[] $stock.Length
    for ($i = 0; $i -lt $stock.Length; $i++) { $decoded[$i] = $decode[$stock[$i]] }
    Assert-That ((Get-BytesHash $decoded) -eq $DecodedHash) 'Wrong decoded firmware.'
    foreach ($patch in (ConvertFrom-Json $PatchTableJson)) {
        $before = Convert-Hex $patch.before
        $after = Convert-Hex $patch.after
        $offset = [int]$patch.offset
        Assert-That ($before.Length -eq $after.Length -and $offset -ge 0 -and ($offset + $after.Length) -le $decoded.Length) 'Invalid patch region.'
        for ($i = 0; $i -lt $before.Length; $i++) {
            Assert-That ($decoded[$offset + $i] -eq $before[$i]) 'Unexpected original firmware instruction.'
            $decoded[$offset + $i] = $after[$i]
        }
    }
    $firmware = New-Object byte[] $decoded.Length
    for ($i = 0; $i -lt $decoded.Length; $i++) { $firmware[$i] = $encode[$decoded[$i]] }
    Assert-That ((Get-BytesHash $firmware) -eq $FirmwareHash) 'Patched firmware checksum failed. Nothing was installed.'

    # Write only known paths after checking the complete official ZIP and output.
    $stage = $destination + '.tmp-' + [Guid]::NewGuid().ToString('N')
    [void][IO.Directory]::CreateDirectory((Join-Path $stage 'Firmware'))
    [void][IO.Directory]::CreateDirectory((Join-Path $stage 'Update Program'))
    [IO.File]::WriteAllBytes((Join-Path $stage ('Firmware/' + $FirmwareName)), $firmware)
    foreach ($name in $UpdaterFiles) {
        [IO.File]::WriteAllBytes((Join-Path $stage ('Update Program/' + $name)), (Read-Entry $archive ('Update Program/' + $name)))
    }
    [IO.File]::WriteAllBytes((Join-Path $stage $InstructionsName), (Read-Entry $archive $InstructionsName))
    [IO.File]::WriteAllText((Join-Path $stage 'README.txt'), $FirmwareReadme + "`r`n", [Text.Encoding]::UTF8)
    [IO.Directory]::Move($stage, $destination)
    $stage = $null
    Write-Host "Ready: $destination"
    Write-Host 'Read the included installation PDF before flashing.'
    Write-Host "In the updater, select Firmware\$FirmwareName."
    Write-Host 'After updating, re-sync the receiver with the controller before playing.'
    if (-not $NoLaunch) {
        $program = Join-Path $destination 'Update Program/BxUsbUpdate.exe'
        Start-Process -FilePath $program -WorkingDirectory (Join-Path $destination 'Update Program')
    }
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
} finally {
    if ($archive) { $archive.Dispose() }
    if ($zipStream) { $zipStream.Dispose() }
    if ($stage -and [IO.Directory]::Exists($stage)) { [IO.Directory]::Delete($stage, $true) }
}
