$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = "C:\MyDownloads"
$watcher.Filter = "*.pdf"
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingEvents = $true

$action = {
    $path = $Event.SourceEventArgs.FullPath
    python -c "from paper2html import open_paper_htmls; open_paper_htmls('$path')"
}    
Register-ObjectEvent $watcher "Created" -Action $action

while ($true) {sleep 10}