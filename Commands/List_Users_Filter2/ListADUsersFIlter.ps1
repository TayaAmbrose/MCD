([adsisearcher]"(&(objectCategory=person)(samaccountname=p*))").FindAll() | ForEach-Object { $_.Properties.samaccountname }