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
    output wire [1:0]  operand_bytes     // number of extra bytes to fetch (0,1,2)
);
    wire [6:0] ir = opcode[6:0]; // 7-bit instruction register

    // Decode by opcode groups (derived from mux4_2 tree analysis)
    wire is_add  = (ir[6:4] == 3'b001) && (ir[3:0] <= 4'hF);
    wire is_addc = (ir[6:0] == 7'h35) || (ir[6:0] == 7'h36) || (ir[6:0] == 7'h37);
    wire is_subb = (ir[6:0] == 7'h95) || (ir[6:0] == 7'h96) || (ir[6:0] == 7'h97);
    wire is_anl  = (ir[6:3] == 4'b0101);
    wire is_orl  = (ir[6:3] == 4'b0100);
    wire is_xrl  = (ir[6:3] == 4'b0110);
    wire is_mov  = (ir[6:5] == 2'b11) || (ir[6:3] == 4'b0111);
    wire is_movx = (ir[6:0] == 7'hE0) || (ir[6:0] == 7'hE2) || (ir[6:0] == 7'hE3);
    wire is_push = (ir[6:0] == 7'hC0);
    wire is_pop  = (ir[6:0] == 7'hD0);
    wire is_jmp  = (ir[6:5] == 2'b00) && (ir[4:3] != 2'b00);
    wire is_call = (ir[6:5] == 2'b00) && (ir[4:0] == 5'b10001) || (ir[6:0] == 7'h12);
    wire is_ret  = (ir[6:0] == 7'h22);
    wire is_reti = (ir[6:0] == 7'h32);
    wire is_mul  = (ir[6:0] == 7'hA4);
    wire is_div  = (ir[6:0] == 7'h84);
    wire is_da   = (ir[6:0] == 7'hD4);
    wire is_inc  = (ir[6:3] == 4'b0000) && (ir[2:0] != 3'b000);
    wire is_dec  = (ir[6:3] == 4'b0001);
    wire is_rl   = (ir[6:0] == 7'h23);
    wire is_rlc  = (ir[6:0] == 7'h33);
    wire is_rr   = (ir[6:0] == 7'h03);
    wire is_rrc  = (ir[6:0] == 7'h13);
    wire is_swap = (ir[6:0] == 7'hC4);
    wire is_cpl  = (ir[6:0] == 7'hF4);
    wire is_clr  = (ir[6:0] == 7'hE4);

    // ALU operation encoding
    assign alu_op = is_add  ? 4'h0 : is_addc ? 4'h1 : is_subb ? 4'h2 :
                    is_anl  ? 4'h3 : is_orl  ? 4'h4 : is_xrl  ? 4'h5 :
                    is_inc  ? 4'h6 : is_dec  ? 4'h7 : is_da   ? 4'h8 :
                    is_rl   ? 4'h9 : is_rlc  ? 4'hA : is_rr   ? 4'hB :
                    is_rrc  ? 4'hC : is_swap ? 4'hD : is_cpl  ? 4'hE :
                    is_clr  ? 4'hF : 4'h0;  // default: ADD (NOP)

    // Memory and SFR control
    assign ram_rd = is_mov || is_pop;
    assign ram_wr = is_mov || is_push;
    assign sfr_rd = is_mov || is_push;
    assign sfr_wr = is_mov || is_pop;

    // Register writes
    assign acc_write = is_add || is_addc || is_subb || is_anl || is_orl || is_xrl ||
                       is_inc || is_dec || is_da || is_rl || is_rlc || is_rr || is_rrc ||
                       is_swap || is_cpl || is_mov;
    assign b_write = is_mul || is_div;
    assign psw_write = is_add || is_addc || is_subb || is_mul || is_div || is_da;

    // Program flow
    assign pc_inc  = 1'b1; // PC increments every instruction
    assign pc_load = is_jmp || is_call || is_ret || is_reti;
    assign sp_inc  = is_push;
    assign sp_dec  = is_pop || is_ret || is_reti;

    // Operand bytes to fetch (after opcode)
    assign operand_bytes = (is_jmp && ir[4:3] == 2'b10) ? 2'd2 : // LJMP/LCALL: 2 bytes
                           (is_mov && ir[7:4] != 4'h7) ? 2'd2 :   // MOV direct,direct: 2 bytes
                           (ir[6:0] == 7'hE0 || ir[6:0] == 7'hE2 || ir[6:0] == 7'hE3) ? 2'd0 : // MOVX: 0 extra
                           (is_mov && ir[3:0] <= 4'h7 && ir[7:4] >= 4'h7) ? 2'd1 : // MOV A,#data: 1 byte
                           (is_jmp || is_call) ? 2'd2 : 2'd1; // default: 1 operand byte

endmodule
