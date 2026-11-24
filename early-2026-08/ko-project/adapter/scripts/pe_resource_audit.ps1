param(
    [Parameter(Mandatory = $true)]
    [string]$Root
)

$ErrorActionPreference = 'Stop'

function Read-U16([byte[]]$Bytes, [int]$Offset) {
    [BitConverter]::ToUInt16($Bytes, $Offset)
}

function Read-U32([byte[]]$Bytes, [int]$Offset) {
    [BitConverter]::ToUInt32($Bytes, $Offset)
}

$typeNames = @{
    1 = 'CURSOR'; 2 = 'BITMAP'; 3 = 'ICON'; 4 = 'MENU'; 5 = 'DIALOG'
    6 = 'STRING'; 7 = 'FONTDIR'; 8 = 'FONT'; 9 = 'ACCELERATOR'
    10 = 'RCDATA'; 11 = 'MESSAGETABLE'; 12 = 'GROUP_CURSOR'
    14 = 'GROUP_ICON'; 16 = 'VERSION'; 23 = 'HTML'; 24 = 'MANIFEST'
}

foreach ($fileName in @(
    'NightRemaster.exe',
    'OpenSaveFolder.exe',
    'ResetConfig.exe',
    'Uninstaller.exe'
)) {
    $path = Join-Path $Root $fileName
    [byte[]]$bytes = [IO.File]::ReadAllBytes($path)
    $peOffset = Read-U32 $bytes 0x3c
    $sectionCount = Read-U16 $bytes ($peOffset + 6)
    $optionalSize = Read-U16 $bytes ($peOffset + 20)
    $optionalOffset = $peOffset + 24
    $magic = Read-U16 $bytes $optionalOffset
    $dataDirectoryOffset = $optionalOffset + $(if ($magic -eq 0x20b) { 112 } else { 96 })
    $resourceRva = Read-U32 $bytes ($dataDirectoryOffset + 16)
    $resourceSize = Read-U32 $bytes ($dataDirectoryOffset + 20)
    $sectionHeaders = $optionalOffset + $optionalSize

    function Convert-RvaToOffset([uint32]$Rva) {
        for ($sectionIndex = 0; $sectionIndex -lt $sectionCount; $sectionIndex++) {
            $sectionOffset = $sectionHeaders + (40 * $sectionIndex)
            $virtualSize = Read-U32 $bytes ($sectionOffset + 8)
            $virtualAddress = Read-U32 $bytes ($sectionOffset + 12)
            $rawSize = Read-U32 $bytes ($sectionOffset + 16)
            $rawOffset = Read-U32 $bytes ($sectionOffset + 20)
            $extent = [Math]::Max($virtualSize, $rawSize)
            if ($Rva -ge $virtualAddress -and $Rva -lt ($virtualAddress + $extent)) {
                return [int]($rawOffset + ($Rva - $virtualAddress))
            }
        }
        return $null
    }

    $resourceBase = Convert-RvaToOffset $resourceRva
    Write-Output "=== $fileName resource_size=$resourceSize ==="
    if ($null -eq $resourceBase) {
        Write-Output 'NO_RESOURCE_SECTION'
        continue
    }

    function Convert-ResourceName([uint32]$Value) {
        [uint64]$wide = $Value
        if ($wide -ge 2147483648) {
            $nameOffset = $resourceBase + [int]($wide - 2147483648)
            $length = Read-U16 $bytes $nameOffset
            return [Text.Encoding]::Unicode.GetString($bytes, $nameOffset + 2, $length * 2)
        }
        return [string]$wide
    }

    $leaves = [Collections.Generic.List[object]]::new()

    function Read-ResourceDirectory([int]$RelativeOffset, [object[]]$PathParts) {
        $directoryOffset = $resourceBase + $RelativeOffset
        $entryCount = (Read-U16 $bytes ($directoryOffset + 12)) +
            (Read-U16 $bytes ($directoryOffset + 14))
        for ($entryIndex = 0; $entryIndex -lt $entryCount; $entryIndex++) {
            $entryOffset = $directoryOffset + 16 + (8 * $entryIndex)
            $resourceName = Convert-ResourceName (Read-U32 $bytes $entryOffset)
            [uint64]$value = Read-U32 $bytes ($entryOffset + 4)
            [object[]]$newPath = @($PathParts) + @($resourceName)
            if ($value -ge 2147483648) {
                Read-ResourceDirectory ([int]($value - 2147483648)) $newPath
                continue
            }

            $dataEntryOffset = $resourceBase + [int]$value
            $dataRva = Read-U32 $bytes $dataEntryOffset
            $dataSize = Read-U32 $bytes ($dataEntryOffset + 4)
            $codePage = Read-U32 $bytes ($dataEntryOffset + 8)
            $leaves.Add([pscustomobject]@{
                Path = $newPath -join '/'
                Type = $newPath[0]
                Name = $newPath[1]
                Language = $newPath[2]
                Offset = Convert-RvaToOffset $dataRva
                Size = $dataSize
                CodePage = $codePage
            })
        }
    }

    Read-ResourceDirectory 0 @()

    foreach ($group in ($leaves | Group-Object Type | Sort-Object Name)) {
        $typeId = 0
        $isNumericType = [int]::TryParse([string]$group.Name, [ref]$typeId)
        $label = if ($isNumericType -and $typeNames.ContainsKey($typeId)) {
            $typeNames[$typeId]
        } else {
            [string]$group.Name
        }
        $totalBytes = ($group.Group | Measure-Object Size -Sum).Sum
        Write-Output "TYPE $($group.Name) ($label): $($group.Count) leaf(s), $totalBytes bytes"
    }

    foreach ($resource in $leaves) {
        if ($null -eq $resource.Offset -or $resource.Size -le 0) {
            continue
        }
        [byte[]]$blob = [byte[]]::new($resource.Size)
        [Array]::Copy($bytes, $resource.Offset, $blob, 0, $resource.Size)
        $texts = [Collections.Generic.List[string]]::new()

        $resourceTypeId = 0
        $numericResourceType = [int]::TryParse([string]$resource.Type, [ref]$resourceTypeId)

        if ($numericResourceType -and $resourceTypeId -eq 6) {
            $offset = 0
            for ($index = 0; $index -lt 16 -and ($offset + 2) -le $blob.Length; $index++) {
                $length = Read-U16 $blob $offset
                $offset += 2
                if ($length -gt 0 -and ($offset + ($length * 2)) -le $blob.Length) {
                    $texts.Add([Text.Encoding]::Unicode.GetString($blob, $offset, $length * 2))
                    $offset += $length * 2
                }
            }
        } elseif ($numericResourceType -and $resourceTypeId -in @(4, 5, 10, 11, 16, 23, 24)) {
            $unicode = [Text.Encoding]::Unicode.GetString($blob)
            foreach ($match in [regex]::Matches(
                $unicode,
                '[\u0020-\u007E\u3000-\u30FF\u3400-\u9FFF\uFF01-\uFFEE]{2,}'
            )) {
                $texts.Add($match.Value)
            }
        }

        $shown = @(
            $texts |
                Where-Object { $_ -match '[\u3040-\u30FF\u3400-\u9FFF]' } |
                Sort-Object -Unique
        )
        if ($shown.Count -gt 0) {
            Write-Output "[$($resource.Path)] $($shown -join ' | ')"
        }
    }
}
