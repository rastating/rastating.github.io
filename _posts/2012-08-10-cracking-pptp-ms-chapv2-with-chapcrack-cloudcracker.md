---
layout: single
title: "Cracking PPTP / MS-CHAPv2 with Chapcrack & CloudCracker"
date: 2012-08-10 21:54:00 +0100
categories:
  - security
tags:
  - backtrack
  - chapcrack
  - cloudcracker
  - des
  - ms-chapv2
  - pptp
  - vpn
---
After a long trip to the United States to return to Defcon, I am back and thought I'd share some information on a talk I checked out by [Moxie Marlinspike](https://twitter.com/moxie) which was of particular interest to me as this year I decided to use a PPTP tunnel instead of an SSH tunnel; not the best of ideas it turns out!

## What is Chapcrack and CloudCracker?
[Chapcrack](https://github.com/moxie0/chapcrack) is a tool you can use to take network packet captures and extract from them a string which can be submitted to [CloudCracker](http://www.cloudcracker.com/) which can finish a brute force against it in a worst case scenario of 24 hours and return to you via e-mail the cracked key.

CloudCracker does come at a cost (that being $200 per key), however if you really need to crack the key, the money isn't much to part with when you take into consideration the amount of time that will be saved if a strong key has been chosen.

## Some Background on the Protocol and its Flaws

*Just want to start off pointing out this research of the protocol is not my own, I am not taking credit for it, it was done by Moxie; I am just reposting it for the sake of keeping this post as informative as possible!*

Let's take a look at the protocol itself, in order to see what we're dealing with:

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/protocol_frame1_e1344632468334.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/protocol_frame1_e1344632468334.png)

At first glance, one is initially struck by the unnecessary complexity of the protocol. It almost feels like the digital equivalent of hand-waving — as if throwing in one more hash, random nonce, or unusual digest construction will somehow dazzle any would-be adversaries into submission. The literal strings "Pad to make it do more than one iteration" and "Magic server to client signing constant" are particularly amusing.

If we look carefully, however, there is really only one unknown in the entire protocol — the MD4 hash of the user's passphrase, which is used to construct three separate DES keys. Every other element of the protocol is either sent in the clear, or can be easily derived from something sent in the clear:

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/protocol_highlighted_frame1_e1344632704875.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/protocol_highlighted_frame1_e1344632704875.png)

Given that everything else is known, we can try ignoring everything but the core unknown, and seeing if there are any possibilities available to us:

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/protocol_core_highlighted_frame1_e1344633500703.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/protocol_core_highlighted_frame1_e1344633500703.png)

We have an unknown password, an unknown MD4 hash of that password, a known plaintext, and a known ciphertext. Looking back at the larger scope, we can see that the MD4 hash of the user's password serves as a password-equivalent — meaning that the MD4 hash of the user's password is enough to authenticate as them, as well as to decrypt any of their traffic. So our objective is to recover the MD4 hash of the user’s password.

Typically, given a packet capture, this is where a network adversary would attempt to employ a dictionary attack. Using a tool such as [asleap](http://www.willhackforsushi.com/Asleap.html), it's possible to rapidly attempt a series of password guesses offline. The attacker can simply calculate MD4(password_guess), split that hash up into three DES keys, encrypt the known plaintext three times, and see if the concatenated output from those DES operations matches the known ciphertext.

The problem with this approach is that it won't give the attacker a 100% success rate, and relies on the user's propensity for selecting a predictable password. In the case of the riseup.net PPTP VPN service, for instance, the attacker would need to attempt guesses across the full 96 key character set for all 21 characters of the generated password. That's a total complexity of 96<sup>21</sup> — slightly larger than 2<sup>138</sup>, or what you could think of as a 138 bit key.

In a situation with an unbounded password length across a large character set, it would make more sense to brute force the output of the MD4 hash directly. But that's still 128bits, making the total keyspace for a brute force approach on that value 2<sup>128</sup> — which will likely be forever computationally infeasible.

The hash we're after, however, is used as the key material for three DES operations. DES keys are 7 bytes long, so each DES operation uses a 7 byte chunk of the MD4 hash output. This gives us an opportunity for a classic divide and conquer attack. Instead of brute forcing the MD4 hash output directly (a complexity of 2<sup>128</sup>), we can incrementally brute force 7 bytes of it at a time.

Since there are three DES operations, and each DES operation is completely independent of the others, that gives us an additive complexity of 2<sup>56</sup> + 2<sup>56</sup> + 2<sup>56</sup>, a total keyspace of 2<sup>57.59</sup>

This is certainly better than 2<sup>138</sup> or 2<sup>128</sup>, but still quite a large number. There's something wrong with our calculations though. We need three DES keys, each 7 bytes long, for a total of 21 bytes:

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/keys_frame1_e1344634103227.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/keys_frame1_e1344634103227.png)

Those keys are drawn from the output of MD4(password), though, which is only 16 bytes:

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/keys_hash_frame1_e1344634185156.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/keys_hash_frame1_e1344634185156.png)

We're missing five bytes of key material for the third DES key. Microsoft's solution was to simply pad those last five bytes out as zero, effectively making the third DES key two bytes long:

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/keys_padding_frame1_e1344634335619.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/keys_padding_frame1_e1344634335619.png)

Since the third DES key is only two bytes long, a keyspace of 2<sup>16</sup>, we can immediately see the effectiveness of divide-and-conquer approach by brute forcing the third key in a matter of seconds, giving us the last two bytes of the MD4 hash. We're left trying to find the remaining 14 bytes of the MD4 hash, but can divide-and-conquer those in two 7 byte chunks, for a total complexity of 2<sup>57</sup>.

Again, still a big number, but considerably better. We're left with, essentially, this core problem:

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/protocol_core_reduced_frame1_e1344634500121.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/protocol_core_reduced_frame1_e1344634500121.png)

The next interesting thing about the remaining unknowns is that both of the remaining DES operations are over the *same* plaintext, only with different keys. The naive approach to cracking these DES operations would look like:

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/code_naieve_frame1_e1344634640493.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/code_naieve_frame1_e1344634640493.png)

...iterate over every key in the keyspace, and use each key to encrypt our known plaintext and compare it to our first known ciphertext. When we find a match, we start over and iterate through every key in the keyspace, encrypt our known plaintext, and compare it to our second known ciphertext.

The expensive part of these loops are the DES operations. But since it's the same plaintext for both loops, we can consolidate them into a single iteration through the keyspace, with one encrypt for each key, and two compares:

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/code_consolidated_frame1_e1344634964853.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/code_consolidated_frame1_e1344634964853.png)

This brings us down to a total complexity of 2<sup>56</sup>!

This means that, effectively, the security of MS-CHAPv2 can be reduced to the strength of a singleDES encryption.

## So Let's Crack this Key Already!
The first thing you're going to have to do is download the latest copy of the chapcrack source files from [Here](https://github.com/moxie0/chapcrack/zipball/master) or visit the [Github Page](https://github.com/moxie0/chapcrack) if you need a specific revision (I am using commit b2f5cf8 as of the time of writing this).

As this is a [Python](http://www.python.org/) program, it goes without saying you'll have to install Python! I won't go into this here as there are plenty of tutorials around the web on setting it up in the environment of your choice.

Before you install chapcrack you may require a few prerequisites first. I installed chapcrack on a fresh install of [BackTrack5](http://www.backtrack-linux.org/), and these were the steps I had to take:

### Installing Passlib
> Passlib is a password hashing library for Python 2 & 3, which provides cross-platform implementations of over 30 password hashing algorithms, as well as a framework for managing existing password hashes. It's designed to be useful for a wide range of tasks, from verifying a hash found in /etc/shadow, to providing full-strength password hashing for multi-user applications.

To install passlib, head over to the [Downloads Page](http://pypi.python.org/pypi/passlib/#downloads) and grab the latest version, extract it and then open a terminal in the same directory and run the following command:

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/python_setup__py__install.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/python_setup__py__install.png)

Once it's done its thing the installation has finished and we can move on!

### Installing python-m2crypto
> M2Crypto is the most complete OpenSSL wrapper for Python. M2Crypto makes it relatively easy to add cryptographic support and security to your Python applications.

Again, just one small command to run and we're done!

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/apt_get_install_python_m2crypto.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/apt_get_install_python_m2crypto.png)

Now that we have the prerequisites we can install chapcrack! Change your working directory in your terminal to the directory in which you extracted the chapcrack ZIP file and then run the following command to install chapcrack:

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/python_setup__py__install_chapcrack.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/python_setup__py__install_chapcrack.png)

Now that we have chapcrack installed we can give it a test whirl!

I'm not going to explain here how to capture packets over a network, as again there are lots of guides and information on this available and I'd just be reiterating them, and chances are if you're reading this you probably know how to anyway. If you do need a push in the right direction however, have a look around for some guides on how to use [Wireshark](http://www.wireshark.org/).

If you don't have a capture file already that contains an MS-CHAPv2 handshake, throw one together or alternatively you can use the sample file (pptp.cap) in the tests directory of the chapcrack download (see below) like I will be doing to demonstrate.

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/ls_l_tests_.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/ls_l_tests_.png)

To use chapcrack we just have to execute it with the parse -i command, passing through to it the path to our capture file. It should finish relatively quickly and give you back a few bits of data; the one we are interested in is the CloudCracker Submission.

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/chapcrack.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/chapcrack.png)

Copy and paste the CloudCracker Submission string into a file and then head over to http://www.cloudcracker.com/.

Choose the MS-CHAPv2 option on the first page you arrive at, and then select the file you just created as the Chapcrack Output file to submit. From here just follow the instructions on the website, and when the crack is finished you'll get an e-mail with the results; it's that simple!

[![](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/cloudcracker.png)](/assets/images/cracking-pptp-ms-chapv2-with-chapcrack-cloudcracker/cloudcracker.png)
