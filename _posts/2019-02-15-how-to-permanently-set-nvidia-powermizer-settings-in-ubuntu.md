---
layout: post
title: How to Permanently Set NVIDIA PowerMizer Settings in Ubuntu
date: 2019-02-15
categories:
  - ubuntu
  - linux
tags:
  - ubuntu 18.04
  - nvidia
  - powermizer
  - bionic beaver
image: /assets/images/how-to-permanantly-set-nvidia-powermizer-settings-in-ubuntu/control-panel.png
---
When setting the preferred power mode in the PowerMizer settings of the NVIDIA control panel in Ubuntu, the setting is reset after a reboot of the system. As the default setting forces the GPU to use an adaptive power setting, this can result in decreased performance until such time as setting PowerMizer to prefer maximum performance again.

Although the NVIDIA control panel provides no means of persisting these settings, there is a CLI utility that can help automate the process. Running the `nvidia-settings` binary with the `-q` option will output all the current settings. Filtering the output to those related to PowerMizer reveals the `GPUPowerMizerMode` setting, which when unaltered is set to `0`:

```shell_session
$ nvidia-settings -q all | grep -C 10 -i powermizer
  Attribute 'GPUCurrentPerfLevel' (rastating-PC:1[gpu:0]): 3.
    'GPUCurrentPerfLevel' is an integer attribute.
    'GPUCurrentPerfLevel' is a read-only attribute.
    'GPUCurrentPerfLevel' can use the following target types: X Screen, GPU.

  Attribute 'GPUAdaptiveClockState' (rastating-PC:1[gpu:0]): 1.
    'GPUAdaptiveClockState' is a boolean attribute; valid values are: 1 (on/true) and 0 (off/false).
    'GPUAdaptiveClockState' is a read-only attribute.
    'GPUAdaptiveClockState' can use the following target types: X Screen, GPU.

  Attribute 'GPUPowerMizerMode' (rastating-PC:1[gpu:0]): 0.
    Valid values for 'GPUPowerMizerMode' are: 0, 1 and 2.
    'GPUPowerMizerMode' can use the following target types: GPU.

  Attribute 'GPUPowerMizerDefaultMode' (rastating-PC:1[gpu:0]): 0.
    'GPUPowerMizerDefaultMode' is an integer attribute.
    'GPUPowerMizerDefaultMode' is a read-only attribute.
    'GPUPowerMizerDefaultMode' can use the following target types: GPU.

  Attribute 'ECCSupported' (rastating-PC:1[gpu:0]): 0.
    'ECCSupported' is a boolean attribute; valid values are: 1 (on/true) and 0 (off/false).
    'ECCSupported' is a read-only attribute.
    'ECCSupported' can use the following target types: GPU.

  Attribute 'GPULogoBrightness' (rastating-PC:1[gpu:0]): 100.
    The valid values for 'GPULogoBrightness' are in the range 0 - 100 (inclusive).
    'GPULogoBrightness' can use the following target types: GPU.
```

After setting the preferred mode to "Prefer Maximum Performance", the control panel and terminal output now looked as follows:

![](/assets/images/how-to-permanantly-set-nvidia-powermizer-settings-in-ubuntu/control-panel.png)

```shell_session
$ nvidia-settings -q GpuPowerMizerMode

  Attribute 'GPUPowerMizerMode' (rastating-PC:1[gpu:0]): 1.
    Valid values for 'GPUPowerMizerMode' are: 0, 1 and 2.
    'GPUPowerMizerMode' can use the following target types: GPU.
```

As can be seen in the above output, the `GPUPowerMizerMode` is now set to a value of `1`.

In addition to reading current values, `nvidia-settings` can also be used to alter settings. Before using this, we must take note of the GPU index that needs to be changed. In most instances, this will be `0`. The index can be identified by looking at the number following `gpu:` in the attribute line of the output.

Using this information, we can use the `-a` option to set the value of `GpuPowerMizerMode` to `1` and verify it has been changed using the `-q` option:

```shell_session
$ nvidia-settings -a "[gpu:0]/GpuPowerMizerMode=1"

  Attribute 'GPUPowerMizerMode' (rastating-PC:1[gpu:0]) assigned value 1.

$ nvidia-settings -q GpuPowerMizerMode

  Attribute 'GPUPowerMizerMode' (rastating-PC:1[gpu:0]): 1.
    Valid values for 'GPUPowerMizerMode' are: 0, 1 and 2.
    'GPUPowerMizerMode' can use the following target types: GPU.
```

There are multiple ways to automate the execution of this command. Personally, I have chosen to add it as a startup application. To do this, run "Startup Applications Preferences" from the dock and then click the "Add" button. In the dialog that is displayed, add the previously used command to set the preferred mode, like this:

![](/assets/images/how-to-permanantly-set-nvidia-powermizer-settings-in-ubuntu/startup.png)

After adding this as a startup program, the setting will be automatically adjusted every time you login and the GPU will always prefer maximum performance.
