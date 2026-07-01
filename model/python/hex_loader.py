"""Intel HEX file loader for 8051 program memory."""

from typing import Optional


def load_hex(filename: str, rom_size: int = 65536) -> bytearray:
    """Load an Intel HEX file into a bytearray.

    Returns the bytearray (size rom_size) with program data loaded.
    """
    rom = bytearray(rom_size)

    with open(filename, 'r') as f:
        extended_addr = 0
        for line in f:
            line = line.strip()
            if not line or line[0] != ':':
                continue

            byte_count = int(line[1:3], 16)
            address = int(line[3:7], 16)
            record_type = int(line[7:9], 16)

            if record_type == 0x00:  # Data record
                addr = extended_addr + address
                for i in range(byte_count):
                    data_byte = int(line[9 + i*2:11 + i*2], 16)
                    if addr < rom_size:
                        rom[addr] = data_byte
                    addr += 1

            elif record_type == 0x01:  # EOF
                break

            elif record_type == 0x02:  # Extended segment address
                extended_addr = int(line[9:13], 16) << 4

            elif record_type == 0x04:  # Extended linear address
                extended_addr = int(line[9:13], 16) << 16

            # type 0x03 (start segment) and 0x05 (start linear) ignored

    return rom


def hex_to_bytes(hex_str: str) -> Optional[bytes]:
    """Parse a single line of Intel HEX into a (address, data) pair.

    Returns (address, bytes_data) or None.
    """
    hex_str = hex_str.strip()
    if not hex_str or hex_str[0] != ':':
        return None

    byte_count = int(hex_str[1:3], 16)
    address = int(hex_str[3:7], 16)
    record_type = int(hex_str[7:9], 16)

    if record_type != 0x00:
        return None

    data = bytes(int(hex_str[9 + i*2:11 + i*2], 16) for i in range(byte_count))
    return (address, data)


def create_test_hex() -> str:
    """Create a minimal test program in Intel HEX format.

    Program: repeatedly increment P1 port (blink-like).
    """
    # Assembly:
    # 0000: 75 90 00    MOV P1, #0x00
    # 0003: 05 90       INC P1
    # 0005: 80 FC       SJMP $
    hex_lines = [
        ":03000000759000F8",
        ":020003000590D0",
        ":0200050080FCF7",
        ":00000001FF",
    ]
    return '\n'.join(hex_lines)
