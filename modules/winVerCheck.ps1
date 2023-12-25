$registryData = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion' -Name CurrentMajorVersionNumber, CurrentMinorVersionNumber, CurrentBuildNumber, UBR -ErrorAction SilentlyContinue
if ($?) {
    '{0}.{1}.{2}.{3}' -f @(
        $registryData.CurrentMajorVersionNumber,
        $registryData.CurrentMinorVersionNumber,
        $registryData.CurrentBuildNumber,
        $registryData.UBR
    )
}