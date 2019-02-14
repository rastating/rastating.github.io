---
layout: post
title: Fixing MySQL Failed Startup in Ubuntu Server 14.04
date: 2015-01-08 22:26:00 +0100
categories:
  - linux
tags:
  - ubuntu server
  - "14.04"
  - mysql
---
When installing Ubuntu Server 14.04, you have the ability to automatically install and configure a LAMP stack. However, doing so in the latest build (as of 08/01/2015), seems to cause an ownership issue on a few directories that will prevent you from being able to actually start the service.

To fix this, you simply need to change the ownership of three directories using the following commands:

```bash
sudo chown -R mysql:mysql /var/run/mysqld
sudo chown -R mysql:mysql /var/lib/mysql
sudo chown -R mysql:mysql /usr/share/mysql
```

If you have changed the user that MySQL runs as, it goes without saying you will have to change the username in the above commands.

After setting the correct ownership on the directories, startup MySQL again using:

```bash
sudo service mysql start
```
