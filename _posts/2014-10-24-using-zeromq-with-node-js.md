---
layout: post
title: "Using ZeroMQ with Node.js"
date: 2014-10-24 23:57:00 +0100
categories:
  - programming
tags:
  - zeromq
  - zmq
  - javascript
  - node.js
  - node
---
ZeroMQ (sometimes referred to as ØMQ) is an asynchronous messaging library which allows you to utilise a number of different patterns to fit the needs of a variety of scenarios and is capable of handling load balancing by itself, as can be seen in the demonstration video below.

<iframe width="420" height="315" src="//www.youtube.com/embed/RcrsklW0KkQ?rel=0" frameborder="0" allowfullscreen></iframe>

On the left, we have the application that is pushing the messages and on the right, we have two applications pulling the messages. As you can see, once we start the second application, the client applications alternate in pulling messages to process. Once one of the client applications exits, the remaining application continues to process all messages being pushed out; making this a great solution for situations where a worker may go down unexpectedly.

## Setting Up Our Environment
Before we can get started developing with ZeroMQ, you'll have to head over to the website at http://zeromq.org/ and install the latest version. If you're running Windows you can go ahead and grab the latest install wizard. If running on a UNIX like system however, you will have to build it yourself using the instructions found on the website.

Once ZeroMQ is setup, open a command line window or terminal and navigate to the folder you wish to place your Node.js files in and run the following command to download the Node.js bindings:

```bash
npm install zmq
```

Once installed, we can begin writing some code!

## The Pipeline Pattern
Let's start by taking a look at the pipline pattern (also referred to as the push/pull pattern). The pipline pattern is the one used in the demonstration video above, and consists of an application that pushes / sends messages (which I'll refer to as the server from here on) and one or more applications that pull / receive messages pushed from the server (which I'll refer to as the client).

So, what scenarios is this good for? Basically, any scenario in which the server does not need to receive feedback back from the client; typically this would be when offloading long running tasks.

Let's start by putting together the server application. The first thing we'll need to do is initialise the zmq module and create a new socket, so create a new file called server.js and put in the following code:

```javascript
var zmq = require("zmq");
var socket = zmq.socket("push");
var counter = 0;
```

As you can see, we specify the type of socket we want to create when calling the socket method. For a full list of possible types and how they work check out http://api.zeromq.org/4-0:zmq-socket

Next, add these two helper functions that we'll be using further in the script to keep the console logging consistent:

```javascript
function logToConsole (message) {
    console.log("[" + new Date().toLocaleTimeString() + "] " + message);
}

function sendMessage (message) {
    logToConsole("Sending: " + message);
    socket.send(message);
}
```

And now, bind the socket to all IP addresses on port 9998 and call to the sendMessage function every second to push the value of the `counter` variable:

```javascript
socket.bind("tcp://*:9998", function (error) {
    if (error) {
        logToConsole("Failed to bind socket: " + error.message);
        process.exit(0);
    }
    else {
        logToConsole("Server listening on port 9998");

        // Increment the counter and send the value to the clients every second.
        setInterval(function () { sendMessage(counter++); }, 1000);
    }
});
```

It is that simple! Your full script should now look like this:

```javascript
var zmq = require("zmq");
var socket = zmq.socket("push");
var counter = 0;

// Just a helper function for logging to the console with a timestamp.
function logToConsole (message) {
    console.log("[" + new Date().toLocaleTimeString() + "] " + message);
}

function sendMessage (message) {
    logToConsole("Sending: " + message);
    socket.send(message);
}

// Begin listening for connections on all IP addresses on port 9998.
socket.bind("tcp://*:9998", function (error) {
    if (error) {
        logToConsole("Failed to bind socket: " + error.message);
        process.exit(0);
    }
    else {
        logToConsole("Server listening on port 9998");

        // Increment the counter and send the value to the clients every second.
        setInterval(function () { sendMessage(counter++); }, 1000);
    }
});
```
Now that we have our server application able to push messages, we need to setup the client script that will pull them.

As we did before, open up a new file and name this one client.js and initialise a new socket:

```javascript
var zmq = require("zmq");
var socket = zmq.socket("pull");
```
This time we are setting the socket up using the pull type, as this socket needs to connect to the server and pull the messages.

As with before, we need to add a little helper function to keep logging consistent and we also need to setup an event handler for when messages are received on the socket:

```javascript
function logToConsole (message) {
    console.log("[" + new Date().toLocaleTimeString() + "] " + message);
}

socket.on("message", function (message) {
    // Convert the message into a string and log to the console.
    logToConsole("Received message: " + message.toString("utf8"));
});
```

Once we receive a message, the callback gets fired and we convert the message into a UTF8 string and log it to the console, again, very simple!

The last thing we need to do is simply establish a connection to the server application by adding this line of code:

```javascript
socket.connect('tcp://127.0.0.1:9998');
```

This assumes that you're running all of this on your local machine, if you've decided to run the server application on a different machine simply replace `127.0.0.1` with the IP address of the machine you wish to connect to.

Your client.js file should now look like this:

```javascript
var zmq = require("zmq");
var socket = zmq.socket("pull");

// Just a helper function for logging to the console with a timestamp.
function logToConsole (message) {
    console.log("[" + new Date().toLocaleTimeString() + "] " + message);
}

// Add a callback for the event that is invoked when we receive a message.
socket.on("message", function (message) {
    // Convert the message into a string and log to the console.
    logToConsole("Received message: " + message.toString("utf8"));
});

// Connect to the server instance.
socket.connect('tcp://127.0.0.1:9998');
```

Now, to give it a test run. Run the scripts using `node server` and `node client` from the directory you stored them in. It doesn't matter what order you start them in, as ZeroMQ is capable of re-establishing connections as they become available for you (another nice little feature).

The output of these applications should be akin to that of the demonstration video at the start of this guide. Go ahead and fire up more instances of the client application in separate command line / terminal windows and watch as the messages are balanced between all available connections!

## The Request / Reply Pattern
Another useful pattern that can be easily applied is the request / reply pattern, which as the name suggests, consists of a request being sent and a reply being received by the sender of the request.

By making a few small alterations to our original script we can enable our server script to receive replies from the client script.

To do this, change your server.js file to read:

```javascript
var zmq = require("zmq");
var socket = zmq.socket("req");
var counter = 0;

// Just a helper function for logging to the console with a timestamp.
function logToConsole (message) {
    console.log("[" + new Date().toLocaleTimeString() + "] " + message);
}

function sendMessage (message) {
    logToConsole("Sending: " + message);
    socket.send(message);
}

// Add a callback for the event that is invoked when we receive a message.
socket.on("message", function (message) {
    // Convert the message into a string and log to the console.
    logToConsole("Response: " + message.toString("utf8"));
});

// Begin listening for connections on all IP addresses on port 9998.
socket.bind("tcp://*:9998", function (error) {
    if (error) {
        logToConsole("Failed to bind socket: " + error.message);
        process.exit(0);
    }
    else {
        logToConsole("Server listening on port 9998");

        // Increment the counter and send the value to the clients every second.
        setInterval(function () { sendMessage(counter++); }, 1000);
    }
});
```

And our client.js file to read:

```javascript
var zmq = require("zmq");
var socket = zmq.socket("rep");

// Just a helper function for logging to the console with a timestamp.
function logToConsole (message) {
    console.log("[" + new Date().toLocaleTimeString() + "] " + message);
}

// Add a callback for the event that is invoked when we receive a message.
socket.on("message", function (message) {
    // Convert the message into a string and log to the console.
    logToConsole("Received message: " + message.toString("utf8"));

    // Send the message back aa a reply to the server.
    socket.send(message);
});

// Connect to the server instance.
socket.connect('tcp://127.0.0.1:9998');
```

As you can see, the only changes we've had to make are:

*    Change the socket type to `req` on the server and `rep` on the client
*    Add a message callback to the server
*    Send a message using the socket after receiving one on the client

Now, when running these two applications, we will see the replies on the server and the clients will only process the next request once it has finished replying to the previous one and as with the previous pipeline pattern example, it will handle load balancing automatically between available clients.

Hopefully this will prove as a useful starting point for utilising ZeroMQ, be sure to check out the website for more in depth information as to what it can achieve and what it can do for you.
