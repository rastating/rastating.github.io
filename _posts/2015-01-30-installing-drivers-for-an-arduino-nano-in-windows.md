---
layout: post
title: Installing Drivers for an Arduino Nano in Windows
date: 2015-01-30 23:47:00 +0100
categories:
  - programming
  - hardware
  - arduino
  - electronics
  - windows
tags:
  - ft232r usb uart
  - driver
---
If you are attempting to use an Arduino Nano on a Windows machine and having no luck finding drivers automatically, chances are it is due to a counterfeit FTDI chip which unfortunately does not work with the automatic driver finding functionality in Windows.

Thankfully, there is a solution if you are running into this problem! Start off by downloading the drivers from the official FTDI site via [http://www.ftdichip.com/Drivers/CDM/CDM%20v2.12.00%20WHQL%20Certified.zip](http://www.ftdichip.com/Drivers/CDM/CDM%20v2.12.00%20WHQL%20Certified.zip) (a mirror can be found [Here](https://mega.co.nz/#!XRsFhKZD!GYfC83h701XkbhT7OO3GkOtnaENl-aNyHKWjmCqOWEQ), in case the official link dies in the future).

Once downloaded, unzip the archive and then head to the device manager (Control Panel > Administrative Tools > Computer Management > Device Manager), you should see a device with a yellow exclamation mark next to it labelled "FT232R USB UART", or possibly a slight variation if using a different FTDI chip. Right click this entry and click `Update Driver Software...`.

On the next prompt, choose the option labelled "Browse my computer for driver software", and on the next prompt choose "Let me pick from a list of device drivers on my computer". You will now be presented with a list of device driver types. Highlight `USB Serial Converter` and click the button labelled "Have Disk..."

![](/assets/images/installing-drivers-for-an-arduino-nano-in-windows/ft232r_usb_uart_usb_serial_converter.png)

You will now be presented with an open file prompt, click browse and select the file called `ftdibus.inf` that is in the root folder of the archive we extracted earlier and confirm all the open prompts to install the driver.

Now that is done, you will see a new device with a yellow exclamation mark next to it, labelled "USB Serial Port". Follow the same steps as we did for the `FT232R USB UART` device, but this time, when choosing the device driver, select `USB Serial Port` instead and click the `Have Disk...` button:

![](/assets/images/installing-drivers-for-an-arduino-nano-in-windows/usb_serial_port.png)

This time, the driver file you need to select is the `ftdiport.inf` file that is located in the same root folder of the archive that we used previously. Once again, confirm all the open windows and the driver installation will be complete.

Now when you load up the Arduino IDE you should see it select the correct COM port and you should now be able to upload sketches to your Arduino Nano.
