---
layout: post
title: Fixing "Driver not available, application will exit" error when launching SteelSeries Engine
date: 2014-05-29 21:36:00 +0100
categories:
  - hardware
tags:
  - steelseries
  - synology disk assistant
  - error
  - driver
---
After having bought the Diablo 3 [Mouse](http://steelseries.com/products/games/diablo-iii/steelseries-diablo-iii-mouse) and [Headset](http://steelseries.com/us/products/games/diablo-iii/steelseries-diablo-iii-headset), I decided to pick up a new keyboard from SteelSeries too given how good the quality of the previous two products were.

Today my new [SteelSeries APEX Keyboard](http://steelseries.com/products/keyboards/steelseries-apex-gaming-keyboard) arrived and it is great; the only problem was that when trying to launch the SteelSeries Engine, the software which provides the macro key functionaity, it would not load.

Every time I tried to load it, I got the error "Driver not available, application will exit.", on my Windows 7 (64 bit) machine; thankfully, I found the cause and found a solution.

The problem in my case, was quite an obscure one, which was caused by having previously installed the Synology Disk Assistant software for my Synology NAS box, which installed a virtual device on my system called "Synology Virtual USB Hub"

![](/assets/images/fixing-driver-not-available-application-will-exit-error-when-launching-steelseries-engine/synology-virtual-usb-hub.png)

If you are experiencing this same problem and are the owner of a Synology NAS box, there is a good chance this is what the problem is.

Here are the steps I took to resolve the problem:

1. Uninstall both the Synology Disk Assistant and the SteelSeries Engine
2. Delete `C:\Windows\system32\DRIVERS\busenum.sys` (if still present)
3. Delete `C:\Windows\system32\DRIVERS\SteelBus64.sys` (if still present)
4. Restart the system
5. Open Device Manager (Control Panel > Administrative Tools > Computer Management > Device Manager), if not running as an administrator ensure you right click Computer Management and click 'Run as Administrator'
6. Expand the 'System devices' node and find the item named 'Synology Virtual USB Hub'. Right click it and click 'Uninstall'
7. Restart the system, again.
8. Reinstall the SteelSeries Engine

The SteelSeries Engine *should* run without issue now.
