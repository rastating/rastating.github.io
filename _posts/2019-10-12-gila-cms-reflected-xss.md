---
layout: post
title: Gila CMS Reflected XSS
date: 2019-10-12
categories:
  - disclosure
  - websec
  - security
tags:
  - disclosure
  - php
  - security
  - websec
  - CVE-2019-17535
image: /assets/images/2019-10-12-gila-cms-reflected-xss/gila-reflected-xss.png
---
Versions prior to and including 1.11.4 of Gila CMS are vulnerable to reflected cross-site scripting. On line 29 and 30 of the `blog-list.php` view found in both the `gila-blog` and `gila-mag` themes, the value of the user provided search criteria is printed back to the response without any sanitisation. This can result in cross-site scripting as can be seen in the below screenshot:

![](/assets/images/2019-10-12-gila-cms-reflected-xss/gila-reflected-xss.png)

Additionally, as HTTP only cookies are not in use, this can lead to a compromise of an admin session and lead to a takeover of the CMS.

Proof of Concept
----------------
`http://gila.host/?search=xss%22+onfocus%3D%22console.log%28document.domain%29%22+autofocus%3D%22true`

Versions Affected
-----------------
<= 1.11.4

Solution
--------
Update to a version later than 1.11.4 or apply the patch found at [https://github.com/GilaCMS/gila/pull/48](https://github.com/GilaCMS/gila/pull/48)

CVSS v3 Vector
--------------
[AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:N/E:F/RL:T/RC:R](https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator?vector=AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:N/E:F/RL:T/RC:R&version=3.1)

Disclosure Timeline
-------------------
- **2019-10-12**: Vulnerability found, pull request opened with fix
- **2019-10-12**: CVE requested
- **2019-10-13**: CVE-2019-17535 assigned
