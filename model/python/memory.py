"""8051 Memory Model: ROM, IRAM, SFR, XRAM."""

from typing import Optional

# SFR addresses
SFR_P0   = 0x80
SFR_SP   = 0x81
SFR_DPL  = 0x82
SFR_DPH  = 0x83
SFR_PCON = 0x87
SFR_TCON = 0x88
SFR_TMOD = 0x89
SFR_TL0  = 0x8A
SFR_TL1  = 0x8B
SFR_TH0  = 0x8C
SFR_TH1  = 0x8D
SFR_P1   = 0x90
SFR_SCON = 0x98
SFR_SBUF = 0x99
SFR_P2   = 0xA0
SFR_IE   = 0xA8
SFR_P3   = 0xB0
SFR_IP   = 0xB8
SFR_PSW  = 0xD0
SFR_ACC  = 0xE0
SFR_B    = 0xF0

# PSW bit positions
PSW_P  = 0
PSW_OV = 2
PSW_RS0 = 3
PSW_RS1 = 4
PSW_F0 = 5
PSW_AC = 6
PSW_CY = 7

# IE bit positions
IE_EX0 = 0
IE_ET0 = 1
IE_EX1 = 2
IE_ET1 = 3
IE_ES  = 4
IE_EA  = 7

# IP bit positions
IP_PX0 = 0
IP_PT0 = 1
IP_PX1 = 2
IP_PT1 = 3
IP_PS  = 4

# Interrupt vectors
INT_VEC_INT0 = 0x0003
INT_VEC_T0   = 0x000B
INT_VEC_INT1 = 0x0013
INT_VEC_T1   = 0x001B
INT_VEC_UART = 0x0023

# TCON bit positions
TCON_IT0 = 0
TCON_IE0 = 1
TCON_IT1 = 2
TCON_IE1 = 3
TCON_TR0 = 4
TCON_TF0 = 5
TCON_TR1 = 6
TCON_TF1 = 7

# SCON bit positions
SCON_RI  = 0
SCON_TI  = 1
SCON_RB8 = 2
SCON_TB8 = 3
SCON_REN = 4
SCON_SM2 = 5
SCON_SM1 = 6
SCON_SM0 = 7


class Memory:
    """8051 memory subsystem: ROM + IRAM + SFR + XRAM."""

    def __init__(self, rom_size: int = 4096):
        self.rom = bytearray(rom_size)
        self.iram = bytearray(128)      # 0x00-0x7F
        self.sfr = bytearray(128)       # 0x80-0xFF (SFR space)
        self.xram = bytearray(65536)    # external RAM (64KB)

        # SFR default values after reset
        self.sfr[SFR_SP - 0x80] = 0x07
        self.sfr[SFR_P0 - 0x80] = 0xFF
        self.sfr[SFR_P1 - 0x80] = 0xFF
        self.sfr[SFR_P2 - 0x80] = 0xFF
        self.sfr[SFR_P3 - 0x80] = 0xFF
        self.sfr[SFR_PCON - 0x80] = 0x00
        self.sfr[SFR_TCON - 0x80] = 0x00
        self.sfr[SFR_TMOD - 0x80] = 0x00
        self.sfr[SFR_IE - 0x80] = 0x00
        self.sfr[SFR_IP - 0x80] = 0x00
        self.sfr[SFR_PSW - 0x80] = 0x00

    def reset(self):
        """Reset memory to initial state."""
        self.iram = bytearray(128)
        self.sfr = bytearray(128)
        self.xram = bytearray(65536)
        self.sfr[SFR_SP - 0x80] = 0x07
        for addr in [SFR_P0, SFR_P1, SFR_P2, SFR_P3]:
            self.sfr[addr - 0x80] = 0xFF

    # ---- ROM ----
    def read_rom(self, addr: int) -> int:
        if 0 <= addr < len(self.rom):
            return self.rom[addr]
        return 0

    def write_rom(self, addr: int, value: int):
        if 0 <= addr < len(self.rom):
            self.rom[addr] = value & 0xFF

    # ---- IRAM (direct) ----
    def read_iram(self, addr: int) -> int:
        """Read internal RAM. 0x00-0x7F goes to IRAM, 0x80-0xFF goes to SFR."""
        addr &= 0xFF
        if addr < 0x80:
            return self.iram[addr]
        else:
            return self._read_sfr(addr)

    def write_iram(self, addr: int, value: int):
        addr &= 0xFF
        if addr < 0x80:
            self.iram[addr] = value & 0xFF
        else:
            self._write_sfr(addr, value & 0xFF)

    # ---- IRAM (indirect: @R0/@R1) ----
    def read_iram_indirect(self, addr: int) -> int:
        """Indirect read: 0x00-0x7F → IRAM, 0x80-0xFF → upper IRAM (not SFR)."""
        addr &= 0xFF
        if addr < 0x80:
            return self.iram[addr]
        else:
            # 8051: indirect access to 0x80-0xFF goes to upper 128B RAM
            # (not implemented in basic 8051, returns 0)
            return 0

    def write_iram_indirect(self, addr: int, value: int):
        addr &= 0xFF
        if addr < 0x80:
            self.iram[addr] = value & 0xFF

    # ---- SFR ----
    def _read_sfr(self, addr: int) -> int:
        return self.sfr[addr - 0x80]

    def _write_sfr(self, addr: int, value: int):
        self.sfr[addr - 0x80] = value & 0xFF

    def read_sfr(self, addr: int) -> int:
        return self._read_sfr(addr)

    def write_sfr(self, addr: int, value: int):
        self._write_sfr(addr, value)

    # ---- XRAM ----
    def read_xram(self, addr: int) -> int:
        return self.xram[addr & 0xFFFF]

    def write_xram(self, addr: int, value: int):
        self.xram[addr & 0xFFFF] = value & 0xFF

    # ---- Convenience SFR accessors ----
    @property
    def acc(self) -> int: return self.sfr[SFR_ACC - 0x80]
    @acc.setter
    def acc(self, v: int): self.sfr[SFR_ACC - 0x80] = v & 0xFF

    @property
    def b(self) -> int: return self.sfr[SFR_B - 0x80]
    @b.setter
    def b(self, v: int): self.sfr[SFR_B - 0x80] = v & 0xFF

    @property
    def psw(self) -> int: return self.sfr[SFR_PSW - 0x80]
    @psw.setter
    def psw(self, v: int): self.sfr[SFR_PSW - 0x80] = v & 0xFF

    @property
    def sp(self) -> int: return self.sfr[SFR_SP - 0x80]
    @sp.setter
    def sp(self, v: int): self.sfr[SFR_SP - 0x80] = v & 0xFF

    @property
    def dptr(self) -> int:
        return (self.sfr[SFR_DPH - 0x80] << 8) | self.sfr[SFR_DPL - 0x80]
    @dptr.setter
    def dptr(self, v: int):
        self.sfr[SFR_DPL - 0x80] = v & 0xFF
        self.sfr[SFR_DPH - 0x80] = (v >> 8) & 0xFF

    @property
    def ie(self) -> int: return self.sfr[SFR_IE - 0x80]
    @property
    def ip(self) -> int: return self.sfr[SFR_IP - 0x80]
    @property
    def tcon(self) -> int: return self.sfr[SFR_TCON - 0x80]
    @tcon.setter
    def tcon(self, v: int): self.sfr[SFR_TCON - 0x80] = v & 0xFF
    @property
    def scon(self) -> int: return self.sfr[SFR_SCON - 0x80]
    @scon.setter
    def scon(self, v: int): self.sfr[SFR_SCON - 0x80] = v & 0xFF

    # ---- Bit operations ----
    def read_bit(self, bit_addr: int) -> bool:
        """Read a bit-addressable location."""
        if bit_addr < 0x80:
            byte_addr = 0x20 + (bit_addr >> 3)  # IRAM 0x20-0x2F
        else:
            byte_addr = bit_addr & 0xF8  # SFR: round down to nearest 0x?8
        bit_pos = bit_addr & 0x7
        return bool(self.read_iram(byte_addr) & (1 << bit_pos))

    def write_bit(self, bit_addr: int, value: bool):
        if bit_addr < 0x80:
            byte_addr = 0x20 + (bit_addr >> 3)
        else:
            byte_addr = bit_addr & 0xF8
        bit_pos = bit_addr & 0x7
        v = self.read_iram(byte_addr)
        if value:
            v |= (1 << bit_pos)
        else:
            v &= ~(1 << bit_pos)
        self.write_iram(byte_addr, v)

    def read_carry(self) -> bool:
        return bool(self.psw & (1 << PSW_CY))

    def write_carry(self, v: bool):
        if v:
            self.sfr[SFR_PSW - 0x80] |= (1 << PSW_CY)
        else:
            self.sfr[SFR_PSW - 0x80] &= ~(1 << PSW_CY)
