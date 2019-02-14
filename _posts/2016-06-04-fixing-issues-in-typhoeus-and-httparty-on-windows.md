---
layout: post
title: Fixing Issues in Typhoeus and HTTParty on Windows
date: 2016-06-04
categories:
  - windows
  - ruby
  - programming
tags:
  - typhoeus
  - httparty
  - libcurl
  - openssl
---
Recently when doing some Ruby development using the Typhoeus and HTTParty gems with a Windows machine, I've found there are two issues that seem to appear out of the box near enough every time. Both these issues are easily resolved, but there are a lot of inappropriate solutions being suggested around the web (such as disabling SSL!?!).

## Issue 1: Failing to load libcurl
This is the issue that seems to be affecting Windows users all around, and is due to the fact libcurl is missing, most of the time. This issue will manifest itself by throwing exceptions with messages akin to `Could not open library 'libcurl.dll': The specified module could not be found.` when trying to load the gem / make requests.

If you are experiencing this error, you will need to ensure the latest libcurl binary is included in your Ruby bin folder (e.g. `C:\Ruby22\bin`), or any other folder that is in your environment's `PATH` variable.

The latest version can be downloaded from http://curl.haxx.se/download.html. As of 04/06/2016, the latest release is marked as `Win32 2000/XP zip 7.40.0 libcurl SSL`. After downloading the archive, extract the contents of the bin directory into your Ruby bin directory (if prompted, don't overwrite any existing DLLs).

## Issue 2: Unable to verify SSL certificates
So far, I've experienced this issue on every Windows machine I've setup for development and is an issue in the underlying library that Typhoeus and HTTParty use (OpenSSL), so this issue may show its head when using other HTTP(s) gems too.

In Typhoeus, this issue will result in no exception being thrown, but a blank response being returned if requesting HTTPS URLs and a return code of `:ssl_cacert`.

Below is an example of a response when requesting https://www.google.com/

```ruby
<Typhoeus::Response:0x3dc4bf8
  @options = {
    :httpauth_avail => 0,
    :total_time => 0.046,
    :starttransfer_time => 0.0,
    :appconnect_time => 0.0,
    :pretransfer_time => 0.0,
    :connect_time => 0.015,
    :namelookup_time => 0.0,
    :redirect_time => 0.0,
    :effective_url => "https://www.google.com/",
    :primary_ip => "62.255.45.162",
    :response_code => 0,
    :request_size => 0,
    :redirect_count => 0,
    :return_code => :ssl_cacert,
    :response_headers => "",
    :response_body => "",
    :debug_info => #<Ethon::Easy::DebugInfo:0x3dc5180 @messages=[]>
  },
  @request = #<Typhoeus::Request:0x3dc55d0
    @base_url = "https://www.google.com/",
    @original_options = { :method => :get },
    @options = {
      :method => :get,
      :headers => {
        "User-Agent" => "Typhoeus - https://github.com/typhoeus/typhoeus"
      },
      :maxredirs => 50
    },
    @response = #<Typhoeus::Response:0x3dc4bf8 ...>,
    @on_complete = [],
    @on_failure = []
  >
>
```

In HTTParty, the same issue will instead throw an exception directly from OpenSSL, like this:

```
OpenSSL::SSL::SSLError: SSL_connect returned=1 errno=0 state=SSLv3 read server certificate B: certificate verify failed
        from C:/Ruby22/lib/ruby/2.2.0/net/http.rb:923:in `connect'
        from C:/Ruby22/lib/ruby/2.2.0/net/http.rb:923:in `block in connect'
        from C:/Ruby22/lib/ruby/2.2.0/timeout.rb:73:in `timeout'
        from C:/Ruby22/lib/ruby/2.2.0/net/http.rb:923:in `connect'
        from C:/Ruby22/lib/ruby/2.2.0/net/http.rb:863:in `do_start'
        from C:/Ruby22/lib/ruby/2.2.0/net/http.rb:852:in `start'
        from C:/Ruby22/lib/ruby/2.2.0/net/http.rb:1375:in `request'
        from C:/Ruby22/lib/ruby/gems/2.2.0/gems/httparty-0.13.7/lib/httparty/request.rb:117:in `perform'
        from C:/Ruby22/lib/ruby/gems/2.2.0/gems/httparty-0.13.7/lib/httparty.rb:545:in `perform_request'
        from C:/Ruby22/lib/ruby/gems/2.2.0/gems/httparty-0.13.7/lib/httparty.rb:476:in `get'
        from C:/Ruby22/lib/ruby/gems/2.2.0/gems/httparty-0.13.7/lib/httparty.rb:583:in `get'
        from (irb):2
        from C:/Ruby22/bin/irb:11:in `<main>'
```

The first step to resolving this, is to download the `cacert.pem` file from [https://curl.haxx.se/docs/caextract.html](https://curl.haxx.se/docs/caextract.html) and store it somewhere permanently on your system.

Once you've downloaded and extracted the file, add a new environment variable called `SSL_CERT_FILE` and set its value to be the path to `cacert.pem`. If you're unsure of how to add new environment variables, [Check Out This Page](https://www.microsoft.com/resources/documentation/windows/xp/all/proddocs/en-us/sysdm_advancd_environmnt_addchange_variable.mspx?mfr=true).

After doing this, you'll have to close any command prompts you are using to execute Ruby scripts and restart them, but after doing so, it should pick up the new variable and HTTPS requests should now work.
