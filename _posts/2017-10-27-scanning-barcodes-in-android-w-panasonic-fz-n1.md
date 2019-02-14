---
layout: post
title: Scanning Barcodes w/ Panasonic FZ-N1
date: 2017-10-27
categories:
  - programming
  - android
tags:
  - java
  - panasonic
  - FZ-N1
  - barcode
  - scanning
---
Reading barcodes in Android from the Panasonic FZ-N1 barcode scanner is natively achievable via the `dispatchKeyEvent` method within an `Activity`.

When initially pressing down the scanner button, on the side of the device, the event will be triggered twice; once with key code `305`, and once with key code `304`.

If a barcode is then scanned, whilst the button is held down, the event will be raised again, with key code `0`, and the full barcode string available using the `getCharacters` method of the `KeyEvent`.

After a successful scan, or release of the button, the same two key codes raised initially, will be sent again in an `ACTION_UP` event.

Some sample code can be found below, which can be implemeneted directly into an `Activity`, allowing for scanned barcodes to be handled within the `onBarcodeScanned` method.

```java
// Required instance variables
private boolean mFirstBarcodeLatch;
private boolean mSecondBarcodeLatch;

private void onBarcodeScanned(String barcode) {
  // Handle the barcode in here.
}

@Override
public boolean dispatchKeyEvent(KeyEvent event) {
    if (event.getAction() == KeyEvent.ACTION_DOWN) {
        if (event.getKeyCode() == 305) {
            mFirstBarcodeLatch = true;
        }
        else if (event.getKeyCode() == 304) {
            mSecondBarcodeLatch = true;
        }
    }
    else {
        if (event.getKeyCode() == 305) {
            mFirstBarcodeLatch = false;
        }
        else if (event.getKeyCode() == 304) {
            mSecondBarcodeLatch = false;
        }
    }

    if (event.getKeyCode() == 0 && mFirstBarcodeLatch && mSecondBarcodeLatch) {
        onBarcodeScanned(event.getCharacters());
    }

    return super.dispatchKeyEvent(event);
}
```
