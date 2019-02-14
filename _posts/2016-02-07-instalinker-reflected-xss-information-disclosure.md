---
layout: post
title: InstaLinker Reflected XSS Information Disclosure
date: 2016-02-07
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - instalinker
  - reflected xss
excerpt: Due to a lack of input sanitization in the `includes/instalinker-admin-preview.php` file, it is possible to utilise a reflected XSS vector to run a script in the target user's browser and potentially compromise the WordPress installation.
---
## Homepage
[https://en-gb.wordpress.org/plugins/instalinker/](https://en-gb.wordpress.org/plugins/instalinker/)

## Overview
Due to a lack of input sanitization in the `includes/instalinker-admin-preview.php` file, it is possible to utilise a reflected XSS vector to run a script in the target user's browser and potentially compromise the WordPress installation.

There are numerous query string parameters that can be abused to use this vector, the first one can be found on line 17:
```php
<?php echo !empty($_GET['client_id']) ? 'data-il-client-id="' . $_GET['client_id'] . '"' : ""; ?>
```

## CVSS Score
5.3

## CVSS Vector
[(AV:N/AC:L/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C)](https://nvd.nist.gov/cvss.cfm?calculator&version=2&vector=(AV:N/AC:L/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C))

## Versions Affected
1.1.1 and below

## Solution
Upgrade to version 1.1.2

## Proof of Concept
http://target/wp-content/plugins/instalinker/includes/instalinker-admin-preview.php?client_id=%22%3E%3Cscript%3Ealert(1);%3C/script%3E%3Cdiv%20data-il-client-id=%22

## WordPress Exploit Framework Module
[exploit/xss/reflected/instalinker\_reflected\_xss\_shell\_upload](https://github.com/rastating/wordpress-exploit-framework/blob/development/lib/wpxf/modules/exploit/xss/reflected/instalinker_reflected_xss_shell_upload.rb)

## WPVDB-ID
[8382](https://wpvulndb.com/vulnerabilities/8382)

## Disclosure Timeline
* **2016-02-06**: Found [Original Publication](https://www.intelligentexploit.com/view-details.html?id=23244) of the vulnerability and contacted the vendor to make them aware along with a patch to fix the issue.
* **2016-02-07**: Vendor responded and released version 1.1.2 which includes the patch.
