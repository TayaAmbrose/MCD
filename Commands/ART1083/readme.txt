Obfuscated: False
Type: Information Gathering
Name: ListFolders.ps1
Exec: 
	Classification: Malicious
	Command: powershell -Command "Start-Process powershell -Verb runAs -ArgumentList '-noexit','-ExecutionPolicy','bypass','-File','%PAYLOAD%'"