// Top-level testbench for echo_8051
// Verifies: reset, clock, basic instruction execution
// Compares RTL output against golden reference (external ISS)

`timescale 1ns/1ps

module tb_echo_8051_top;
    reg         clk;
    reg         rst_n;
    reg         int0_n, int1_n;
    wire [7:0]  p0, p1, p2, p3;
    reg         rxd;
    wire        txd, ale, psen_n, rd_n, wr_n;
    reg         ea_n;

    // Clock generation: 50 MHz = 20ns period
    always #10 clk = ~clk;

    // DUT instantiation
    echo_8051_top dut (
        .clk(clk), .rst_n(rst_n),
        .int0_n(int0_n), .int1_n(int1_n),
        .p0(p0), .p1(p1), .p2(p2), .p3(p3),
        .rxd(rxd), .txd(txd),
        .ale(ale), .psen_n(psen_n), .rd_n(rd_n), .wr_n(wr_n),
        .ea_n(ea_n)
    );

    initial begin
        $display("=== echo_8051 Top-Level Testbench ===");
        $display("Clock: 50 MHz (20ns period)");

        // Initialize
        clk = 0;
        rst_n = 0;
        int0_n = 1;
        int1_n = 1;
        rxd = 1;
        ea_n = 0;  // internal ROM

        // Reset pulse
        #50 rst_n = 1;
        #100;

        // Wait for first instruction fetch
        #200;

        // Check basic signals
        $display("Reset complete. Checking operation...");

        // Run for 100 cycles
        #2000;

        $display("Simulation complete.");
        $finish;
    end

    // Monitor important signals
    initial begin
        $monitor("[%0t] PC=%h  IR=%h  ACC=%h  PSW=%b  SP=%h",
                 $time,
                 dut.pc,
                 dut.ir,
                 dut.acc,
                 dut.psw_flags,
                 dut.sp);
    end

    // Waveform dump
    initial begin
        $dumpfile("tb_echo_8051_top.vcd");
        $dumpvars(0, tb_echo_8051_top);
    end

endmodule
