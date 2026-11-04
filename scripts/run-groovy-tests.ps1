param([Parameter(Mandatory=$true)][string]$TestFile)
$root = Split-Path -Parent $PSScriptRoot
$java = Join-Path $root 'runtime\bin\java.exe'
if (-not (Test-Path -LiteralPath $java)) {
  $java8 = Get-ChildItem -LiteralPath "$env:ProgramFiles\Java" -Directory -Filter 'jre1.8*' -ErrorAction SilentlyContinue |
    Sort-Object Name -Descending | Select-Object -First 1
  if ($java8) { $java = Join-Path $java8.FullName 'bin\java.exe' } else { $java = 'java' }
}
$jars = Get-ChildItem -LiteralPath (Join-Path $root 'lib') -Filter '*.jar' | ForEach-Object FullName
$extra = Get-ChildItem -LiteralPath (Join-Path $root 'jars') -Filter '*.jar' -ErrorAction SilentlyContinue | ForEach-Object FullName
$cp = (@($jars) + @($extra) + @((Join-Path $root 'classes'), $root)) -join [IO.Path]::PathSeparator
& $java '-cp' $cp 'groovy.ui.GroovyMain' (Join-Path $root $TestFile)
exit $LASTEXITCODE
