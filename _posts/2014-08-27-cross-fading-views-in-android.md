---
layout: post
title: "Cross-fading Views in Android"
date: 2014-08-27 19:55:00 +0100
categories:
  - programming
  - android
tags:
  - animation
  - cross fade
  - java
---
A new Android app I have recently been working on needed sprucing up a little bit yesterday and I've always found cross-fading between loading screens to be a nice, yet subtle, transitioning effect, so I put together a reusable class for it.

The code works on the premise that you have two views that each will take up the entire screen space. In my case, I had an ImageView which would be displayed while retrieving data to indicate the data is being loaded, and when the data had been loaded I would want to hide that ImageView and show a ListView.

Below is an example of the XML layout I was using and that is required for this guide:

```xml
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">

    <ImageView
        android:id="@+id/loading"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:src="@drawable/animation_loading"/>

    <ListView android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:id="@+id/list_view"
        android:visibility="gone" />

</LinearLayout>
```

As you can see, the ImageView named `loading` is the view that is initially visible, with the ListView hidden.

Once your layout is setup like the above, create a new file named `CrossFader.java` and copy and paste the below code, ensuring to change the package in the first line to whatever package you prefer it to be in:

```java
package com.rastating;

import android.animation.Animator;
import android.animation.AnimatorListenerAdapter;
import android.view.View;

public class CrossFader {
    private View mView1, mView2;
    private int mDuration;

    /***
     * Instantiate a new CrossFader object.
     * @param view1 the view to fade out
     * @param view2 the view to fade in
     * @param fadeDuration the duration in milliseconds for each fade to last
     */
    public CrossFader(View view1, View view2, int fadeDuration) {
        mView1 = view1;
        mView2 = view2;
        mDuration = fadeDuration;
    }

    /***
     * Start the cross-fade animation.
     */
    public void start() {
        mView2.setAlpha(0f);
        mView2.setVisibility(View.VISIBLE);
        mView1.animate()
            .alpha(0f)
            .setDuration(mDuration)
            .setListener(new AnimatorListenerAdapter() {
                @Override
                public void onAnimationEnd(Animator animation) {
                    mView1.setVisibility(View.GONE);
                    mView2.animate()
                        .alpha(1f)
                        .setDuration(mDuration)
                        .setListener(null);
                }
            });
    }
}
```

The CrossFader class takes three parameters in the constructor:

-    **view1** - the view to fade out (in the above case, the ImageView)
-    **view2** - the view to fade in (in the above case, the ListView)
-    **fadeDuration** - the time in milliseconds each fade animation should last

After instantiating a CrossFader object, we simply call the start method and the animation will begin. In the below example we fade out the ImageView, fade in the ListView and make each fade last 500 milliseconds:

```java
ListView listView = (ListView) findViewById(R.id.list_view);
ImageView loadingImage = (ImageView) findViewById(R.id.loading);

new CrossFader(loadingImage, listView, 500).start();
```

You can of course just use the code in the start method directly, if you wanted. In my project though it was going to be reused in a number of places so it made sense to abstract it into its own class.
