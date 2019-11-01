---
layout: post
title: Release of Chweb
date: 2019-11-01
categories:
  - development
  - websec
  - security
tags:
  - chweb
image: /assets/images/2019-11-01-release-of-chweb/chweb.png
---

I have been working on this system for quite a while now and ramped up development time on it a lot the last month or two. Although there are a lot of content filtering systems out there, none really worked in the way I wanted them too; enter chweb. Chweb is not really targeting the use case that a lot of systems do. It works on the presumption of full trust of the end user and they want to opt in, rather than zero trust (e.g. a school environment where the users would typically try to bypass the system).

The best way to describe its use case is probably to explain my own (after all, it was what prompted its development!). Over the last 12 months, I have been helping someone who is suffering from dementia. Although there are lots of terrible things that this brings to the table for people who suffer from it, there is a huge issue that doesn't get spoken about much - the impact on their security.

People suffering with dementia will typically become confused very easily and can be led astray easily. Combine this with them looking at websites with user generated content (YouTube, Twitter, et al.) and this can increase their chances of being victims of phishing campaigns.

So, what can you do? Well, in my case, the person in question only visits a handful of websites, mostly YouTube. Anything outside a certain set of websites, and chances are they didn't mean to get there and could be being led to a scam. So, my ideal solution was to create a white list of websites available to them.

Although there are DNS services to do this, it would mean a lot of maintenance on my part to go that route as although they typically only browse the web, if they did decide to take up using any other Internet enabled software (or need to contact servers for software updates etc.) it would mean maintaining a list of domain names that would be resolved; which could get troublesome. Setting up a proxy in the middle also felt very heavy handed and would require more hardware.

All of this ultimately led me to go hunting for browser extensions that may do what I want, and sure enough, I found one that would let me create white lists! This also didn't fully meet my requirements though. As the user has multiple devices, it would make it difficult to maintain these lists on each device. Ideally, I'd be able to manage them in a central location, with the devices pulling the latest rule sets down.

A month or two of development later, and here we are! Chweb consists of a server package and a browser extension (currently only Chrome is supported, but I'm going to work on versions for other browsers too). The server runs on Node.js and MongoDB and is pretty lightweight - it shouldn't take much to run it. The general flow is as follows:

1. User loads browser, the extension requests the latest configuration from the server (this includes the ruleset and some misc settings)

2. A hook is setup in the user's browser to check the requests being made (works with both HTTP and HTTPS requests). The URL is then checked against the ruleset to see if a rule is defined for the URL

3. If the URL matches a rule, it will either be blocked or allowed to render appropriately

4. If the page is allowed, any resources the page requests will NOT follow this ruleset. This means if you allow, for example, YouTube, you'd not have to also allow all their individual CDNs in order for thumbnails and videos to load properly.

5. If a rule was not found, the default action (configurable on the server) will be taken instead

6. If the collection of analytics is enabled on the server, a request to the API will be sent to log the action that was taken against the requested host name (emphasis on host, the URL of the resource being requested is not sent)

The benefits this brings over the solutions I decided against is:

1. Easy handling of HTTPS traffic without installing and configuring a proxy and doing packet inspection

2. Easy maintenance across multiple hosts (particularly useful if you aren't able to gain remote access to the user's machine or make a trip to see them)

3. Greater control over exactly what can be allowed or rejected

4. Analytical data to allow for a review from time to time to see if there is legitimate looking requests that should be updated to be allowed through the filter

As mentioned in the opening sentence of this post, this is in no way appropriate if the end user is not wanting their content filtered, as they could simply disable the extension or just use a portable browser. It does, however, provide [what I believe to be] a good solution for when there is a need to filter what comes through for someone's own safety.

Also, it has pretty graphs!

![](/assets/images/2019-11-01-release-of-chweb/chweb.png)

If you'd like to check it out, it is now available on GitHub at the following URLs:

* Back-end server: [https://github.com/rastating/chweb-server](https://github.com/rastating/chweb-server)
* Chrome extension: [https://github.com/rastating/chweb-chrome](https://github.com/rastating/chweb-chrome)

Currently, the Chrome extension is still pending approval by Google, so it must be installed manually in developer mode by running `yarn build` in the source code directory and then loading an unpacked extension in Chrome using the `build` directory. Inconvenient, but if you want to try it out before it reaches the Google Store, that's how it is done!

As the goal of this system is to help keep people secure, it's safe to say the security of the system is of paramount importance. Although I have tested this extensively during development, it's entirely possible there are holes that I have been blinded by from a developers' standpoint. If you want to try hacking on it and find anything, if you could open an issue on the appropriate GitHub repository, it'd be much appreciated!
