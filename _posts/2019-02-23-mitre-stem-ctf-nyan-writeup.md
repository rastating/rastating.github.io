---
layout: post
title: "MITRE STEM CTF: Nyanyanyan Writeup"
date: 2019-02-23
categories:
  - ctf
  - writeups
tags:
  - mitre
  - ctf
  - nyanyanyan
image: /assets/images/2019-02-23-mitre-stem-ctf-nyan-writeup/nyan.png
---

Upon connecting to the provided server via SSH, a [Nyan Cat](https://www.youtube.com/watch?v=wZZ7oFKsKzY) loop is instantly launched. There appears to be no way to escape this.

Specifying a command to be executed upon connecting via SSH results in a stream of whitespace being sent vs. the expected output.

Upon examining the animation, I was able to see some alphanumeric characters in white against the bright blue background. Within these characters, was the flag.

As the characters were too fast to be noted manually, it was necessary to redirect the outpuit of the SSH session to a file (`ssh ctf@ip > nyan.txt`). After doing this and inspecting the file, there is a significant amount of junk data. As the flag will only contain alphanumeric and special characters, running the following command will show only the individual characters that were displayed in white, and concatenate them together:

```shell_session
grep -oP "[a-zA-Z0-9.£$%^&*()_\-+=#~'@;:?><,.{}]" nyan.txt | tr '\n' ' '
```

Upon doing this, it is possible to see the flag within the output:

![](/assets/images/2019-02-23-mitre-stem-ctf-nyan-writeup/screenshot.png)
