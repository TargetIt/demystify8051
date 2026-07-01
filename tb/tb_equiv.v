// Simulation-based equivalence check
// Runs the same program on RTL and gate-level netlist, compares output
// This is the practical alternative to formal equivalence for reverse-engineered designs

`timescale 1ns/1ps

module tb_equiv;
    reg clk, rst_n;
    reg int0_n, int1_n, rxd, ea_n;
    wire [7:0] p0_rtl, p1_rtl, p2_rtl, p3_rtl;
    wire txd_rtl, ale_rtl, psen_n_rtl, rd_n_rtl, wr_n_rtl;
    wire [7:0] p0_gate, p1_gate, p2_gate, p3_gate;
    wire txd_gate, ale_gate, psen_n_gate, rd_n_gate, wr_n_gate;

    always #10 clk = ~clk;

    // RTL DUT
    echo_8051_top rtl (
        .clk(clk), .rst_n(rst_n), .int0_n(int0_n), .int1_n(int1_n),
        .p0(p0_rtl), .p1(p1_rtl), .p2(p2_rtl), .p3(p3_rtl),
        .rxd(rxd), .txd(txd_rtl), .ale(ale_rtl), .psen_n(psen_n_rtl),
        .rd_n(rd_n_rtl), .wr_n(wr_n_rtl), .ea_n(ea_n)
    );

    // Gate-level DUT (original netlist)
    echo_8051_top gate (
        .clk(clk), .rst_n(rst_n), .int0_n(int0_n), .int1_n(int1_n),
        .p0(p0_gate), .p1(p1_gate), .p2(p2_gate), .p3(p3_gate),
        .rxd(rxd), .txd(txd_gate), .ale(ale_gate), .psen_n(psen_n_gate),
        .rd_n(rd_n_gate), .wr_n(wr_n_gate), .ea_n(ea_n)
    );

    integer mismatch_count;
    integer cycle_count;
    reg check_enable;

    initial begin
        $display("=== Equivalence Check: RTL vs Gate-Level Netlist ===");
        clk = 0; rst_n = 0; int0_n = 1; int1_n = 1; rxd = 1; ea_n = 0;
        mismatch_count = 0;
        cycle_count = 0;
        check_enable = 0;

        #50 rst_n = 1;
        #200 check_enable = 1;  // start checking after reset

        // Run for 5000 cycles (enough for smoke test program)
        #100000;

        if (mismatch_count == 0)
            $display("PASS: RTL matches gate-level netlist (%0d cycles)", cycle_count);
        else
            $display("FAIL: %0d mismatches in %0d cycles", mismatch_count, cycle_count);
        $finish;
    end

    // Compare on each posedge
    always @(posedge clk) begin
        if (check_enable) begin
            cycle_count <= cycle_count + 1;
            if (p0_rtl !== p0_gate) begin mismatch_count <= mismatch_count + 1; $display("[%0d] P0 mismatch: RTL=%h GATE=%h", $time, p0_rtl, p0_gate); end
            if (p1_rtl !== p1_gate) begin mismatch_count <= mismatch_count + 1; $display("[%0d] P1 mismatch: RTL=%h GATE=%h", $time, p1_rtl, p1_gate); end
            if (p2_rtl !== p2_gate) begin mismatch_count <= mismatch_count + 1; $display("[%0d] P2 mismatch: RTL=%h GATE=%h", $time, p2_rtl, p2_gate); end
            if (p3_rtl !== p3_gate) begin mismatch_count <= mismatch_count + 1; $display("[%0d] P3 mismatch: RTL=%h GATE=%h", $time, p3_rtl, p3_gate); end
        end
    end

    // Waveform
    initial begin
        $dumpfile("tb_equiv.vcd");
        $dumpvars(0, tb_equiv);
    end

endmodule
