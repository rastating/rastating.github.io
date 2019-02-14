---
layout: post
title: "Setting Default CurrentCulture in all Versions of .NET"
date: 2012-09-12 21:27:00 +0100
categories:
  - programming
tags:
  - csharp
  - cultureinfo
  - CurrentCulture
  - thread
---
If you are using any version of .NET prior to 4.5, you will not have access to the handy property that is [DefaultThreadCurrentCulture](http://msdn.microsoft.com/en-us/library/system.globalization.cultureinfo.defaultthreadcurrentculture.aspx) (or if you are using .NET 4.5 just stop reading here and use that property!). However, that does not mean you can't set the default [CultureInfo](http://msdn.microsoft.com/en-us/library/kx54z3k7) to be used across the current thread and all threads spawned afterwards in the one place.

The CultureInfo class has two private static members named ```m_userDefaultCulture``` and ```m_userDefaultUICulture``` in versions prior to .NET 4.0; in 4.0 they are named ```s_userDefaultCulture``` and ```s_userDefaultUICulture```.

These two members are used when calling ```Thread.CurrentThread.CurrentCulture``` and ```Thread.CurrentThread.CurrentUICulture```, and with some simple reflection we can set these members, and all calls from there on to these two properties will return our newly set default.

Copy and paste the method below into your project wherever you see fit, ensuring that you are using both ```System.Globalization``` and ```System.Reflection``` at the top of the file:

```csharp
public void SetDefaultCulture(CultureInfo culture)
{
    Type type = typeof(CultureInfo);

    try
    {
        type.InvokeMember("s_userDefaultCulture",
                            BindingFlags.SetField | BindingFlags.NonPublic | BindingFlags.Static,
                            null,
                            culture,
                            new object[] { culture });

        type.InvokeMember("s_userDefaultUICulture",
                            BindingFlags.SetField | BindingFlags.NonPublic | BindingFlags.Static,
                            null,
                            culture,
                            new object[] { culture });
    }
    catch { }

    try
    {
        type.InvokeMember("m_userDefaultCulture",
                            BindingFlags.SetField | BindingFlags.NonPublic | BindingFlags.Static,
                            null,
                            culture,
                            new object[] { culture });

        type.InvokeMember("m_userDefaultUICulture",
                            BindingFlags.SetField | BindingFlags.NonPublic | BindingFlags.Static,
                            null,
                            culture,
                            new object[] { culture });
    }
    catch { }
}
```

Just to give a slight overview of what is happening in that method re. the try catch blocks – as mentioned previously, the names of these static members differs between .NET 4.0 and versions prior, so this will attempt to set both and fall back to whichever one it needs.

Once you've added the method, simply call it and pass through the CultureInfo you wish to be the default and you're done!

Below is a full example of how it can be used, or alternatively you can [Download This Sample Project](https://mega.co.nz/#!7UUkQCLa!zXPlhtaaXtFT74ituJqQmmcVbOkuQ5_Z7A6VYt7s05s).

Enjoy!

```csharp
using System;
using System.Globalization;
using System.Reflection;
using System.Threading;

namespace DefaultCultureInfoExample
{
    class Program
    {
        static void SetDefaultCulture(CultureInfo culture)
        {
            Type type = typeof(CultureInfo);

            try
            {
                type.InvokeMember("s_userDefaultCulture",
                                    BindingFlags.SetField | BindingFlags.NonPublic | BindingFlags.Static,
                                    null,
                                    culture,
                                    new object[] { culture });

                type.InvokeMember("s_userDefaultUICulture",
                                    BindingFlags.SetField | BindingFlags.NonPublic | BindingFlags.Static,
                                    null,
                                    culture,
                                    new object[] { culture });
            }
            catch { }

            try
            {
                type.InvokeMember("m_userDefaultCulture",
                                    BindingFlags.SetField | BindingFlags.NonPublic | BindingFlags.Static,
                                    null,
                                    culture,
                                    new object[] { culture });

                type.InvokeMember("m_userDefaultUICulture",
                                    BindingFlags.SetField | BindingFlags.NonPublic | BindingFlags.Static,
                                    null,
                                    culture,
                                    new object[] { culture });
            }
            catch { }
        }

        static void Main(string[] args)
        {
            Console.WriteLine("Culture name before update: {0}",
                              Thread.CurrentThread.CurrentCulture.Name);

            SetDefaultCulture(new CultureInfo("fr-fr"));
            Console.WriteLine("Culture name after update: {0}",
                              Thread.CurrentThread.CurrentCulture.Name);

            Console.ReadLine();
        }
    }
}
```
