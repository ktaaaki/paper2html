$watcher = New-Object System.IO.FileSystemWatcher
# set your download folder for pdf documents
$watcher.Path = "${HOME}/Downloads"
$watcher.Filter = "*.pdf"
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingEvents = $true

$action = {
    $path = $Event.SourceEventArgs.FullPath
    # set your browser path
    $browser_path = $env:SystemDrive + "\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    if (! (Test-Path $browser_path)){
        $browser_path = $env:SystemDrive + "\Program Files\Google\Chrome\Application\chrome.exe"
    }
    if (Test-Path $browser_path){
        python -c "from paper2html import open_paper_htmls; open_paper_htmls('$path', browser_path='$browser_path')"
    } else {
        python -c "from paper2html import open_paper_htmls; open_paper_htmls('$path')"
    }
}    
Register-ObjectEvent $watcher "Created" -Action $action

while ($true) {sleep 10}
