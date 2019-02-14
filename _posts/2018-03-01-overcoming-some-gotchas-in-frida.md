---
layout: post
title: 'Overcoming Some "Gotcha''s" in Frida'
date: 2018-03-01
categories:
  - security
tags:
  - frida
---
I took part in a new research project recently, which involved quite a significant amount of reverse engineering; to which [Frida](https://www.frida.re/) came to the rescue. Whilst using it to hook into some obfuscated code, I ran into a few issues, with fixes which weren't overly obvious.

Calling The Correct Overload
----------------------------
The first problem I ran into was whilst attempting to call into the original implementation of a method that I had hooked into.

I had hooked into the `a` method of the `E$A$C$A` class, specifically the overload that expected an `e.u$a`. When trying to call the original implementation, using `this.a(c2248a)`, it would fail, and the application would throw a `java.lang.IncompatibleClassChangeError` exception.

The reason this happened, is because it was calling into another overload of this method, which also accepted a single argument, but of a different type.

To resolve this, I used the `overload` method a second time, to retrieve the original method implementation, and then invoked it using `call`, rather than calling the `a` method directly from `this`:

```javascript
Java.perform(function () {
  var E$A$C$A = Java.use('e.a.c.a');
  E$A$C$A.a.overload('e.u$a').implementation = function (c2248a) {
    return E$A$C$A.a.overload('e.u$a').call(this, c2248a);
  }
});
```

Naming Conflicts Between Fields & Methods
-----------------------------------------
The next issue I ran into, was that because I was dealing with obfuscated code, there were some naming clashes that typically wouldn't be seen.

For example, there was a field / property, named `c`, however, there was also a method named `c`.

When attempting to retrieve the value of this in Frida using `obj.c()`, it would always invoke the method, and the field seemed inaccessible. Thankfully, the developers of Frida thought about this ahead of time, and handled it by prefixing any fields that share the same name as a method, with an underscore.

This means, that in this intance, I'd be able to access the `c` field by calling `obj._c()` and access the method by calling `obj.c()`.
