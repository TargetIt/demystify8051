// Decoder — 8051 Instruction Decoder
// Reverse-engineered: 242 mux4_2 cells → 7-bit IR → 559 control signals
// Groups opcodes by instruction class and generates control signals

module decoder (
    input  wire [7:0]  opcode,           // 8-bit opcode (only 7 used: bits 6-0)
    output wire [3:0]  alu_op,           // ALU operation select
    output wire        acc_write,        // write enable for ACC
    output wire        b_write,          // write enable for B register
    output wire        psw_write,        // write enable for PSW
    output wire        ram_rd,           // internal RAM read
    output wire        ram_wr,           // internal RAM write
    output wire        sfr_rd,           // SFR read
    output wire        sfr_wr,           // SFR write
    output wire        pc_inc,           // increment PC
    output wire        pc_load,          // load PC (jump/call)
    output wire        sp_inc,           // increment stack pointer
    output wire        sp_dec,           // decrement stack pointer
    output wire [1:0]  operand_bytes,    // number of extra bytes to fetch (0,1,2)
    output wire        is_mov_op,        // high when MOV/move operation (not ALU)
    output wire        use_imm,          // ALU B-input = immediate (op1) instead of B register
    output wire        reg_rd,           // read R0-R7 register file
    output wire        reg_wr,           // write R0-R7 register file
    output wire        is_cy_op,         // CLR C / SETB C / CPL C
    output wire        is_djnz           // DJNZ Rn,rel
);
    wire [6:0] ir = opcode[6:0]; // 7-bit instruction register

    // Decode by opcode groups (derived from mux4_2 tree analysis)
    // ADD: 0x24-0x2F (opcode[7:4]=0010)
    wire is_add  = (opcode[7:4] == 4'b0010) && (opcode[3:0] <= 4'hF);
    wire is_addc = (ir[6:0] == 7'h35) || (ir[6:0] == 7'h36) || (ir[6:0] == 7'h37);
    wire is_subb = (ir[6:0] == 7'h95) || (ir[6:0] == 7'h96) || (ir[6:0] == 7'h97)
                || (opcode[7:0] == 8'h94)  // SUBB A,#imm
                || (ir[7:3] == 5'b10011);   // SUBB A,Rn (98-9F)
    // ANL: 0x54(#imm), 0x55(direct), 0x56-57(@Ri), 0x58-5F(Rn)
    wire is_anl  = (opcode[7:4] == 4'b0101) && (opcode[3:0] <= 4'hF);
    // ORL: 0x44(#imm), 0x45(direct), 0x46-47(@Ri), 0x48-4F(Rn)
    wire is_orl  = (opcode[7:4] == 4'b0100) && (opcode[3:0] <= 4'hF);
    // XRL: 0x64(#imm), 0x65(direct), 0x66-67(@Ri), 0x68-6F(Rn)
    wire is_xrl  = (opcode[7:4] == 4'b0110) && (opcode[3:0] <= 4'hF);
    // MOV instructions that access IRAM or SFR (not register-only)
    wire is_mov_mem = (opcode[7:0] == 8'h74)  // MOV A,#imm: internal_bus needs op1
                   || (opcode[7:0] == 8'hE5)  // MOV A,direct
                   || (opcode[7:0] == 8'hF5)  // MOV direct,A
                   || (opcode[7:0] == 8'h85)  // MOV direct,direct
                   || (opcode[7:0] == 8'h75)  // MOV direct,#imm
                   || (opcode[7:0] == 8'h76) || (opcode[7:0] == 8'h77)  // MOV @Ri,#imm
                   || (opcode[7:0] == 8'hA6) || (opcode[7:0] == 8'hA7)  // MOV @Ri,direct
                   || (opcode[7:0] == 8'h86) || (opcode[7:0] == 8'h87)  // MOV direct,@Ri
                   || (opcode[7:0] == 8'hE6) || (opcode[7:0] == 8'hE7)  // MOV A,@Ri
                   || (opcode[7:0] == 8'hF6) || (opcode[7:0] == 8'hF7)  // MOV @Ri,A
                   || (opcode[7:0] == 8'h90)  // MOV DPTR,#imm16
                   || (opcode[7:3] == 5'b01111); // MOV Rn,#imm (78-7F)
    // Legacy is_mov kept for acc_write compatibility — but we use is_mov_op instead now
    wire is_mov  = is_mov_mem;
    wire is_movx = (ir[6:0] == 7'hE0) || (ir[6:0] == 7'hE2) || (ir[6:0] == 7'hE3);
    wire is_push = (ir[6:0] == 7'hC0);
    wire is_pop  = (ir[6:0] == 7'hD0);
    // AJMP: aaa00001, JMP @A+DPTR: 73, LJMP: 02
    wire is_sjmp = (opcode[7:0] == 8'h80);
    wire is_ajmp = (opcode[4:0] == 5'b00001) && (opcode[7:5] != 3'b000);
    wire is_jmp  = is_ajmp || (opcode[7:0] == 8'h73) || (opcode[7:0] == 8'h02) || is_sjmp;
    assign is_djnz = (opcode[7:4] == 4'hD) && (opcode[3:0] >= 4'h8) && (opcode[3:0] <= 4'hF); // DJNZ Rn,rel (D8-DF)
    wire is_call = (ir[6:5] == 2'b00) && (ir[4:0] == 5'b10001) || (ir[6:0] == 7'h12);
    wire is_ret  = (ir[6:0] == 7'h22);
    wire is_reti = (ir[6:0] == 7'h32);
    wire is_mul  = (opcode[7:0] == 8'hA4);
    wire is_div  = (opcode[7:0] == 8'h84);
    wire is_da   = (opcode[7:0] == 8'hD4);
    // INC: 0x04(A), 0x05(dir), 0x06-07(@Ri), 0x08-0F(Rn)
    wire is_inc  = (opcode[7:4] == 4'b0000) && (opcode[3:0] != 4'h0);
    // DEC: 0x14(A), 0x15(dir), 0x16-17(@Ri), 0x18-1F(Rn)
    wire is_dec  = (opcode[7:4] == 4'b0001) && (opcode[3:0] != 4'h0);
    wire is_rl   = (opcode[7:0] == 8'h23);
    wire is_rlc  = (opcode[7:0] == 8'h33);
    wire is_rr   = (opcode[7:0] == 8'h03);
    wire is_rrc  = (opcode[7:0] == 8'h13);
    wire is_swap = (opcode[7:0] == 8'hC4);
    wire is_cpl  = (opcode[7:0] == 8'hF4);
    wire is_clr  = (opcode[7:0] == 8'hE4);

    // ALU operation encoding
    assign alu_op = is_add  ? 4'h0 : is_addc ? 4'h1 : is_subb ? 4'h2 :
                    is_anl  ? 4'h3 : is_orl  ? 4'h4 : is_xrl  ? 4'h5 :
                    is_inc  ? 4'h6 : (is_dec || is_djnz) ? 4'h7 : is_da ? 4'h8 :
                    is_rl   ? 4'h9 : is_rlc  ? 4'hA : is_rr   ? 4'hB :
                    is_rrc  ? 4'hC : is_swap ? 4'hD : is_cpl  ? 4'hE :
                    is_clr  ? 4'hF : 4'h0;  // default: ADD (NOP)

    // Memory and SFR control (exclude register-only operations)
    wire is_mem_op = is_mov && !reg_rd && !reg_wr; // MOV to/from IRAM/SFR only
    assign ram_rd = is_mem_op || is_pop;
    assign ram_wr = is_mem_op || is_push;
    assign sfr_rd = is_mem_op || is_push;
    assign sfr_wr = is_mem_op || is_pop;
    // is_cy_op triggers sfr_wr through the top-level addr_bus mux instead

    // Register writes
    assign acc_write = is_add || is_addc || is_subb || is_anl || is_orl || is_xrl ||
                       is_inc || is_dec || is_da || is_rl || is_rlc || is_rr || is_rrc ||
                       is_swap || is_cpl || is_clr || is_mov_op || is_mul || is_div ||
                       is_pop || (opcode[7:3] == 5'b11101); // MOV A,Rn
    assign b_write = is_mul || is_div;
    assign psw_write = is_add || is_addc || is_subb || is_mul || is_div || is_da
                     || (opcode[7:0] == 8'hC3) || (opcode[7:0] == 8'hD3) || (opcode[7:0] == 8'hB3);
    // CLR C (C3), SETB C (D3), CPL C (B3)
    wire is_clr_c  = (opcode[7:0] == 8'hC3);
    wire is_setb_c = (opcode[7:0] == 8'hD3);
    wire is_cpl_c  = (opcode[7:0] == 8'hB3);
    assign is_cy_op = is_clr_c || is_setb_c || is_cpl_c;

    // Program flow
    assign pc_inc  = 1'b1; // PC increments during fetch
    assign pc_load = is_jmp || is_call || is_ret || is_reti || is_djnz;
    assign sp_inc  = is_push || is_call;
    assign sp_dec  = is_pop || is_ret || is_reti;

    // Operand bytes to fetch (after opcode)
    // Default 2'd0 = 1-byte instruction (most common)
    wire is_2byte = (is_mov && opcode[7:4] == 4'h7 && opcode[3:0] <= 4'h7)  // MOV Rn,#imm
                 || is_push || is_pop
                 || (is_anl && opcode == 8'h82) || (is_anl && opcode == 8'hB0)  // ANL C,bit
                 || (is_orl && opcode == 8'h72) || (is_orl && opcode == 8'hA0)  // ORL C,bit
                 || (opcode[7:0] == 8'hA2) || (opcode[7:0] == 8'h92)  // MOV C/bit
                 || (opcode[7:0] == 8'hC2) || (opcode[7:0] == 8'hD2) || (opcode[7:0] == 8'hB2)  // CLR/SETB/CPL bit
                 || (opcode[7:0] == 8'h80)  // SJMP
                 || (opcode[7:4] == 4'h4 && opcode[3:0] <= 4'hF)  // JC/JNC/JZ/JNZ
                 || (opcode[7:0] == 8'h74)  // MOV A,#imm
                 || (opcode[7:0] == 8'h24) || (opcode[7:0] == 8'h34)  // ADD/ADDC A,#imm
                 || (opcode[7:0] == 8'h94)  // SUBB A,#imm
                 || (opcode[7:0] == 8'h54) || (opcode[7:0] == 8'h44) || (opcode[7:0] == 8'h64)  // ANL/ORL/XRL A,#imm
                 || (opcode[7:0] == 8'hE5) || (opcode[7:0] == 8'hF5)  // MOV A,direct; MOV direct,A
                 || (opcode[7:0] == 8'hC5)  // XCH A,direct
                 || (opcode[7:0] == 8'h05) || (opcode[7:0] == 8'h15)  // INC/DEC direct
                 || (opcode[7:0] == 8'h25) || (opcode[7:0] == 8'h35)  // ADD/ADDC A,direct
                 || (opcode[7:0] == 8'h45) || (opcode[7:0] == 8'h55) || (opcode[7:0] == 8'h65)  // ORL/ANL/XRL A,direct
                 || (opcode[7:0] == 8'h95)  // SUBB A,direct
                 || (opcode[7:0] == 8'h76) || (opcode[7:0] == 8'h77)  // MOV @Ri,#imm
                 || (opcode[7:0] == 8'hA6) || (opcode[7:0] == 8'hA7)  // MOV @Ri,direct
                 || (opcode[7:0] == 8'h86) || (opcode[7:0] == 8'h87)  // MOV direct,@Ri
                 || (opcode[7:4] == 4'hD && (opcode[3:0] >= 4'h8))  // DJNZ Rn,rel
                 || (opcode[7:0] == 8'hD5)  // DJNZ direct,rel
                 || (opcode[7:3] == 5'b10001)  // ACALL
                 || (opcode[7:5] == 3'b000 && opcode[4:0] == 5'b00001)  // AJMP
                 || (opcode[7:0] == 8'hC0) || (opcode[7:0] == 8'hD0); // PUSH/POP direct
    wire is_3byte = (opcode[7:0] == 8'h75)  // MOV direct,#imm
                 || (opcode[7:0] == 8'h85)  // MOV direct,direct
                 || (opcode[7:0] == 8'h02)  // LJMP
                 || (opcode[7:0] == 8'h12)  // LCALL
                 || (opcode[7:0] == 8'h90)  // MOV DPTR,#imm16
                 || (opcode[7:0] == 8'hB4) || (opcode[7:0] == 8'hB5)  // CJNE A,#imm/direct,rel
                 || (opcode[7:0] == 8'hB6) || (opcode[7:0] == 8'hB7)  // CJNE @Ri,#imm,rel
                 || (opcode[7:4] == 4'hB && (opcode[3:0] >= 4'h8))  // CJNE Rn,#imm,rel
                 || (opcode[7:0] == 8'hD5)  // DJNZ direct,rel
                 || (opcode[7:0] == 8'h10) || (opcode[7:0] == 8'h20) || (opcode[7:0] == 8'h30)  // JBC/JB/JNB bit,rel
                 || (opcode[7:0] == 8'h43) || (opcode[7:0] == 8'h53) || (opcode[7:0] == 8'h63); // ORL/ANL/XRL direct,#imm
    assign operand_bytes = is_3byte ? 2'd2 : is_2byte ? 2'd1 : 2'd0;

    // MOV-to-ACC via immediate: data goes to ACC via op1
    wire is_mov_imm  = (opcode[7:0] == 8'h74);  // MOV A,#imm
    wire is_mov_a_dir = (opcode[7:0] == 8'hE5);  // MOV A,direct
    wire is_mov_a_ri  = (opcode[7:0] == 8'hE6) || (opcode[7:0] == 8'hE7); // MOV A,@Ri
    assign is_mov_op = is_mov_imm || is_mov_a_dir || is_mov_a_ri;
    // Note: MOV A,Rn uses reg_rd (register file) not is_mov_op

    // ALU immediate: ADD/ADDC/SUBB/ANL/ORL/XRL A,#imm
    assign use_imm = (opcode[7:0] == 8'h24) || (opcode[7:0] == 8'h34) ||  // ADD/ADDC A,#imm
                     (opcode[7:0] == 8'h94) ||  // SUBB A,#imm
                     (opcode[7:0] == 8'h54) || (opcode[7:0] == 8'h44) || (opcode[7:0] == 8'h64);
                     // ANL/ORL/XRL A,#imm

    // Register file access: Rn in ir[2:0]
    wire is_mov_rn_a  = (opcode[7:3] == 5'b11101);  // MOV A,Rn (E8-EF)
    wire is_mov_a_rn  = (opcode[7:3] == 5'b11111);  // MOV Rn,A (F8-FF)
    wire is_mov_rn_imm= (opcode[7:3] == 5'b01111);  // MOV Rn,#imm (78-7F)
    wire is_inc_rn    = (opcode[7:3] == 5'b00001);  // INC Rn (08-0F)
    wire is_dec_rn    = (opcode[7:3] == 5'b00011);  // DEC Rn (18-1F)
    wire is_djnz_rn   = (opcode[7:4] == 4'hD && opcode[3:0] >= 4'h8); // DJNZ Rn,rel (D8-DF)
    assign reg_rd = is_mov_rn_a || is_inc_rn || is_dec_rn || is_djnz_rn;
    // is_mov_a_rn excluded: MOV Rn,A writes ACC to Rn (source is ACC, not reg file)
    assign reg_wr = is_mov_a_rn || is_mov_rn_imm || is_inc_rn || is_dec_rn || is_djnz_rn;
endmodule
