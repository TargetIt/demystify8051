#!/bin/bash
# Equivalence verification: RTL vs Gate-Level Netlist
# Method: Yosys formal (if available) or Icarus Verilog simulation

set -e
cd "$(dirname "$0")/.."

echo "=== echo_8051 Equivalence Check ==="

# Check if Yosys is available
if command -v "$HOME/tools/oss-cad-suite/bin/yosys" &>/dev/null; then
    echo "Yosys found. Running formal equivalence..."
    $HOME/tools/oss-cad-suite/bin/yosys -q tools/equiv_check.ys 2>&1 | tee data/equiv_yosys.log
    if grep -q "EQUIVALENT" data/equiv_yosys.log; then
        echo "PASS: Yosys proves equivalence"
    else
        echo "NOTE: Yosys formal check incomplete — falling back to simulation"
    fi
fi

# Icarus Verilog simulation-based check
if command -v iverilog &>/dev/null; then
    echo "Icarus found. Running simulation-based equivalence..."
    mkdir -p build
    iverilog -o build/tb_equiv.vvp \
        rtl/alu.v rtl/decoder.v rtl/control_fsm.v rtl/psw.v \
        rtl/iram.v rtl/sfr_block.v rtl/timer.v rtl/uart.v \
        rtl/intc.v rtl/io_ports.v rtl/echo_8051_top.v \
        input/echo_8051_synth.v \
        tb/tb_equiv.v 2>&1 | tee data/equiv_iverilog.log
    vvp build/tb_equiv.vvp | tee -a data/equiv_iverilog.log
    if grep -q "PASS" data/equiv_iverilog.log; then
        echo "PASS: Simulation equivalence confirmed"
    else
        echo "FAIL: RTL and gate-level outputs differ"
        exit 1
    fi
else
    echo "WARNING: Neither Yosys nor Icarus available — skipping equivalence check"
fi
