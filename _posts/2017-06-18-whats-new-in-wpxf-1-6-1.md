---
layout: post
title: "What's New in WPXF 1.6.1"
date: 2017-06-18
categories:
  - software
  - security
  - websec
tags:
  - wordpress exploit framework
  - wordpress
---
This is the first time I have written a blog post regarding [WordPress Exploit Framework](https://github.com/rastating/wordpress-exploit-framework). I've never felt the need to write one yet, but given some of the changes in the latest update that I have pushed to GitHub, it seemed fitting to do so now in order to update people on some of the bigger changes in v1.6.1.

## Supported Rubies
Probably the biggest change within v1.6.1 which could cause some issues, is dropping < Ruby 2.4.1. Although the code is **currently** still fully functional from 2.2.6 upwards, the `.ruby-version` file has been changed to signal to RVM to use 2.4.1.

### Why could this cause issues?
WPXF relies on a number of third party dependencies, in way of Ruby gems (which is why you run `bundle install` on installation and update). These gems are tied to specific Ruby versions, and thus switching to a new Ruby will require them to be re-installed.

Typically, any gem issues should be resolved by simply running `bundle install` again. There is a chance, though, that an error such as the below will occur:

> Ignoring ffi-1.9.3 because its extensions are not built. Try: gem pristine ffi --version 1.9.3

In the event this does happen, simply run through the list that bundler provides and execute the appropriate pristine commands.

## Major Bug in Self Updater
Along with the migration towards Ruby 2.4.1, I identified that there was a major bug in the self updater that can be used by running WPXF with the `--update` switch, which was causing hidden files to not be updated. This is a particularly big problem during the process of dropping Ruby 2.2.6 support, as it prevents the `.ruby-version` file from updating, thus preventing RVM users being properly notified.

This will have no major impact for users who upgrade to 1.6.1, as this will fix the issue going forward. For now, the code is still compatible with Ruby 2.2.6, but if anyone was to skip over version 1.6.1 and update at a point when incompatible code is introduced, this could see them receive unexpected and unpredictable errors.

If you're updating manually either by downloading the latest ZIP or by cloning straight from GitHub, this will not affect you.

## Less Bugs, More Meterpreter Sessions
One of the reasons all the changes have come about regarding the supported Rubies is to try and bring the Ruby version inline with Metasploit.

Why, you ask? Because v1.6.1 has introduced two new payloads:

* `meterpreter_bind_tcp`
* `meterpreter_reverse_tcp`

There is a wiki entry which explains the old / manual way of [Establishing a Meterpreter Session Using a Custom Payload](https://github.com/rastating/wordpress-exploit-framework/wiki/Establishing-a-Meterpreter-Session-Using-a-Custom-Payload/5c1586c6f0ecf87cc54c3079f35c8780d818252c), however, I felt there was really no need for this to be a manual process.

Personally, I use Meterpreter wherever possible, and running `msfvenom` manually was an extra unnecessary step, which has led to the creation of these two new payloads.

Both payloads will use `msfvenom` to create either a `php/meterpreter/bind_tcp` or a `php/meterpreter/reverse_tcp` payload and expose the basic options available to WPXF:

```
Payload options:

Name             Current Setting   Required   Description                                              
--------------   ---------------   --------   ------------------------------------------------------   
encode_payload   true              true       Encode the payload to avoid fingerprint detection        
msfvenom         msfvenom          true       The path to the msfvenom executable                      
lhost            10.2.0.3          true       The address of the host listening for a connection       
lport            4444              true       The port being used to listen for incoming connections   
```

The manual setup of the `exploit/multi/handler` module in Metasploit itself is still required, but the Meterpreter payload generation is now automated using these new payloads.

There is one pitfall to this level of automation - if the Ruby version being used in Metasploit and WPXF differs, errors may occur during payload generation and will cause the exploit to fail (hence the change regarding supported rubies!). With the latest update, this will hopefully be a none issue, as RVM users will be forced into using the same version of Ruby for both Metasploit and WPXF, so it should fit together nicely.

Should Metasploit be using a different version of Ruby, switch WPXF to use the same version using `rvm use`, and then re-run `bundle install` and the Meterpreter payloads should work without issue.

## Reporting Issues
Finally, if you do run into any problems or know of ways to improve the WPXF <--> MSF gem situation more elegantly, head over to GitHub and let me know or send a pull request! This has gone through quite a bit of testing, but given the different environments out there, I'm sure there are going to be some issues still not accommodated for; hopefully with minimal impact.
