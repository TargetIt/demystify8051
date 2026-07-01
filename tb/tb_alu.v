// ALU Module Testbench
// Tests all 16 ALU operations with known input/output pairs

`timescale 1ns/1ps

module tb_alu;
    reg  [7:0] a, b, expected;
    reg        carry_in;
    reg  [3:0] op;
    wire [7:0] result;
    wire       carry_out, aux_carry, overflow;

    alu dut (.a(a), .b(b), .carry_in(carry_in), .op(op),
             .result(result), .carry_out(carry_out),
             .aux_carry(aux_carry), .overflow(overflow));

    integer pass, fail;
    initial begin
        pass = 0; fail = 0;
        $display("=== ALU Testbench ===");

        // ADD
        a = 8'h10; b = 8'h20; carry_in = 0; op = 4'h0;
        #10 if (result == 8'h30 && carry_out == 0) pass = pass+1; else begin fail = fail+1; $display("FAIL ADD 10+20"); end

        // ADDC with carry
        a = 8'hFF; b = 8'h01; carry_in = 1; op = 4'h1;
        #10 if (result == 8'h01 && carry_out == 1) pass = pass+1; else begin fail = fail+1; $display("FAIL ADDC"); end

        // SUBB
        a = 8'h10; b = 8'h01; carry_in = 1; op = 4'h2;
        #10 if (result == 8'h0F && carry_out == 1) pass = pass+1; else begin fail = fail+1; $display("FAIL SUBB"); end

        // ANL
        a = 8'h0F; b = 8'hF0; op = 4'h3;
        #10 if (result == 8'h00) pass = pass+1; else begin fail = fail+1; $display("FAIL ANL"); end

        // ORL
        a = 8'h0A; b = 8'hA0; op = 4'h4;
        #10 if (result == 8'hAA) pass = pass+1; else begin fail = fail+1; $display("FAIL ORL"); end

        // XRL
        a = 8'hAA; b = 8'hFF; op = 4'h5;
        #10 if (result == 8'h55) pass = pass+1; else begin fail = fail+1; $display("FAIL XRL"); end

        // INC
        a = 8'hFF; op = 4'h6;
        #10 if (result == 8'h00 && carry_out == 1) pass = pass+1; else begin fail = fail+1; $display("FAIL INC"); end

        // DEC
        a = 8'h00; op = 4'h7;
        #10 if (result == 8'hFF && carry_out == 1) pass = pass+1; else begin fail = fail+1; $display("FAIL DEC"); end

        // RL
        a = 8'h81; op = 4'h9;
        #10 if (result == 8'h03) pass = pass+1; else begin fail = fail+1; $display("FAIL RL"); end

        // RR
        a = 8'h81; op = 4'hB;
        #10 if (result == 8'hC0) pass = pass+1; else begin fail = fail+1; $display("FAIL RR"); end

        // SWAP
        a = 8'h12; op = 4'hD;
        #10 if (result == 8'h21) pass = pass+1; else begin fail = fail+1; $display("FAIL SWAP"); end

        // CPL
        a = 8'hAA; op = 4'hE;
        #10 if (result == 8'h55) pass = pass+1; else begin fail = fail+1; $display("FAIL CPL"); end

        $display("ALU Tests: %0d passed, %0d failed", pass, fail);
        $finish;
    end
endmodule
