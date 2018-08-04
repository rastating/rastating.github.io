---
layout: single
title: Unrestricted File Upload via Plugin Uploader in WordPress
date: 2018-08-04
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - CVE-2018-14028
---
On 11th July, 2018, a pull request was opened on the [WordPress Exploit Framework GitHub Page](https://github.com/rastating/wordpress-exploit-framework/pull/52) to add a new feature that a user ([Vinicius Marangoni](https://github.com/viniciusmarangoni)) had created whilst completing a boot2root machine from VulnHub.

The scenario encountered by the user was that the plugins directory did not have write permissions, preventing them from using the [Admin Shell Upload Module](https://github.com/rastating/wordpress-exploit-framework/blob/master/modules/exploit/shell/admin_shell_upload.rb). This led to the discovery that if they were to upload PHP files instead of ZIP files in the plugin uploader - WordPress would accept the files, and then leave a copy in the uploads directory after it failed to process it as a ZIP - leaving a PHP file to be executed.

 As he did not realise this was a flaw within the core code, I quickly raised the issue with WordPress and contacted Vinicius to let him know that he had stumbled upon a bug which needs to be patched and that would hopefully score a bounty for him.

 After a bit of chasing, WordPress responded, but unfortunately did not deem the issue to be within the scope of WordPress and felt that the security issues posed by this were due to server configuration.

 I put forward (and still maintain) that this needs to be patched as it is not uncommon to see people revoke write permissions on the `wp-content/plugins` directory, in order to prevent plugins being uploaded. By not validating file types, and not cleaning up after failed uploads, it can allow the compromise of an administrator account to escalate into a compromise of the web server user account via remote code execution.

Despite the disagreement on whether the security issue imposed by this is the responsibility of WordPress to mitigate - there was a mutual agreement that it's something that should be fixed on a functional level. Alongside the closure of the report on HackerOne, an issue was raised on [Trac](https://core.trac.wordpress.org/ticket/44710) to remedy the issue.

CVE-ID
------
[CVE-2018-14028](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2018-14028)

Versions Affected
-----------------
All versions as of 4th August, 2018

Timeline
--------
* **2018-07-11**: Initial discovery and report via HackerOne
* **2018-07-24**: Request update due to no acknowledgement from vendor
* **2018-08-02**: Initial response from vendor
* **2018-08-03**: Report closed by vendor as non-urgent / out of scope
* **2018-08-04**: Public disclosure of issue

References
----------
* [GitHub: upload non-encapsulated payload when zip installation fails #52](https://github.com/rastating/wordpress-exploit-framework/pull/52)
* [Trac: Upload plugin and theme functionalities are not removing uploaded files after failure conditions.](https://core.trac.wordpress.org/ticket/44710)
