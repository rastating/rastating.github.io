---
layout: single
title: "Capturing Network Traffic using the WiFi Pineapple, tcpdump and Android"
date: 2012-08-26 22:05:00 +0100
categories:
  - security
  - android
tags:
  - wifi pineapple
  - tcpdump
  - wireshark
  - hak5
  - mitm
  - man in the middle
  - packet capture
---
First off I'd just like to say props to [Robin Wood](http://www.digininja.org/), [Darren Kitchen](http://hak5.org/), [Sebastian Kinne](http://sebkinne.com/), [Rob Fuller](http://www.room362.com/) and everyone else who has contributed to the WiFi Pineapple project, you've done a great job!

There are a few things in this guide that I’m not going to cover (such as rooting your device, the ins and outs of WireShark etc.), however I'll add links to appropriate reading material for these things where I can! And if you're still stuck feel free to ask for help in the comments.

## Why not just use tcpdump on the pineapple itself?
The reason I ended up trying to do this is due to the fact that the pineapple only has the one USB port, and I don't have a powered USB hub, so I thought – "Hey, why not just capture the traffic on my phone seeing as it's tethering to the pineapple anyway?".

In addition to not requiring a USB hub, it also has the benefit of not soaking up more battery power from the pineapple itself as it doesn't have to power a pen drive and write data to it constantly.

## What do we need to get started?
*    A WiFi Pineapple MKIV, available from [The HakShop](http://hakshop.myshopify.com/collections/gadgets/products/wifi-pineapple) - I'd recommend the elite bundle for the extra goodies and as a means of helping support the project!
*    A rooted Android device with the [Shark for Root](https://play.google.com/store/apps/details?id=lv.n3o.shark&hl=en) app installed
*    A program capable of viewing pcap files. For this example I’ll be using [WireShark](http://www.wireshark.org/)

*N.B. I should point out, at this point in time I am using version 2.6.1 of the firmware, which supports Android tethering without much extra configuration. If you are using an earlier version you may need to follow [This Guide](http://forums.hak5.org/index.php?/topic/26601-mk4-android-tethering-how-to/) by wiregr.*

## Setting up the pineapple
First thing's first, power up your pineapple and give it a few minutes to finish booting. After it's booted and ready to go, plug in your Android device via USB as in the picture below and enable USB tethering from your settings menu. The location of the tethering option can vary from device to device, but on my Samsung Galaxy S2 it can be found in Settings > Wireless and networks > Tethering and portable hotspot > USB tethering.

[![](/assets/images/capturing-network-traffic-using-the-wifi-pineapple-tcpdump-and-android/DSC_0026.jpg)](/assets/images/capturing-network-traffic-using-the-wifi-pineapple-tcpdump-and-android/DSC_0026.jpg)

Give this a moment to begin tethering and then connect to the pineapple, either by Ethernet or by WiFi. Once connected to the pineapple network, SSH into the device (default credentials are root:pineapplesareyummy) and attempt to ping Google or any other external address to ensure that the Android device is indeed tethering to the pineapple.

[![](/assets/images/capturing-network-traffic-using-the-wifi-pineapple-tcpdump-and-android/connectivity_test.jpg)](/assets/images/capturing-network-traffic-using-the-wifi-pineapple-tcpdump-and-android/connectivity_test.jpg)

Once we know the Internet connection from the Android device is definitely tethered to the pineapple, we need to configure iptables to route the traffic from the connected clients via the usb0 interface. You can either do this via the SSH session we have open, or by logging in to the pineapple's web control panel and copying and pasting the commands into the "Execute Commands" box in the advanced tab.

The commands you need to execute are:

```bash
iptables -t nat -A POSTROUTING -s 172.16.42.0/24 -o usb0 -j MASQUERADE
iptables -A FORWARD -s 172.16.42.0/24 -o usb0 -j ACCEPT
iptables -A FORWARD -d 172.16.42.0/24 -m state --state ESTABLISHED,RELATED -i usb0 -j ACCEPT
```

This will have to be done every time you restart the pineapple, however you could throw it in a script if you wanted and make it run automatically on startup if you so wish.

*N.B. At the time of writing this (August, 2012), the iptables configuration is necessary, however I believe that the Jasager team have plans to make this automatic in the future.*

## Setting up the Android device
Now that our pineapple is setup and ready to go, we need to setup the Android device to capture traffic (this is much simpler than you may think).

As mentioned in the first section, your Android device **must** be rooted in order to run the app we need to capture traffic. As rooting devices is a topic (and in some cases challenge) of its own, I'm not going to go over it here. If you do need to root your device though, I'd recommend checking out [This Guide](http://forum.xda-developers.com/showthread.php?t=1746794) at XDA-Developers. I have tested it, it works, and is about the fastest way you could root your device!

Now, the only thing we need for this step is an app available from the Google Play Store which is called Shark for Root, developed by [Elviss Kuštans](https://play.google.com/store/apps/developer?id=Elviss+Ku%C5%A1tans). You can download Shark for Root free from the following page: https://play.google.com/store/apps/details?id=lv.n3o.shark&hl=en

## Capturing the traffic
Once you've installed it, open it up and if presented with a screen asking your permission for it to use root access go ahead and accept it. The screen you'll be presented with is pretty straight forward, there is a parameters input field which will let you specify the parameters you want to pass through to tcpdump (leave this as it is if you're not familiar with it).

When you're ready to begin monitoring the traffic hit the button labelled "Start" and the status should change to "Running", with some information about the data it is capturing.

[![](/assets/images/capturing-network-traffic-using-the-wifi-pineapple-tcpdump-and-android/Screenshot_2012_08_26_21_03_04.png)](/assets/images/capturing-network-traffic-using-the-wifi-pineapple-tcpdump-and-android/Screenshot_2012_08_26_21_03_04.png)

Now head over to another device that is connected to the pineapple and navigate to Google and search for something (for this example I'm going to search for "herpy derp derp"). Once the page has loaded you can go back to your Android device and click the stop button. After stopping Shark, make sure to take note of the filename so you know which file you are going to be working with.

[![](/assets/images/capturing-network-traffic-using-the-wifi-pineapple-tcpdump-and-android/Screenshot_2012_08_26_21_04_47.png)](/assets/images/capturing-network-traffic-using-the-wifi-pineapple-tcpdump-and-android/Screenshot_2012_08_26_21_04_47.png)

## Examining the captured data
I'm not going to go into much depth here as again examining network captures is a topic of its own, and if you're up to this point you probably know what to be doing with a pcap file anyway.

Plug your Android device into your computer and copy over the pcap file that Shark exported to in the previous step, and open it up in WireShark.

What you see now is all the data that passed through the pineapple to the Android device, and anything else that the phone was doing on the network it was connected to.

If you want to filter this down to HTTP traffic, type "http" in the filter field and hit enter. As you can see in the screenshot below, the Google search for "herpy derp derp" was successfully captured.

[![](/assets/images/capturing-network-traffic-using-the-wifi-pineapple-tcpdump-and-android/wireshark.jpg)](/assets/images/capturing-network-traffic-using-the-wifi-pineapple-tcpdump-and-android/wireshark.jpg)

## The covering my ass section
It goes without saying that to be doing this on a public network without the users' permission is **illegal** due to the fact you can capture sensitive data via these means such as login credentials. If you're going to do this and don't want to have your hands slapped in the process, do it with your own devices or seek permission from people first who's data you’ll be capturing.

If you are going to insist on doing this in public (which again, I am not encouraging!), at least don't be an ass hat about it by screwing around with any personal data you may find; play nice!
