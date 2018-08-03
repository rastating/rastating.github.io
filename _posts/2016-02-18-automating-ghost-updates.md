---
layout: single
title: Automating Ghost Updates
date: 2016-02-18
categories:
  - linux
tags:
  - ghost
  - automatic update
  - push notification
  - ifttt
excerpt: I've been using the [Ghost](https://ghost.org/) platform for some time now and it is without doubt my favourite. One thing, however, that has been some what of a pain, is the lack of automation in terms of updates.
---
**N.B With the release of Ghost 1.x comes a new CLI utility which can handle automated upgrades. The below should only be used on the LTS version (i.e. < v1.0).**

I've been using the [Ghost](https://ghost.org/) platform for some time now and it is without doubt my favourite. One thing, however, that has been some what of a pain, is the lack of automation in terms of updates.

To overcome this, I've created two small utilities to help keep up to date.

## Notifications of New Releases
The first is an IFTTT recipe which will monitor the [Ghost GitHub Repository](https://github.com/TryGhost/Ghost) for new releases and send me a push notification. This recipe can easily be modified to e-mail you or whatever other method of communication you'd prefer.

You can find the IFTTT recipe here: [https://ifttt.com/recipes/319718-send-a-pushover-notification-when-a-new-version-of-ghost-is-released-on-github](https://ifttt.com/recipes/319718-send-a-pushover-notification-when-a-new-version-of-ghost-is-released-on-github)

## Update Script
The second utility, is a small bash script that I coined together from [These Manual Instructions on Updating](http://support.ghost.org/how-to-upgrade/) which will:

1. Stop the ghost service
2. Create a backup in the `var/www/backups` folder (I'd **highly** recommend changing this if you expose your entire `www` folder publicly, or if you simply would rather it be somewhere else)
3. Download the latest version and extract it
4. Update all dependencies via NPM
5. Cleanup the temporary files and start the ghost service

The script can be found below:

```bash
#!/bin/bash
today=`date '+%Y-%m-%d'`;
service ghost stop
tar -zcvf "/var/www/backups/ghost_backup_$today.tar.gz" /var/www/ghost
wget https://ghost.org/zip/ghost-latest.zip -O /tmp/ghost-latest.zip
unzip /tmp/ghost-latest.zip -d /tmp/ghost-temp
rm -rf /var/www/ghost/core
cp -R /tmp/ghost-temp/core /var/www/ghost
cp /tmp/ghost-temp/index.js /var/www/ghost/index.js
cp /tmp/ghost-temp/*.json /var/www/ghost
chown -R ghost:ghost /var/www/ghost
cd /var/www/ghost
npm install --production
rm -rf /tmp/ghost-temp
service ghost start
rm /tmp/ghost-latest.zip
```
