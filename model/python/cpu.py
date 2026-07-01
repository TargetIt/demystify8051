"""8051 CPU Core: execution loop, peripherals, interrupt handling."""

from .memory import (Memory, SFR_ACC, SFR_PSW, SFR_SP, SFR_DPH, SFR_DPL,
                      SFR_P0, SFR_P1, SFR_P2, SFR_P3,
                      SFR_TCON, SFR_TMOD, SFR_TL0, SFR_TH0, SFR_TL1, SFR_TH1,
                      SFR_SCON, SFR_SBUF, SFR_IE, SFR_IP, SFR_PCON,
                      PSW_CY, PSW_RS0, PSW_RS1,
                      TCON_TF0, TCON_TF1, TCON_TR0, TCON_TR1,
                      TCON_IE0, TCON_IE1, TCON_IT0, TCON_IT1,
                      IE_EA, IE_ES, IE_ET1, IE_EX1, IE_ET0, IE_EX0,
                      INT_VEC_INT0, INT_VEC_T0, INT_VEC_INT1, INT_VEC_T1, INT_VEC_UART)
from .decoder import decode, build_opcode_table
from .hex_loader import load_hex


class CPU:
    """8051 CPU core with integrated peripherals (Timer, UART, Interrupts, I/O)."""

    def __init__(self, rom_size: int = 4096):
        build_opcode_table()

        self.mem = Memory(rom_size)
        self.pc = 0
        self.cycles = 0
        self.instructions = 0
        self.running = True
        self.interrupt_active = False
        self.pending_interrupts: list[tuple[int, int]] = []  # [(vector, priority)]

        # Hooks for I/O
        self.port_read_hook = None   # callable(port_num) -> int
        self.port_write_hook = None  # callable(port_num, value)
        self.uart_tx_hook = None     # callable(byte)
        self.uart_rx_data = []       # list of bytes waiting for Rx

    def reset(self):
        self.mem.reset()
        self.pc = 0
        self.cycles = 0
        self.instructions = 0
        self.running = True
        self.interrupt_active = False
        self.pending_interrupts.clear()
        # SFR defaults after reset
        self.mem.sp = 0x07
        self.mem.write_sfr(SFR_P0, 0xFF)
        self.mem.write_sfr(SFR_P1, 0xFF)
        self.mem.write_sfr(SFR_P2, 0xFF)
        self.mem.write_sfr(SFR_P3, 0xFF)

    def load_hex(self, filename: str):
        self.mem.rom = load_hex(filename, len(self.mem.rom))
        self.pc = 0

    def load_bytes(self, data: bytes, start_addr: int = 0):
        for i, b in enumerate(data):
            if start_addr + i < len(self.mem.rom):
                self.mem.rom[start_addr + i] = b

    # ===== Register access =====
    def _reg_bank_base(self) -> int:
        rs = (self.mem.psw >> PSW_RS0) & 0x03
        return rs * 8

    def read_rn(self, n: int) -> int:
        return self.mem.read_iram(self._reg_bank_base() + (n & 0x7))

    def write_rn(self, n: int, value: int):
        self.mem.write_iram(self._reg_bank_base() + (n & 0x7), value)

    def r0_addr(self) -> int:
        return self.read_rn(0)

    def r1_addr(self) -> int:
        return self.read_rn(1)

    # ===== Fetch =====
    def fetch(self) -> int:
        b = self.mem.read_rom(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        return b

    # ===== Interrupt handling =====
    def request_interrupt(self, vector: int, flag_addr: int, flag_bit: int,
                          enable_bit: int):
        """Request an interrupt. Called by peripherals when interrupt condition met."""
        ie = self.mem.ie
        if not (ie & (1 << enable_bit)):
            return
        sfr = flag_addr
        self.mem.sfr[sfr - 0x80] |= (1 << flag_bit)

        ip = self.mem.ip
        if enable_bit == IE_ES:
            priority = 1 if (ip & 0x10) else 0
        elif enable_bit == IE_ET1:
            priority = 1 if (ip & 0x08) else 0
        elif enable_bit == IE_EX1:
            priority = 1 if (ip & 0x04) else 0
        elif enable_bit == IE_ET0:
            priority = 1 if (ip & 0x02) else 0
        else:  # IE_EX0
            priority = 1 if (ip & 0x01) else 0

        self.pending_interrupts.append((vector, priority))
        self.pending_interrupts.sort(key=lambda x: -x[1])  # higher priority first

    def _service_interrupts(self):
        """Check and service pending interrupts."""
        if not self.pending_interrupts:
            return
        ie = self.mem.ie
        if not (ie & (1 << 7)):  # EA disabled
            self.pending_interrupts.clear()
            return

        vector, _ = self.pending_interrupts[0]
        self.pending_interrupts.clear()

        # Push PC
        sp = self.mem.sp
        self.mem.write_iram((sp + 1) & 0xFF, self.pc & 0xFF)
        self.mem.write_iram((sp + 2) & 0xFF, (self.pc >> 8) & 0xFF)
        self.mem.sp = (sp + 2) & 0xFF
        self.interrupt_active = True
        self.pc = vector

    # ===== Step =====
    def step(self) -> int:
        """Execute one instruction. Returns cycles consumed."""
        if not self.running:
            return 0

        self._service_interrupts()

        opcode = self.fetch()
        info = decode(opcode)
        info.handler(self, opcode)

        self.instructions += 1
        cycles_taken = info.cycles
        self.cycles += cycles_taken

        # Peripheral update (after each instruction)
        self._update_timers(cycles_taken)
        self._update_serial()

        return cycles_taken

    def run(self, max_cycles: int = -1):
        """Run until max_cycles or cpu halts."""
        start = self.cycles
        while self.running:
            if max_cycles > 0 and (self.cycles - start) >= max_cycles:
                break
            self.step()

    # ===== Timer update =====
    def _update_timers(self, elapsed: int):
        """Update T0 and T1 based on elapsed cycles."""
        tmod = self.mem.read_sfr(SFR_TMOD)
        tcon = self.mem.read_sfr(SFR_TCON)

        for tn in [0, 1]:
            tr_bit = TCON_TR0 if tn == 0 else TCON_TR1
            if not (tcon & (1 << tr_bit)):
                continue

            gate_bit = 3 if tn == 0 else 7
            ct_bit = 2 if tn == 0 else 6
            m0_bit = 0 if tn == 0 else 4
            m1_bit = 1 if tn == 0 else 5
            th_addr = SFR_TH0 if tn == 0 else SFR_TH1
            tl_addr = SFR_TL0 if tn == 0 else SFR_TL1

            # Gate check
            if (tmod & (1 << gate_bit)):
                int_bit = 2 if tn == 0 else 3  # INT0/INT1
                if not (tcon & (1 << int_bit)):
                    continue

            # Counter mode (external pin) — not supported in ISS, skip
            if (tmod & (1 << ct_bit)):
                continue

            # Timer mode
            mode = ((tmod >> (m0_bit)) & 1) | (((tmod >> (m1_bit)) & 1) << 1)

            th = self.mem.read_sfr(th_addr)
            tl = self.mem.read_sfr(tl_addr)

            if mode == 0:  # 13-bit
                val = ((th << 5) | (tl & 0x1F)) + elapsed
                if val > 0x1FFF:
                    val = 0
                    tcon |= (1 << (TCON_TF0 if tn == 0 else TCON_TF1))
                    self.request_interrupt(
                        INT_VEC_T0 if tn == 0 else INT_VEC_T1,
                        SFR_TCON, TCON_TF0 if tn == 0 else TCON_TF1,
                        IE_ET0 if tn == 0 else IE_ET1)
                self.mem.write_sfr(th_addr, (val >> 5) & 0xFF)
                self.mem.write_sfr(tl_addr, val & 0x1F)

            elif mode == 1:  # 16-bit
                val = ((th << 8) | tl) + elapsed
                if val > 0xFFFF:
                    val = 0
                    tcon |= (1 << (TCON_TF0 if tn == 0 else TCON_TF1))
                    self.request_interrupt(
                        INT_VEC_T0 if tn == 0 else INT_VEC_T1,
                        SFR_TCON, TCON_TF0 if tn == 0 else TCON_TF1,
                        IE_ET0 if tn == 0 else IE_ET1)
                self.mem.write_sfr(th_addr, (val >> 8) & 0xFF)
                self.mem.write_sfr(tl_addr, val & 0xFF)

            elif mode == 2:  # 8-bit auto-reload
                val = tl + elapsed
                if val > 0xFF:
                    val = 0
                    tcon |= (1 << (TCON_TF0 if tn == 0 else TCON_TF1))
                    self.request_interrupt(
                        INT_VEC_T0 if tn == 0 else INT_VEC_T1,
                        SFR_TCON, TCON_TF0 if tn == 0 else TCON_TF1,
                        IE_ET0 if tn == 0 else IE_ET1)
                    self.mem.write_sfr(tl_addr, th)  # reload from TH
                else:
                    self.mem.write_sfr(tl_addr, val)

        self.mem.tcon = tcon

    # ===== Serial update =====
    def _update_serial(self):
        """UART TX/RX with baud rate simulation. TX sends one bit per baud tick."""
        scon = self.mem.scon
        mode = (scon >> 6) & 3  # SM0,SM1

        # TX: Check if TI was set by previous transmission, clear if so
        if scon & 0x02:  # TI set
            self.mem.scon = scon & ~0x02  # clear TI

        # TX: If SBUF was written (detected via SBUF != last value), start TX
        sbuf_val = self.mem.read_sfr(SFR_SBUF)
        if hasattr(self, '_last_sbuf') and sbuf_val != self._last_sbuf:
            # New byte written to SBUF — start transmission
            self._tx_byte = sbuf_val
            self._tx_bit_count = 0
            self._tx_busy = True
            # TI will be set after all bits transmitted
        self._last_sbuf = sbuf_val

        # TX bit transmission
        if getattr(self, '_tx_busy', False):
            self._tx_bit_count += 1
            bits_per_frame = 10 if mode == 1 else 11  # start + 8 data + stop (+ parity for mode 2/3)
            if self._tx_bit_count >= bits_per_frame:
                scon |= 0x02  # set TI
                self.mem.scon = scon
                self._tx_busy = False
                self.request_interrupt(INT_VEC_UART, SFR_SCON, 1, IE_ES)  # TI interrupt

        # RX: Check for incoming bytes
        if self.uart_rx_data and (scon & 0x10):  # REN enabled
            byte = self.uart_rx_data.pop(0)
            self.mem.write_sfr(SFR_SBUF, byte)
            scon |= 0x01  # set RI
            self.mem.scon = scon
            self.request_interrupt(INT_VEC_UART, SFR_SCON, 0, IE_ES)

    def uart_receive(self, byte: int):
        """Enqueue a byte for UART reception (external API)."""
        self.uart_rx_data.append(byte & 0xFF)
        # Initialize TX state
        if not hasattr(self, '_tx_busy'):
            self._tx_busy = False
            self._tx_byte = 0
            self._tx_bit_count = 0
            self._last_sbuf = 0

    # ===== State dump =====
    def get_state(self) -> dict:
        return {
            'pc': self.pc,
            'acc': self.mem.acc,
            'b': self.mem.b,
            'psw': self.mem.psw,
            'sp': self.mem.sp,
            'dptr': self.mem.dptr,
            'cycles': self.cycles,
            'instructions': self.instructions,
            'ie': self.mem.ie,
            'ip': self.mem.ip,
            'tcon': self.mem.tcon,
            'iram': bytes(self.mem.iram),
            'sfr': bytes(self.mem.sfr),
        }
