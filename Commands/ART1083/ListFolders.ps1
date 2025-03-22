$folderarray = @("Desktop", "Downloads", "Documents", "AppData/Local", "AppData/Roaming")
Get-ChildItem -Path $env:homedrive -ErrorAction SilentlyContinue | Out-File -append output.txt
Get-ChildItem -Path $env:programfiles -erroraction silentlycontinue | Out-File -append output.txt
Get-ChildItem -Path "${env:ProgramFiles(x86)}" -erroraction silentlycontinue | Out-File -append output.txt
$UsersFolder = "$env:homedrive\Users\"
foreach ($directory in Get-ChildItem -Path $UsersFolder -ErrorAction SilentlyContinue) 
{
foreach ($secondarydirectory in $folderarray)
{Get-ChildItem -Path "$UsersFolder/$directory/$secondarydirectory" -ErrorAction SilentlyContinue | Out-File -append output.txt
}
cat output.txt