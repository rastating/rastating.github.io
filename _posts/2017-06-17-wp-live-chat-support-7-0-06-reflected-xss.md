---
layout: single
title: WP Live Chat Support <= 7.0.06 Reflected XSS
date: 2017-06-17
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - wp-live-chat-support
  - reflected xss
excerpt: Due to a lack of CSRF mitigation and entity encoding in `wp-live-chat-support.php`, it is possible to execute scripts in the context of an admin user by including a script in the `cid` field in a GET request.
---
## Homepage
[https://wordpress.org/plugins/wp-live-chat-support/](https://wordpress.org/plugins/wp-live-chat-support/)

## Overview
Due to a lack of CSRF mitigation and entity encoding in `wp-live-chat-support.php`, it is possible to execute scripts in the context of an admin user by including a script in the `cid` field in a GET request.

## CVSS Score
4.8

## CVSS Vector
[(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C)](https://nvd.nist.gov/vuln-metrics/cvss/v2-calculator?vector=(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C))

## Versions Affected
7.0.06 and below

## Solution
Upgrade  to version 7.0.07 or newer

## WordPress Exploit Framework Module
[exploit/xss/reflected/wp\_live\_chat\_support\_reflected\_xss\_shell\_upload](https://github.com/rastating/wordpress-exploit-framework/blob/development/modules/exploit/xss/reflected/wp_live_chat_support_reflected_xss_shell_upload.rb)

## Proof of Concept
`http://target/wp-admin/admin.php?page=wplivechat-menu-history&wplc_action=remove_cid&cid=0'><script>alert(document.cookie)<%2Fscript><span class='`

## WPVDB-ID
[8843](https://wpvulndb.com/vulnerabilities/8843)
