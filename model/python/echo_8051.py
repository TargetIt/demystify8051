"""echo_8051 main API — compatible with Intel MCS-51 (8051) microcontroller."""

from typing import Optional, Callable, Any
from .cpu import CPU


class Echo8051:
    """Public API for the echo_8051 instruction set simulator.

    Usage:
        cpu = Echo8051()
        cpu.load_hex("firmware.hex")
        cpu.run(max_cycles=10000)
        state = cpu.get_state()
        print(f"ACC=0x{state['acc']:02X}, PSW=0x{state['psw']:02X}")
    """

    def __init__(self, rom_size: int = 4096):
        self._cpu = CPU(rom_size)
        self._cpu.reset()

    def reset(self):
        """Reset CPU to initial state."""
        self._cpu.reset()

    def load_hex(self, filename: str):
        """Load an Intel HEX file into program ROM."""
        self._cpu.load_hex(filename)

    def load_bytes(self, data: bytes, start_addr: int = 0):
        """Load raw bytes into program ROM at given start address."""
        self._cpu.load_bytes(data, start_addr)

    def step(self) -> int:
        """Execute one instruction. Returns number of cycles consumed."""
        return self._cpu.step()

    def run(self, max_cycles: int = -1, max_instructions: int = -1):
        """Run until max_cycles or max_instructions reached.

        Args:
            max_cycles: Maximum machine cycles (-1 = unlimited)
            max_instructions: Maximum instructions (-1 = unlimited)
        """
        start_cycles = self._cpu.cycles
        start_instr = self._cpu.instructions
        while self._cpu.running:
            if max_cycles > 0 and (self._cpu.cycles - start_cycles) >= max_cycles:
                break
            if max_instructions > 0 and (self._cpu.instructions - start_instr) >= max_instructions:
                break
            self._cpu.step()

    def get_state(self) -> dict:
        """Return complete CPU state snapshot."""
        return self._cpu.get_state()

    def set_irq(self, irq_num: int):
        """Trigger external interrupt (0=INT0, 1=INT1)."""
        from .memory import INT_VEC_INT0, INT_VEC_INT1, SFR_TCON, TCON_IE0, IE_EX0, IE_EX1
        if irq_num == 0:
            self._cpu.request_interrupt(INT_VEC_INT0, SFR_TCON, TCON_IE0, IE_EX0)
        elif irq_num == 1:
            self._cpu.request_interrupt(INT_VEC_INT1, SFR_TCON, 0x03, IE_EX1)  # IE1=bit3

    def uart_receive(self, byte: int):
        """Push a byte into the UART receive buffer."""
        self._cpu.uart_receive(byte)

    def read_port(self, port: int) -> int:
        """Read an I/O port (0-3)."""
        from .memory import SFR_P0, SFR_P1, SFR_P2, SFR_P3
        addr = [SFR_P0, SFR_P1, SFR_P2, SFR_P3][port & 3]
        return self._cpu.mem.read_sfr(addr)

    def write_port(self, port: int, value: int):
        """Write to an I/O port (0-3)."""
        from .memory import SFR_P0, SFR_P1, SFR_P2, SFR_P3
        addr = [SFR_P0, SFR_P1, SFR_P2, SFR_P3][port & 3]
        self._cpu.mem.write_sfr(addr, value & 0xFF)

    def get_pc(self) -> int:
        return self._cpu.pc

    def get_cycles(self) -> int:
        return self._cpu.cycles

    def get_instruction_count(self) -> int:
        return self._cpu.instructions

    @property
    def mem(self):
        return self._cpu.mem

    @property
    def acc(self) -> int:
        return self._cpu.mem.acc

    @property
    def psw(self) -> int:
        return self._cpu.mem.psw
