// Decoder Module Testbench
// Tests opcode→control signal mapping for key 8051 instructions

`timescale 1ns/1ps

module tb_decoder;
    reg  [7:0] opcode;
    wire [3:0] alu_op;
    wire       acc_write, psw_write, ram_rd, ram_wr, sfr_rd, sfr_wr;
    wire       pc_inc, pc_load, sp_inc, sp_dec, b_write;
    wire [1:0] operand_bytes;

    decoder dut (.opcode(opcode), .alu_op(alu_op),
                 .acc_write(acc_write), .b_write(b_write), .psw_write(psw_write),
                 .ram_rd(ram_rd), .ram_wr(ram_wr), .sfr_rd(sfr_rd), .sfr_wr(sfr_wr),
                 .pc_inc(pc_inc), .pc_load(pc_load), .sp_inc(sp_inc), .sp_dec(sp_dec),
                 .operand_bytes(operand_bytes));

    integer pass, fail;
    reg [7:0] test_cases [0:15];
    reg [3:0] expected_alu [0:15];
    reg       expected_acc [0:15], expected_psw [0:15];

    initial begin
        pass = 0; fail = 0;
        $display("=== Decoder Testbench ===");

        // ADD A, Rn (opcode 0x28-0x2F)
        opcode = 8'h28; // ADD A, R0
        #10;
        if (alu_op == 4'h0 && acc_write && psw_write) pass = pass+1;
        else begin fail = fail+1; $display("FAIL ADD A,R0: alu=%h acc=%b psw=%b", alu_op, acc_write, psw_write); end

        // SUBB A, Rn (opcode 0x98-0x9F)
        opcode = 8'h98; // SUBB A, R0
        #10;
        if (alu_op == 4'h2 && acc_write && psw_write) pass = pass+1;
        else begin fail = fail+1; $display("FAIL SUBB A,R0"); end

        // ANL A, Rn (opcode 0x58-0x5F)
        opcode = 8'h58;
        #10;
        if (alu_op == 4'h3 && acc_write) pass = pass+1;
        else begin fail = fail+1; $display("FAIL ANL A,Rn"); end

        // MOV A, #data (opcode 0x74)
        opcode = 8'h74;
        #10;
        if (acc_write && operand_bytes == 2'd1) pass = pass+1;
        else begin fail = fail+1; $display("FAIL MOV A,#data"); end

        // MOV direct, direct (opcode 0x85)
        opcode = 8'h85;
        #10;
        if (ram_wr && operand_bytes == 2'd2) pass = pass+1;
        else begin fail = fail+1; $display("FAIL MOV dir,dir"); end

        // PUSH (opcode 0xC0)
        opcode = 8'hC0;
        #10;
        if (sp_inc && sfr_rd) pass = pass+1;
        else begin fail = fail+1; $display("FAIL PUSH"); end

        // POP (opcode 0xD0)
        opcode = 8'hD0;
        #10;
        if (sp_dec && sfr_wr) pass = pass+1;
        else begin fail = fail+1; $display("FAIL POP"); end

        // LJMP (opcode 0x02)
        opcode = 8'h02;
        #10;
        if (pc_load && operand_bytes == 2'd2) pass = pass+1;
        else begin fail = fail+1; $display("FAIL LJMP"); end

        // MUL AB (opcode 0xA4)
        opcode = 8'hA4;
        #10;
        if (b_write && psw_write) pass = pass+1;
        else begin fail = fail+1; $display("FAIL MUL AB"); end

        // SWAP A (opcode 0xC4)
        opcode = 8'hC4;
        #10;
        if (alu_op == 4'hD && acc_write) pass = pass+1;
        else begin fail = fail+1; $display("FAIL SWAP A"); end

        $display("Decoder Tests: %0d passed, %0d failed", pass, fail);
        $finish;
    end
endmodule
