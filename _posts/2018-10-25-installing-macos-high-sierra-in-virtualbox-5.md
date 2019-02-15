---
layout: post
title: Installing MacOS High Sierra in VirtualBox 5
date: 2018-10-25
categories:
  - macos
tags:
  - high sierra
  - virtualbox
image: /assets/images/installing-macos-high-sierra-in-virtualbox-5/uefi.png
---
During a recent pentest, I needed to throw together a macOS virtual machine. Although there was lots of guides around the web, none seemed to work from start to finish. This post contains the steps I extracted from various resources in order to get a fully working High Sierra install within VirtualBox 5.

Step 1: Download The High Sierra Installer
------------------------------------------
To do this, you need to be on an existing macOS system. I was unable to find the download within the App Store itself, but following this link opened the App Store at the correct page: [https://itunes.apple.com/us/app/macos-high-sierra/id1246284741?mt=12](https://itunes.apple.com/us/app/macos-high-sierra/id1246284741?mt=12)

After opening the aforementioned page in the App Store, start the download, but cancel the installation when it starts.

You can then verify that the installer has been downloaded by checking that `"/Applications/Install macOS High Sierra.app"` exists.

Step 2: Create a Bootable ISO
-----------------------------
Next, you need to create an ISO from the installer application that was downloaded in step 1.

Running the below commands will create an ISO on your desktop named `HighSierra.iso`:

```bash
hdiutil create -o /tmp/HighSierra.cdr -size 5200m -layout SPUD -fs HFS+J
hdiutil attach /tmp/HighSierra.cdr.dmg -noverify -mountpoint /Volumes/install_build
sudo /Applications/Install\ macOS\ High\ Sierra.app/Contents/Resources/createinstallmedia --volume /Volumes/install_build
mv /tmp/HighSierra.cdr.dmg ~/Desktop/InstallSystem.dmg
hdiutil detach /Volumes/Install\ macOS\ High\ Sierra
hdiutil convert ~/Desktop/InstallSystem.dmg -format UDTO -o ~/Desktop/HighSierra.iso
```

Step 3: Creating the Virtual Machine
------------------------------------
I experimented with a few different settings in regards to the CPU and RAM allocation. I didn't find a combination that didn't work, but create a VM with the following things in mind:

* Ensure the name of the VM is `MacOS` (ensure to keep the same casing)
* Ensure the type is `Mac OS X` and the version is `macOS 10.12 Sierra (64-bit)` (there is a High Sierra option too, but I chose Sierra by accident and it worked)
* Untick `Floppy` in `System > Motherboard > Boot Order`
* Use >= 4096 MB of memory in `System > Motherboard`
* Use >= 2 CPUs in `System > Processor`
* Use 128 MB of video memory in `Display > Screen`
* **Optionally** enable 3D acceleration in `Display > Screen`
* Remove the IDE device in `Storage > Storage Devices` and replace it with a SATA controller
* Add a new hard disk device under the SATA controller with >= 60 GB of space
* Ensure an optical drive is present under the SATA controller and mount the previously created ISO to it
* Untick the `Enable Audio` option under `Audio`

After creating the virtual machine with the above configuration, hit OK and exit the settings screen. Now, a number of extra options need to be set.

If you're on Windows, you'll need to `cd` into the appropriate directory under the VirtualBox installation path to run `VBoxManage`. For Linux users, this should be in your `PATH` variable already:

```bash
VBoxManage modifyvm "MacOS" --cpuidset 00000001 000106e5 00100800 0098e3fd bfebfbff
VBoxManage setextradata "MacOS" "VBoxInternal/Devices/efi/0/Config/DmiSystemProduct" "iMac11,3"
VBoxManage setextradata "MacOS" "VBoxInternal/Devices/efi/0/Config/DmiSystemVersion" "1.0"
VBoxManage setextradata "MacOS" "VBoxInternal/Devices/efi/0/Config/DmiBoardProduct" "Iloveapple"
VBoxManage setextradata "MacOS" "VBoxInternal/Devices/smc/0/Config/DeviceKey" "ourhardworkbythesewordsguardedpleasedontsteal(c)AppleComputerInc"
VBoxManage setextradata "MacOS" "VBoxInternal/Devices/smc/0/Config/GetKeyFromRealSMC" 1
```

After running the above commands, the VM should be ready to boot!

Step 4: Installation
--------------------
This is where near enough everything I read stopped, despite there being one more problem in the way - UEFI.

Boot into the VM, go into Disk Utility and erase the virtual disk that you added to the machine.

After erasing the disk, start the installation procedure. After a short amount of time, it will reboot the VM.

Once it reboots, it's going to boot back off the ISO again, once it's done this, just shutdown the VM and eject the disk [the ISO] and then start the VM again to boot from disk.

On the next boot, it *should* boot into the installer that was copied to disk, but instead, you will be presented with a UEFI shell like below:

![UEFI shell](/assets/images/installing-macos-high-sierra-in-virtualbox-5/uefi.png)

To continue the macOS installation, follow these steps:

1. Type `exit` and hit return
2. Select `Boot Maintenance Manager` and hit return
3. Select `Boot From File` and hit return
4. You will see two partitions, select the second partition and hit return
5. Select `macOS Install Data` and hit return
6. Select `Locked Files` and hit return
7. Select `Boot Files` and hit return
8. Select `boot.efi` and hit return

After following these steps, you will boot into the remainder of the macOS installation. From here, just follow the steps as per a regular macOS installation.

The next time you boot your virtual machine, you will **not** have to go through the UEFI shell; it should work without any further problems.

Step 5: Tweaking The Resolution
-------------------------------
As there is no VirtualBox additions for macOS, the screen resolution won't automatically change. If you know what resolution you wish to use, however, you can set it manually.

Ensure the virtual machine is powered off, and then run the following command; replacing `1920x1080` with whatever resolution you would like to use:

```bash
VBoxManage setextradata "MacOS" VBoxInternal2/EfiGraphicsResolution 1920x1080
```

After running the above command, the next time you boot the machine, it will use the resolution specified.

Now, you should have a fully working macOS virtual machine!

![macOS virtual machine](/assets/images/installing-macos-high-sierra-in-virtualbox-5/macos.png)

References
----------
The information found in this post was pieced together from the following sources:

* [https://tylermade.net/2017/10/05/how-to-create-a-bootable-iso-image-of-macos-10-13-high-sierra-installer/](https://tylermade.net/2017/10/05/how-to-create-a-bootable-iso-image-of-macos-10-13-high-sierra-installer/)
* [https://superuser.com/questions/1235970/stuck-on-uefi-interactive-shell-with-mac-os-x-high-sierra-vm](https://superuser.com/questions/1235970/stuck-on-uefi-interactive-shell-with-mac-os-x-high-sierra-vm)
* [https://techsviewer.com/install-macos-high-sierra-virtualbox-windows/](https://techsviewer.com/install-macos-high-sierra-virtualbox-windows/)
