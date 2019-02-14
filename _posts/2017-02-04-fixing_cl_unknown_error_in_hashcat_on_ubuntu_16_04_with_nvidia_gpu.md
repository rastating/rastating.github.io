---
layout: post
title: Fixing CL_UNKNOWN_ERROR in Hashcat on Ubuntu 16.04 w/ NVIDIA GPU
date: 2017-02-04
categories:
  - ubuntu
  - linux
tags:
  - hashcat
  - nvidia
---
On a Ubuntu 16.04 box with the proprietary drivers from NVIDIA installed for my GTX 980ti, I was experiencing a problem preventing me from running Hashcat; which was this error message:

```
ERROR: clGetPlatformIDs() : -1001 : CL_UNKNOWN_ERROR
```

This error, [according to the FAQ](https://hashcat.net/wiki/doku.php?id=frequently_asked_questions#what_does_the_clgetplatformids_-1001_error_mean), is the result of a driver issue, usually. In my case, however, the problem was some missing dependencies.

After running `clinfo`, I could see that there were no devices being reported, but this was seemingly unrelated to the actual video card driver.

The solution, was to install two new packages, `nvidia-opencl-dev` and `nvidia-opencl-icd-370`. The second package will be named differently, based on the driver version you have installed. For example, if you had version 346.xx of the NVIDIA driver installed, you would install `nvidia-opencl-icd-346` instead.

If you're not sure which version of the driver you have installed, install the `nvidia-settings` package, and then run it from the terminal, and look at the value next to "NVIDIA Driver Version" in the screen that appears:

![](/assets/images/fixing_cl_unknown_error_in_hashcat_on_ubuntu_16_04_with_nvidia_gpu/Screenshot-from-2017-02-04-00-33-18.png)

After following these steps, you should now see the GPU listed by `clinfo` and be able to start using Hashcat.
