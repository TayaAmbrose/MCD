Obfuscated: True
Type: Loader
Name: Amdey.Noexec.ps1
Exec: 
	Classification: Malicious
	Command: powershell -Command "Start-Process powershell -Verb runAs -ArgumentList '-noexit','-ExecutionPolicy','bypass','-File','%PAYLOAD%'"