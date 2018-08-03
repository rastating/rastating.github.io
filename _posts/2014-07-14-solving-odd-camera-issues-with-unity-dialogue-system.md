---
layout: single
title: "Solving Odd Camera Issues with Unity Dialogue System"
date: 2014-07-14 19:39:00 +0100
categories:
  - programming
tags:
  - unity
  - dialogue
  - camera
  - background colour
---
Earlier today, I purchased [Dialogue System for Unity](https://www.assetstore.unity3d.com/en/#!/content/11672) for a project I am working on that will require interactive dialogues as well as bark dialogues (dialogues that are not interactive, but occur on a trigger; such as you walking by someone).

I began by reading through [The Documentation](http://www.pixelcrushers.com/dialogue_system/manual/html/index.html) and setting up some simple dialogues and managed to get the triggers to work and the conversation flows to work correctly, but for some reason I kept running into a problem in which the camera seemed to be inverted on the Z axis and the background colour of the main camera was being shown as can be seen in the below screenshot:

![](/assets/images/solving-odd-camera-issues-with-unity-dialogue-system/dialogue_system_camera_showing_background_colour.jpg)

Unfortunately, Googling didn't reveal any occurrence of this and I couldn't find anything in the documentation to do with it either. As it turns out, it may have been something a bit more obvious to someone who is more experienced with the system that is easily fixed. The solution was to simply remove the value in the "Default Sequence" property found under the "Camera Settings" drop down in the Dialogue System Controller properties.

![](/assets/images/solving-odd-camera-issues-with-unity-dialogue-system/default_sequence_value.jpg)

By default, this value is set to `Camera(Closeup); required Camera(Closeup,listener)@{{end}}`, as can be seen above, which seems to be what was causing odd camera behaviour. If like me you aren't interested [yet] in interacting with the camera just empty this property and it should be fine.

On a side note, I highly recommend purchasing Dialogue System if you're in need of adding dialogues to your game. Although I haven't spent much time with it, I can safely say it is very well polished and has a very easy to use yet flexible work flow.
