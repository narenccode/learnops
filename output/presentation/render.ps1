param($in,$out)
$app=New-Object -ComObject PowerPoint.Application
$p=$app.Presentations.Open($in,$true,$false,$false)
New-Item -ItemType Directory -Force $out | Out-Null
$p.Export($out,"PNG",1300,900)
$p.Close(); $app.Quit()
