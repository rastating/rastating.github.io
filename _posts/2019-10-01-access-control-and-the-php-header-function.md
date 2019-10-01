---
layout: post
title: Access Control and the PHP Header Function
date: 2019-10-01
categories:
  - security
  - websec
tags:
  - 'access control'
  - php
  - programming
image: /assets/images/2019-10-01-access-control-and-the-php-header-function/patched-code.png
---
Access control issues are noted by many to be something that never seems to get a whole lot less prevalent. Why? Because there is no real way to abstract it and make it automated; unless the developer is working with a framework which contains its own user system. As a result, implementing this will near always be down to the developer, and although it is a simple task, it can be very easy to overlook small mistakes or misinterpret how something will work.

A pattern I have seen a lot of in the past, cropped up again last night when reviewing some open-source projects and felt it was worth reiterating on. That pattern, is using [PHP's header function](https://www.php.net/manual/en/function.header.php) to initiate redirects when a user is not permitted to be viewing the page.

On the face of it, this pattern sounds fine and from a functional stand point *is* something you'd want to do. For example, if a user is trying to access a page that they need to be logged in to view, it'd not be user friendly to simply halt execution, you'd want to redirect them to the login page instead.

The problem with this is in the assumption of what is happening in the implementation of the `header` function. As the name suggests, this function will literally set a HTTP header; meaning code like this is quite common place:

```php
<?php
  session_start();
  include("connect.php");

  if(!isset($_SESSION['username'])) {
    header("location: index.php");
  }

  if(isset($_GET['id'])) {
    $id = $_GET['id'];
    $sql = "DELETE FROM posts WHERE id = '$id'";
    $result = mysqli_query($dbcon, $sql);

    if($result) {
      header('location: index.php');
    } else {
      echo "Failed to delete.".mysqli_connect_error();
    }
  }
  mysqli_close($dbcon);
?>
```

For those not overly familiar with PHP, let's break down lines 5-7. The `$_SESSION` global is an array of session variables. In a user system, this will typically be used to store the username / user ID of the currently logged in user so that it persists between loading different pages. In this case, the developer has chosen to check if the `username` session variable exists (to veirfy the user is logged in) and if it isn't, redirect them back to the home page.

Again, functionally, this sounds great, except a big assumption has been made about the `header` function. The assumption being that it will end script execution (spoiler: it does not). Any code that proceeds a call to `header` will still execute, as even if one is to set the `Location` header in order to facilitate a redirect - it is still completely valid to set content in the body of the response too.

In the project that I found this vulnerability in, all other files that rendered markup to the screen had appropriately handled this scenario, but in this particular file (used for handling post deletions), it had not been. It's possible this was a simple mistake, or that the author had thought maybe there is no exploitable functionality given that the page instantly redirects. If it was the latter, then it would definitely be the wrong presumption.

You'll notice on line 11 that there is string interpolation being used to create an SQL query to be executed:

```php
$id = $_GET['id'];
$sql = "DELETE FROM posts WHERE id = '$id'";
$result = mysqli_query($dbcon, $sql);
```

Although no data is output to the screen and a redirect is initiated, this does not stop us exploiting this. By injecting a call to [SLEEP](https://dev.mysql.com/doc/refman/8.0/en/miscellaneous-functions.html#function_sleep) in the `id` parameter (using the payload `1' RLIKE (SELECT * FROM (SELECT(SLEEP(5)))a)-- a`), it is possible to confirm that the injection is there and that we can use a time-based attack due to the response not being sent until the entirety of the PHP file has been executed:

![](/assets/images/2019-10-01-access-control-and-the-php-header-function/curl.png)

If you take a look at the last timestamp of the request (denoted with a `>`) and the first timestamp of the response (denoted by a `<`), you will see there is a 5 second difference - the same as the value specified in the call to `SLEEP`; confirming the injection can be exploited. This can be further illustrated by throwing SQLmap at it:

![](/assets/images/2019-10-01-access-control-and-the-php-header-function/sqlmap.png)

To fix the main vulnerability that allowed the bypass of the access control, it took simply adding a call to `exit` directly after the call to `header` as can be seen on line 7 of the patched code below:

```php
<?php
  session_start();
  include("connect.php");

  if(!isset($_SESSION['username'])) {
    header("location: index.php");
    exit();
  }

  if(isset($_GET['id'])) {
    $id = mysqli_real_escape_string($dbcon, $_GET['id']);
    $sql = "DELETE FROM posts WHERE id = '$id'";
    $result = mysqli_query($dbcon, $sql);

    if($result) {
      header('location: index.php');
    } else {
      echo "Failed to delete.".mysqli_connect_error();
    }
  }
  mysqli_close($dbcon);
?>
```

After applying this (even without fixing the SQL injection), the same curl request will no longer invoke the call to `SLEEP` as can be seen in the below output:

![](/assets/images/2019-10-01-access-control-and-the-php-header-function/curl-fixed.png)
