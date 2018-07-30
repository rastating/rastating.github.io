---
layout: single
title: Setting Default Audio Device in Ubuntu 18.04
excerpt: After upgrading to Ubuntu 18.04, I ran into an issue (or possibly a feature) causing the active audio input / output devices to revert to a device of the system's choosing after a power cycle.
date: 2018-05-06 13:32:00 +0100
categories:
  - ubuntu
  - ubuntu 18.04
  - pulse audio
  - bionic beaver
---
After upgrading to Ubuntu 18.04, I ran into an issue (or possibly a _feature_) causing the active audio input / output devices to revert to a device of the system's choosing after a power cycle.

Installing the [Sound Input & Output Device Chooser](https://extensions.gnome.org/extension/906/sound-output-device-chooser/) GNOME shell extension mitigated this to an extent, but was adding the need to manually change devices after every reboot still; which quickly became tedious.

Thankfully, the `pactl` application provides a way to script the changing of devices. The first thing to understand about this application, are the two terminologies used to describe devices. A `sink` is an output device (i.e. your speakers), and a `source` is an input device (i.e. your microphone).

## Using pactl to Switch Devices

To get a list of all the output devices, open a terminal and run `pactl list short sinks`; this should provide you with a list of output devices.

```
0	alsa_output.pci-0000_02_00.1.hdmi-stereo	module-alsa-card.c	s16le 2ch 44100Hz	SUSPENDED
1	alsa_output.usb-Blue_Microphones_Yeti_Stereo_Microphone_REV8-00.analog-stereo	module-alsa-card.c	s16le 2ch 44100Hz	SUSPENDED
2	alsa_output.usb-FiiO_DigiHug_USB_Audio-01.analog-stereo	module-alsa-card.c	s16le 2ch 44100Hz	SUSPENDED
3	alsa_output.pci-0000_00_1f.3.analog-stereo	module-alsa-card.c	s16le 2ch 48000Hz	RUNNING
```

For reference, the devices listed in the above output relate to the devices that can be seen in the settings screen below:

![](/assets/images/setting-default-audio-device-in-ubuntu-18-04/output_devices.png)

For my setup, the device I want to be the default output is the one that can be seen highlighted in the above screenshot - `Line Out - Built-in Audio`.

To switch to this device, using `pactl`, the device must first be identified from the list of device names previously acquired. In this case, the device name is `alsa_output.pci-0000_00_1f.3.analog-stereo`.

With the name known, `pactl` can be executed using the `set-default-sink` option, to switch the output device. In the above example, the command that would be executed is:

```
pactl set-default-sink 'alsa_output.pci-0000_00_1f.3.analog-stereo'
```

Switching the input device consists of the same process, but replacing any instance of `sink` with `source`. For example, instead of running `pactl list short sinks`, one would run `pactl list short sources`.

Below are the steps taken to set the default input device to the Yeti microphone.

```
$ pactl list short sources
0	alsa_output.pci-0000_02_00.1.hdmi-stereo.monitor	module-alsa-card.c	s16le 2ch 44100Hz	SUSPENDED
1	alsa_input.usb-AVerMedia_Technologies__Inc._Live_Gamer_Portable_2_5202050100060-03.analog-stereo	module-alsa-card.c	s16le 2ch 48000Hz	SUSPENDED
2	alsa_output.usb-Blue_Microphones_Yeti_Stereo_Microphone_REV8-00.analog-stereo.monitor	module-alsa-card.c	s16le 2ch 44100Hz	SUSPENDED
3	alsa_input.usb-Blue_Microphones_Yeti_Stereo_Microphone_REV8-00.analog-stereo	module-alsa-card.c	s16le 2ch 44100Hz	RUNNING
4	alsa_output.usb-FiiO_DigiHug_USB_Audio-01.analog-stereo.monitor	module-alsa-card.c	s16le 2ch 44100Hz	SUSPENDED
5	alsa_input.usb-FiiO_DigiHug_USB_Audio-01.analog-stereo	module-alsa-card.c	s16le 2ch 44100Hz	SUSPENDED
6	alsa_output.pci-0000_00_1f.3.analog-stereo.monitor	module-alsa-card.c	s16le 2ch 48000Hz	SUSPENDED
7	alsa_input.pci-0000_00_1f.3.analog-stereo	module-alsa-card.c	s16le 2ch 44100Hz	SUSPENDED

$ pactl set-default-source 'alsa_input.usb-Blue_Microphones_Yeti_Stereo_Microphone_REV8-00.analog-stereo'
```

![](/assets/images/setting-default-audio-device-in-ubuntu-18-04/input_devices.png)

## Automating The Switch
Now that the device names are known, and they have been verified to work by using the `pactl` application. They can be used in conjunction with the default Pulse configuration file.

Open `/etc/pulse/default.pa` and scroll to the bottom of the file, where two lines starting with `set-` will be commented out.

Uncomment these lines and replace the words `input` and `output` with the number of the sink / source that you want to be the default.

In my case, the `alsa_input.usb-Blue_Microphones_Yeti_Stereo_Microphone_REV8-00.analog-stereo` and `alsa_output.pci-0000_00_1f.3.analog-stereo` devices were both `3`, so the settings I used were:

```
### Make some devices default
set-default-sink 3
set-default-source 3
```

After doing this, delete the `~/.config/pulse` directory, and then reboot the system. Once the system comes back up, the appropriate devices should now be set as the defaults.

The downside to this approach, will be that if the device list changes, the indexes of the devices may also change, meaning this process may need to be repeated; but it resolves the immediate issue, when there are multiple audio devices connected on a permanent basis.
