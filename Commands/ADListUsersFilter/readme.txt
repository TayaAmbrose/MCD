Obfuscated: False
Type: InformationGather
Name: ListADUsers.ps1
Exec: 
	Classification: Benign
	Command: powershell -Command "Start-Process powershell -Verb runAs -ArgumentList '-noexit','-ExecutionPolicy','bypass','-File','%PAYLOAD%'"