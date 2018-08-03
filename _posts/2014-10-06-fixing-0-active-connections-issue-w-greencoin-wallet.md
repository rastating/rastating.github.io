---
layout: single
title: Fixing "0 Active Connections" Issue w/ GreenCoin Wallet
date: 2014-10-06 20:04:00 +0100
categories:
  - crypto
tags:
  - greencoin
---
Recently, the mining pool I use ([SimpleMulti](http://simplemulti.com/)) added [GreenCoin](https://bitcointalk.org/index.php?topic=636548.0) into their merge mining pool.

I convert all of my merged mined coins into Dogecoin, but at the moment GreenCoin isn't automatically exchangeable into Dogecoin on the pool, so I decided to grab the wallet and just cash them out. Unfortunately though, I was greeted with an inability to connect to any peers on the network.

As it turns out, the reason for this is that you have to create a config file, or at least at this stage of its development. The settings for this are actually posted in [the thread over at bitcointalk.org](https://bitcointalk.org/index.php?topic=636548.0) however there's no guidance as to where it should go, for those of us a bit less experienced.

Anyway, you need to navigate to the folder in which all your data is stored, such as the block chain. In Windows, this by default resides in the app data folder, which you can access by typing `%appdata%` in an Explorer window.

Inside the folder for GreenCoin, create a new file named `greencoin.conf` and add the following contents to it:

```ini
rpcuser=username
rpcpassword=password
rpcallowip=127.0.0.1
rpcport=21036
server=1
daemon=1
listen=1
addnode=168.63.241.137
addnode=76.120.208.5
addnode=109.155.62.64
addnode=178.62.224.174
addnode=211.99.134.28
```

Save the file, restart the GreenCoin wallet and you should now be able to connect to the network.

Happy mining :)
