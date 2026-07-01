// echo_8051_top — 8051 Microcontroller Top Level
// Reverse-engineered from anonymous gate-level netlist
// 12 sub-modules: Decoder, ALU, Control FSM, PSW, IRAM, SFR, Timer, UART, IntC, IO Ports, RegFile, PROM

module echo_8051_top (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        int0_n,
    input  wire        int1_n,
    inout  wire [7:0]  p0,
    inout  wire [7:0]  p1,
    inout  wire [7:0]  p2,
    inout  wire [7:0]  p3,
    input  wire        rxd,
    output wire        txd,
    output wire        ale,
    output wire        psen_n,
    output wire        rd_n,
    output wire        wr_n,
    input  wire        ea_n
);
    // ── Internal buses ──
    wire [7:0]  internal_bus;       // 8-bit data bus
    wire [15:0] addr_bus;           // 16-bit address

    // ── Control signals from Decoder ──
    wire [3:0]  alu_op;
    wire        acc_write, b_write, psw_write;
    wire        ram_rd, ram_wr, sfr_rd, sfr_wr;
    wire        pc_inc, pc_load, sp_inc, sp_dec;
    wire [1:0]  operand_bytes;

    // ── FSM control ──
    wire [2:0]  fsm_state;
    wire [7:0]  ctrl_bus;
    wire        exec_en;
    // fetch_en is combinational: active in FETCH(0), FETCH2(6), FETCH3(7)
    wire fetch_en = (fsm_state == 3'd0) || (fsm_state == 3'd6) || (fsm_state == 3'd7);

    // ── CPU registers ──
    reg  [7:0]  acc, b_reg;
    reg  [15:0] pc;
    reg  [7:0]  sp;
    reg  [7:0]  ir;                  // instruction register
    reg  [7:0]  op1, op2;            // operand bytes
    reg  [1:0]  byte_pos;            // 0=opcode, 1=op1, 2=op2

    // ── ALU signals ──
    wire [7:0]  alu_result;
    wire        cy, ac, ov;

    // ── PSW signals ──
    wire [2:0]  psw_flags;
    wire [7:0]  psw_val;

    // ── SFR signals ──
    wire [7:0]  sfr_rdata, p0_sfr, p1_sfr, p2_sfr, p3_sfr, sp_sfr;
    wire [15:0] dptr;
    wire [7:0]  tcon, tmod, scon, sbuf_sfr, tl0, tl1, th0, th1;
    wire [4:0]  ie, ip;

    // ── Timer signals ──
    wire        tf0, tf1;

    // ── UART signals ──
    wire        ti, ri;
    wire [7:0]  sbuf_rx;

    // ── IntC signals ──
    wire        int_active;
    wire [15:0] int_vector;

    // ── IRAM ──
    wire [7:0]  iram_rdata;

    // ── I/O ports ──
    wire [7:0]  p0_in, p1_in, p2_in, p3_in;
    wire [7:0]  p0_out, p1_out, p2_out, p3_out;

    // ════════════════════════════════════════
    // Module Instantiations
    // ════════════════════════════════════════

    // Decoder
    wire is_mov_op, use_imm, reg_rd, reg_wr, is_cy_op;
    decoder u_decoder (
        .opcode(ir), .alu_op(alu_op),
        .acc_write(acc_write), .b_write(b_write), .psw_write(psw_write),
        .ram_rd(ram_rd), .ram_wr(ram_wr), .sfr_rd(sfr_rd), .sfr_wr(sfr_wr),
        .pc_inc(pc_inc), .pc_load(pc_load), .sp_inc(sp_inc), .sp_dec(sp_dec),
        .operand_bytes(operand_bytes), .is_mov_op(is_mov_op), .use_imm(use_imm),
        .reg_rd(reg_rd), .reg_wr(reg_wr), .is_cy_op(is_cy_op)
    );

    // Register file rf_rdata — declared early for alu_a reference below
    wire [7:0] rf_rdata;

    // ALU A-input: reg file for INC/DEC Rn, otherwise ACC
    wire [7:0] alu_a = (reg_rd && ir[7:3] != 5'b11101) ? rf_rdata : acc;
    // ALU B-input: immediate for ADD/SUBB/etc A,#imm, else B register
    wire [7:0] alu_b = use_imm ? op1 : b_reg;
    alu u_alu (
        .a(alu_a), .b(alu_b), .carry_in(psw_flags[2]),
        .op(alu_op), .result(alu_result), .carry_out(cy), .aux_carry(ac), .overflow(ov)
    );

    // Control FSM
    control_fsm u_fsm (
        .clk(clk), .rst_n(rst_n),
        .opcode_valid(1'b1), .operand_bytes(operand_bytes),
        .interrupt_pending(int_active), .state(fsm_state),
        .ctrl_out(ctrl_bus), .fetch_en(), .exec_en(exec_en)
    );

    // PSW
    psw u_psw (
        .clk(clk), .rst_n(rst_n), .psw_write(psw_write),
        .flags_in({cy, ac, ov}), .flags_out(psw_flags), .psw_out(psw_val)
    );

    // IRAM — 128 bytes
    iram u_iram (
        .clk(clk), .rst_n(rst_n), .ram_rd(ram_rd), .ram_wr(ram_wr),
        .addr(addr_bus[7:0]), .wdata(internal_bus), .rdata(iram_rdata)
    );

    // SFR Block
    sfr_block u_sfr (
        .clk(clk), .rst_n(rst_n), .sfr_rd(sfr_rd), .sfr_wr(sfr_wr),
        .addr(addr_bus[7:0]), .wdata(internal_bus), .rdata(sfr_rdata),
        .p0_out(p0_sfr), .p1_out(p1_sfr), .p2_out(p2_sfr), .p3_out(p3_sfr),
        .sp_out(sp_sfr), .dptr_out(dptr), .tcon_out(tcon), .tmod_out(tmod),
        .scon_out(scon), .sbuf_out(sbuf_sfr), .ie_out(ie), .ip_out(ip),
        .tl0_out(tl0), .tl1_out(tl1), .th0_out(th0), .th1_out(th1)
    );

    // Timer
    timer u_timer (
        .clk(clk), .rst_n(rst_n), .tcon(tcon), .tmod(tmod),
        .t0_pin(p3[4]), .t1_pin(p3[5]), .tl0(tl0), .th0(th0), .tl1(tl1), .th1(th1),
        .tf0(tf0), .tf1(tf1)
    );

    // UART
    uart u_uart (
        .clk(clk), .rst_n(rst_n), .rxd(rxd), .txd(txd),
        .scon(scon), .sbuf_in(internal_bus), .sbuf_out(sbuf_rx),
        .ri(ri), .ti(ti), .baud_div({th1, tl1})
    );

    // Interrupt Controller
    intc u_intc (
        .clk(clk), .rst_n(rst_n), .ie(ie), .ip(ip),
        .int0_n(int0_n), .int1_n(int1_n), .tf0(tf0), .tf1(tf1), .ri(ri), .ti(ti),
        .int_active(int_active), .vector_addr(int_vector)
    );

    // IO Ports
    io_ports u_io (
        .clk(clk), .rst_n(rst_n),
        .p0_wr(internal_bus), .p1_wr(internal_bus), .p2_wr(internal_bus), .p3_wr(internal_bus),
        .p0_wr_en(sfr_wr && addr_bus[7:0]==8'h80), .p1_wr_en(sfr_wr && addr_bus[7:0]==8'h90),
        .p2_wr_en(sfr_wr && addr_bus[7:0]==8'hA0), .p3_wr_en(sfr_wr && addr_bus[7:0]==8'hB0),
        .p0_rd(), .p1_rd(), .p2_rd(), .p3_rd(),
        .p0_out(p0_out), .p1_out(p1_out), .p2_out(p2_out), .p3_out(p3_out),
        .p0_in(p0_in), .p1_in(p1_in), .p2_in(p2_in), .p3_in(p3_in)
    );

    // ── Bidirectional I/O pads (simplified) ──
    assign p0 = p0_out; assign p1 = p1_out; assign p2 = p2_out; assign p3 = p3_out;
    assign p0_in = p0; assign p1_in = p1; assign p2_in = p2; assign p3_in = p3;

    // ── Control outputs ──
    assign ale = 1'b0;     // simplified — no external memory
    assign psen_n = 1'b1;  // internal ROM only
    assign rd_n = 1'b1;    // no external reads
    assign wr_n = 1'b1;    // no external writes

    // ── Register File: R0-R7 (bank 0 only, 8 bytes) ──
    reg [7:0] R0, R1, R2, R3, R4, R5, R6, R7;
    wire [2:0] rf_idx = ir[2:0];
    assign rf_rdata = (rf_idx == 3'd0) ? R0 : (rf_idx == 3'd1) ? R1 :
                      (rf_idx == 3'd2) ? R2 : (rf_idx == 3'd3) ? R3 :
                      (rf_idx == 3'd4) ? R4 : (rf_idx == 3'd5) ? R5 :
                      (rf_idx == 3'd6) ? R6 : R7;

    // ── Internal data bus mux ──
    wire reg_wr_imm = reg_wr && (ir[7:3] == 5'b01111); // MOV Rn,#imm
    wire reg_wr_acc = reg_wr && (ir[7:3] == 5'b11111); // MOV Rn,A
    wire cy_active  = is_cy_op && exec_en;
    wire [7:0] cy_data = (ir == 8'hC3) ? (psw_val & 8'h7F) :
                         (ir == 8'hD3) ? (psw_val | 8'h80) :
                         (psw_val ^ 8'h80); // CPL C
    assign internal_bus = reg_rd     ? rf_rdata :
                          is_mov_op  ? op1 :
                          reg_wr_imm ? op1 :     // MOV Rn,#imm data
                          reg_wr_acc ? acc :     // MOV Rn,A data
                          cy_active  ? cy_data : // CLR/SETB/CPL C
                          ram_rd     ? iram_rdata :
                          sfr_rd     ? sfr_rdata :
                          acc_write  ? alu_result :
                          8'h00;

    // ── Address bus ──
    assign addr_bus = cy_active ? {8'h00, 8'hD0} : {8'h00, op1};

    // ── Instruction fetch ──
    reg [7:0] prom [0:4095]; // 4KB ROM

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc <= 16'h0000;
            sp <= 8'h07;
            acc <= 8'h00;
            b_reg <= 8'h00;
            ir <= 8'h00;
            op1 <= 8'h00;
            op2 <= 8'h00;
            byte_pos <= 2'd0;
            R0 <= 8'h00; R1 <= 8'h00; R2 <= 8'h00; R3 <= 8'h00;
            R4 <= 8'h00; R5 <= 8'h00; R6 <= 8'h00; R7 <= 8'h00;
        end else begin
            // byte_pos: reset at FETCH (blocking, so fetch sees correct value)
            if (fsm_state == 3'd0) byte_pos = 2'd0;
            else if (fetch_en) byte_pos = byte_pos + 2'd1;

            // fetch_en is combinational: only high during FETCH(0), FETCH2(6), FETCH3(7)
            // byte_pos: 0=FETCH (ir+op1 pre-fetch), 1=FETCH2 (op2 pre-fetch), 2=FETCH3 (op2)
            if (fetch_en) begin
                if (byte_pos == 2'd0) begin
                    ir <= prom[pc];
                    op1 <= prom[pc + 16'd1]; // pre-fetch operand
                end else if (byte_pos == 2'd1) begin
                    // op1 already pre-fetched in FETCH — don't overwrite
                    op2 <= prom[pc + 16'd1]; // pre-fetch 3rd byte
                end else begin
                    op2 <= prom[pc]; // actual 3rd byte
                end
                if (pc_inc) pc <= pc + 16'd1;
            end
            // pc_load during exec (SJMP/LJMP etc) — outside fetch_en block
            if (pc_load && exec_en) begin
                if (ir == 8'h80) pc <= pc + {{8{op1[7]}}, op1}; // SJMP relative
                else pc <= {op1, op2}; // LJMP/LCALL absolute
            end
            if (sp_inc) sp <= sp + 8'd1;
            if (sp_dec) sp <= sp - 8'd1;
            if (exec_en) begin
                if (acc_write) acc <= internal_bus;
                if (b_write)   b_reg <= internal_bus;
                if (reg_wr) begin
                    case (ir[2:0])
                        3'd0: R0 <= internal_bus;
                        3'd1: R1 <= internal_bus;
                        3'd2: R2 <= internal_bus;
                        3'd3: R3 <= internal_bus;
                        3'd4: R4 <= internal_bus;
                        3'd5: R5 <= internal_bus;
                        3'd6: R6 <= internal_bus;
                        3'd7: R7 <= internal_bus;
                    endcase
                end
            end
        end
    end

    // ── ROM initialization ──
    integer i;
    initial begin
        for (i = 0; i < 4096; i = i + 1) prom[i] = 8'h00;
        prom[0]=8'h74; prom[1]=8'h42; prom[2]=8'h78; prom[3]=8'h55;
        prom[4]=8'h79; prom[5]=8'h33; prom[6]=8'hE8;
        prom[7]=8'h24; prom[8]=8'h20; prom[9]=8'hC3;
        prom[10]=8'h94; prom[11]=8'h25; prom[12]=8'h54; prom[13]=8'h0F;
        prom[14]=8'h44; prom[15]=8'hAA; prom[16]=8'h64; prom[17]=8'h55;
        prom[18]=8'h04; prom[19]=8'h14; prom[20]=8'h04; prom[21]=8'h04; prom[22]=8'h04;
        prom[23]=8'hC4; prom[24]=8'hF4; prom[25]=8'hE4;
        prom[26]=8'h74; prom[27]=8'h0A; prom[28]=8'h75; prom[29]=8'hF0; prom[30]=8'h06;
        prom[31]=8'hA4; prom[32]=8'hF5; prom[33]=8'h90;
        prom[34]=8'h74; prom[35]=8'h0F; prom[36]=8'h75; prom[37]=8'hF0; prom[38]=8'h04;
        prom[39]=8'h84; prom[40]=8'hF5; prom[41]=8'hA0;
        prom[42]=8'h78; prom[43]=8'h03; prom[44]=8'hE4; prom[45]=8'h04;
        prom[46]=8'hD8; prom[47]=8'hFD; prom[48]=8'hF5; prom[49]=8'hB0;
        prom[50]=8'hC0; prom[51]=8'hE0; prom[52]=8'hE4;
        prom[53]=8'hD0; prom[54]=8'hE0; prom[55]=8'hF5; prom[56]=8'h80;
        prom[57]=8'hD3; prom[58]=8'hC3; prom[59]=8'hB3; prom[60]=8'h80; prom[61]=8'hFE;
        $display("Crossval program loaded: 62 bytes");
    end

endmodule
