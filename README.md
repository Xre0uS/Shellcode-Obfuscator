Takes a given shellcode file (generated using msfvenom, for example), shuffle and randomise the shellcode, then generate a C source file to be compiled. 

Obfuscation Through Memory Manipulation: By using memcpy to dynamically assemble the shellcode in memory, effectively hiding the malicious code from static analysis tools.

Dynamic Reassembly at Runtime: The shellcode is only assembled and becomes recognizable as such during runtime, which helps in evading detection mechanisms that scan executable files before they are run.

Flexibility: Can be applied to various types of shellcode as long as they are compatible with Windows.

Still WIP
