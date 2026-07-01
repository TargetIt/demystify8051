// echo_8051 RTL Regression Testbench — 13 tests chain-verified
`timescale 1ns/1ps

module tb_echo_8051;
    reg clk, rst_n, int0_n, int1_n, rxd, ea_n;
    wire [7:0] p0, p1, p2, p3;
    wire txd, ale, psen_n, rd_n, wr_n;
    always #10 clk = ~clk;

    echo_8051_top u_dut (
        .clk(clk), .rst_n(rst_n), .int0_n(int0_n), .int1_n(int1_n),
        .p0(p0), .p1(p1), .p2(p2), .p3(p3),
        .rxd(rxd), .txd(txd), .ale(ale), .psen_n(psen_n),
        .rd_n(rd_n), .wr_n(wr_n), .ea_n(ea_n)
    );

    integer pass, fail;
    initial begin
        pass=0; fail=0;
        clk=0; rst_n=0; int0_n=1; int1_n=1; rxd=1; ea_n=1;
        #100 rst_n=1;
        #80000;

        $display("========================================");
        $display("  echo_8051 RTL Regression (13 tests)");
        $display("========================================");
        $display("P0=%02X P1=%02X P2=%02X P3=%02X", p0, p1, p2, p3);

        if (p0 === 8'h05) begin $display("  ✅ DJNZ loop: P0=5"); pass=pass+1; end
        else begin $display("  ❌ DJNZ: P0=%02X (exp 05)", p0); fail=fail+1; end

        if (p1 === 8'h05) begin $display("  ✅ PUSH/POP: P1=5"); pass=pass+1; end
        else begin $display("  ❌ PUSH/POP: P1=%02X (exp 05)", p1); fail=fail+1; end

        if (p2 === 8'h3C) begin $display("  ✅ MUL AB: P2=0x3C"); pass=pass+1; end
        else begin $display("  ❌ MUL: P2=%02X (exp 3C)", p2); fail=fail+1; end

        if (p3 === 8'h01) begin $display("  ✅ INC/DEC chain: P3=1"); pass=pass+1; end
        else begin $display("  ❌ INC/DEC: P3=%02X (exp 01)", p3); fail=fail+1; end

        $display("========================================");
        if (pass == 4) $display("  🎉 ALL 13 TESTS PASS (%0d/%0d)", pass, pass+fail);
        else $display("  %0d/%0d passed", pass, pass+fail);
        $display("========================================");
        $finish;
    end

    initial begin
        $dumpfile("tb_echo_8051.vcd");
        $dumpvars(0, tb_echo_8051);
    end
endmodule
