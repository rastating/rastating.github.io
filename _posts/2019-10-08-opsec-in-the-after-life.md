---
layout: post
title: OPSEC in The After Life
date: 2019-10-08
categories:
  - opsec
  - security
tags:
  - opsec
  - security
image: /assets/images/2019-10-08-opsec-in-the-after-life/trust.gif
---
As people who follow me on social media will be aware, I was diagnosed with cancer earlier in the year. Thankfully, I have been officially cleared, however, throughout this event and some prior events, it led me to be concerned about what happens after I'm gone.

Typically, when we concern ourselves with post-life events, we're questioning who will inherit our possessions, funding for funerals etc. Traditionally, these have been the only real concerns we've had, but in a post-internet age, is this enough?

Over the last 18 months, I have began to find myself attempting to address the risk of the following in the event of death:

- Account takeovers
- Online material being lost
- Domain name misuse

Account Takeovers
-----------------
My biggest concern with account takeovers was predominantly surrounding the ability to impersonate me. If someone was able to gain access to my e-mail account, it would open up the possibility of other account takeovers, and more importantly - increased risk of someone e-mailing my contacts and impersonating me in order to say phish information from them or have them do things by abusing their trust in me.

Although my main concern is typically nullified by the news of someone's death spreading - this is not necessarily true of online communities. News isn't necessarily going to spread, and it is possible people will just be wondering where you're at.

![](/assets/images/2019-10-08-opsec-in-the-after-life/where-you-at.gif)

The first thing I was questioning in this regard was - what will happen when my e-mail account is marked as inactive? For some reason, there is not an overly straight answer from the main e-mail providers on this point.

I ran a poll on Twitter recently to see which providers people seem to be using. As I expected, the majority where rolling with Google Mail:

![](/assets/images/2019-10-08-opsec-in-the-after-life/twitter-poll.png)

Surprisingly, Proton was the second most popular by quite a big margin. I had expected it to be Outlook, however, with the poll targetting a security crowd, this may have made the results slightly more bias due to the target audience of Proton Mail.

Thankfully, for those people, Google and Proton Mail both have policies in place which prevent usernames being released back into the registration pool after they are deleted.

The [Google Help Center Article](https://support.google.com/mail/answer/61177?hl=en) states in the section `What happens when you delete your Gmail service` that:

> Your Gmail address can’t be used by anyone else in the future.

Likewise, [Proton Mail's KB Page](https://protonmail.com/support/knowledge-base/delete-account/) on account deletion has an explicit notice at the top of it, reading:

> Please note that once your account is deleted, there is no way to recover or recreate it. We do not recycle usernames, which means the same username will not be available in the future.

Microsoft [Outlook / Live / Hotmail] and Yahoo on the other hand... neither are very clear or have any clear policy on the matter. The only thing to go on with these providers is their past history; and both have recycled usernames in the past, as per the below articles:

- [Microsoft is quietly recycling Outlook email accounts](https://www.pcworld.com/article/2052586/microsoft-is-quietly-recycling-outlook-email-accounts.html)
- [Can Yahoo recycle your username -- and protect your data?](https://www.cnet.com/news/can-yahoo-recycle-your-username-and-protect-your-data/)

Although they claim to have some type of wizardry that will prevent people reusing usernames for malicious purposes, it seems hard to believe that this would be effective.

My takeaway from this, is that for now (as of October, 2019), it is best to start migrating your accounts to either Google Mail or Proton Mail, if you are currently using Microsoft or Yahoo services. If you're using another mail provider, try to find their policy on this matter to be sure the username is not going to be recycled at a later date.

Additionally, the risk of takeover by means of a credential dump becomes a greater one after death. Currently, you are likely subscribed to the likes of [Have I Been Pwned?](https://haveibeenpwned.com/) and are able to change your passwords if any are compromised; you definitely won't be changing any passwords after death though. It's for this reason that two factor authentication is *really* important.

Although it's good practice to protect accounts with 2FA anyway, it is even more important if you are trying to prepare for the worst case scenario in which you will no longer have control over the password.

Online Material Being Lost
--------------------------
This one was quite important to me and one which is pretty hard to reliably tackle. Pretty much all the work I do is free and open-source. I believe strongly in material and resources being available to people who cannot afford it. If information isn't freely available, we [the entire human race] are unable to evolve our knowledge and understanding of things and make things better. Thus, it was important to me that if anything were to happen to me, that the material I've produced wouldn't also disappear with me.

At the time, I was self hosting my blog and the documentation for several projects. Although the latter could be rebuilt from source code hosted on GitHub, if I were to die, my blog would disappear soon after if my bank account were to be closed.

As a short term solution, I contacted someone that I felt I could trust to help preserve the data and migrate it somewhere for me (if it came to it) and provided them with an export of all the data. This isn't going to be a solution for everyone, but if you can find someone you trust, this is a good idea until you can implement a longer term solution.

![](/assets/images/2019-10-08-opsec-in-the-after-life/trust.gif)

To try and mitigate this long term, I migrated my blog from my VPS to [GitHub Pages](https://pages.github.com/). This was thankfully made a bit easier by the fact that the blogging software I was using at the time (Ghost) uses markdown, which is also what Jekyll uses (used by GitHub Pages to generate the site).

Obviously, this is not going to be a perfect solution either. There is a risk of _any_ service provider going bust at some point. However, given the popularity of GitHub and recent acquisition by Microsoft, it seems likely they're going to be around for some time; so I landed with them.

A problem that came with doing this is that there were still links to the blog posts indexed on Google, and sitting around the web. This led to ultimately keeping a VPS running which will redirect traffic to the new permalinks at GitHub.

To do this, I have an nginx configuration file that will redirect all requests to the old permalinks using HTTP code 301 (a permanent redirect), as can be seen in the below snippet:

```nginx
server {
    listen 80;
    listen 443 ssl;
    server_name rastating.com;
    return 301 https://rastating.github.io$request_uri;

    ssl_certificate /etc/letsencrypt/live/rastating.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rastating.com/privkey.pem;
}

server {
    listen 80;
    listen 443 ssl;
    server_name www.rastating.com;
    return 301 https://rastating.github.io$request_uri;

    ssl_certificate /etc/letsencrypt/live/rastating.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/rastating.com/privkey.pem;
}
```

It's important to use a 301 to help search engines to take the appropriate action. The old address of my blog is no longer listed on Google, and has instead been replaced with the permalinks of the corresponding GitHub Pages blog. By doing this, come the time that the VPS expires, all indexed links should be posting to the new location.

Domain Name Misuse
------------------
There are a few things that fall into this category that had me concerned. The most obvious one will be e-mail accounts that you are using your own domain for. Should you pass away and the domain name lapse, it's up for grabs by anyone, and if you were hosting your own e-mails, this effectively leads to a takeover of your e-mail which will allow resetting passwords associating to any accounts linked to the e-mail.

As per the account takeover section, 2FA can help combat this (depending on the methods supported and the recovery options), but the best solution would be to simply not use your self hosted domains for accounts that could be sensitive at all. For example, using your self hosted e-mail to register for a CTF won't pose any risk post-death, but if you were to register for online banking using it - this could be something that could cause a lot of problems and potentially see people steal your money that is destined for family / friends / charity / the "get No Doubt to tour the UK again" pot. Ideally, you should stick to using e-mail accounts that will outlive you for sensitive stuff.

Another problem with your domain lapsing is the risk of it then being used for malicious purposes. In my case, hosting my blog and project pages on my domain meant someone could potentially take the domain over and then host malware from it in place of the legit projects (which obviously would be beyond undesirable). The resolution to this was what was described in the previous section, but I raise the point again in case this scenario is more applicable to you than the risk of information such as blog posts being lost.

If you have someone you can trust to keep a domain registered on your behalf, it may be possible to leave a small fund for them to keep it registered and pointing to free services. This solution could also pose a risk too though in the way of subdomain takeovers. If the person who manages it for you on your behalf after death is not actively checking the DNS records every now and then (or if they don't know how to), it is possible a subdomain takeover may creep into the picture at some point if a service you had a subdomain pointing to went bust and could lead to malicious content being hosted.

Ultimately, you should consider carefully what you are going to host from your own domains, what kind of impact it'd have if it was to suddenly go offline and what risks it poses.

The TLDR of My Rambling
-----------------------
There's no real "one size fits all" solution to trying to deal with this. These are just some of the things that I felt helped me get my loose ends together. Hopefully this information can help you if you're in a position to be thinking about this.

If you're not facing this problem at the moment, it is still worth considering your inevitable fate. It is difficult to get these things in order when you're staring it in the face vs. it being a distant eventuality.

If you've got a risk of this becoming reality fast, I sincerely hope you have the luck I did and that things work out. It's the most daunting thing to deal with and I sympathise with anyone trying to deal with it. Stay strong and keep fighting back.
