---
layout: post
title: "Adding Springs to 2D Platformers in Unity"
date: 2014-06-27 17:43:00 +0100
categories:
  - programming
tags:
  - unity
  - spring
  - prefab
  - jump
  - spring board
---
A rather common component found in a lot of platformer games is some form of spring board that when jumped from ejects the player with a higher velocity than if they jumped from any other surface.

This guide will show you how to utilise a spring prefab I have created (as can be seen in the picture below) for an on going project of my own which needed the use of spring boards.

![](/assets/images/adding-springs-to-2d-platformers-in-unity/unity_spring_platform.png)

To view an example of this component in action, [Click Here](https://rastating.github.io/unity-spring-demo/)! Use the arrow keys to move the player and press the space bar to jump.

### Prerequisites
In order to use this prefab, your user controlled player will have to have a 2D rigidbody attached to it as the prefab assumes you are using the physics engine to control your character's movement.

### Using the Prefab
First of all, download [This Unity Package](https://mega.nz/#!CUViRLSQ!qMiQ-AdZJgHlUKlbzXNXPdJeYHqgBml06zANfiGlyf8)

Once downloaded, import it into your project by opening the Assets menu, clicking "Import Package" and then choosing "Custom Package..." and selecting the package you just downloaded.

![](/assets/images/adding-springs-to-2d-platformers-in-unity/unity_import_package.png)

Once selected, you will be prompted to confirm which items to import. Ensure you have all the items in the package selected and then click the import button in the bottom right hand corner of the dialog.

![](/assets/images/adding-springs-to-2d-platformers-in-unity/unity_import_package_contents.png)

Once the package has been imported, simply drag the spring prefab into your scene and it's almost ready to use; we just have two things to configure in order to get up and running.

The first thing we must set is the layer mask to identify the player object. The spring prefab works on the assumption your user controlled player will always be on a unique layer; in my case I have a layer called "Player" which the player object will be on.

To do this, simply click the spring in your scene and in the property inspector set the "Player Layer Mask" property to the correct layer.

![](/assets/images/adding-springs-to-2d-platformers-in-unity/unity_spring_layer_mask.png)

That's the first of two configurations that need to be made; the next one is a slight code change. Open up the Spring script, you can do this by either double clicking the Spring script in the property inspector, or by double clicking it in the assets window.

In the script, we have a property named `JumpInputActive`. We simply need to change this property to return true if the input required for the player to jump is active. In my case, my player jumps if the space bar is pressed, so I simply return true if the space bar is pressed; if your player also jumps when pressing space, there is no need to change this.

```csharp
private bool JumpInputActive {
  get {
    return Input.GetKeyDown(KeyCode.Space);
  }
}
```

Now, whenever your player is on top of the spring, it will push down, and then will spring the player into the air if they jump; again, [see the online demo](https://rastating.github.io/unity-spring-demo/) for an example of this in action. You can tweak the amount of force that the spring should apply to the player's velocity by altering the spring force property in the inspector.

![](/assets/images/adding-springs-to-2d-platformers-in-unity/unity_spring_force.png)

###Sprite Sheet Vectors
The original vector for the sprite was created by [Kenney Vieugels](http://www.kenney.nl/)
and I modified it to have the various frames, as can be seen below. If you're in need of some top quality resources or some inspiration, definitely check out some of his work; it's amazing and **free**.

![](/assets/images/adding-springs-to-2d-platformers-in-unity/spring.png)

You can download the sprite sheet, the individual frames and the vector (in both svg and ai formats) from [This Link](https://mega.nz/#!bMUSxTyC!8mAUfmWQ_ynuFBhByTYELjBt0kwQ83I8XfESMzDL0oo). To keep inline with the same sharing is caring attitude Kenney has taken to his work - feel free to modify and use this however you see fit, including for commercial use.
