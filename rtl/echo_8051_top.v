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
    wire        fetch_en, exec_en;

    // ── CPU registers ──
    reg  [7:0]  acc, b_reg;
    reg  [15:0] pc;
    reg  [7:0]  sp;
    reg  [7:0]  ir;                  // instruction register

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
    decoder u_decoder (
        .opcode(ir), .alu_op(alu_op),
        .acc_write(acc_write), .b_write(b_write), .psw_write(psw_write),
        .ram_rd(ram_rd), .ram_wr(ram_wr), .sfr_rd(sfr_rd), .sfr_wr(sfr_wr),
        .pc_inc(pc_inc), .pc_load(pc_load), .sp_inc(sp_inc), .sp_dec(sp_dec),
        .operand_bytes(operand_bytes)
    );

    // ALU
    alu u_alu (
        .a(acc), .b(b_reg), .carry_in(psw_flags[2]),
        .op(alu_op), .result(alu_result), .carry_out(cy), .aux_carry(ac), .overflow(ov)
    );

    // Control FSM
    control_fsm u_fsm (
        .clk(clk), .rst_n(rst_n),
        .opcode_valid(1'b1), .operand_bytes(operand_bytes),
        .interrupt_pending(int_active), .state(fsm_state),
        .ctrl_out(ctrl_bus), .fetch_en(fetch_en), .exec_en(exec_en)
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
        .p0_rd(internal_bus), .p1_rd(internal_bus), .p2_rd(internal_bus), .p3_rd(internal_bus),
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

    // ── Internal data bus mux ──
    assign internal_bus = ram_rd ? iram_rdata :
                          sfr_rd ? sfr_rdata :
                          acc_write ? alu_result :
                          8'h00;

    // ── Address bus ──
    assign addr_bus = dptr; // simplified — use DPTR for address

    // ── Instruction fetch (simplified) ──
    reg [7:0] prom [0:4095]; // 4KB ROM (behavioral, not in gate netlist)

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            pc <= 16'h0000;
            sp <= 8'h07;
            acc <= 8'h00;
            b_reg <= 8'h00;
            ir <= 8'h00;
        end else begin
            if (fetch_en) begin
                ir <= prom[pc]; // fetch opcode from ROM
                if (pc_inc) pc <= pc + 16'd1;
                if (pc_load && exec_en) begin
                    if (int_active) pc <= int_vector;
                    else pc <= addr_bus; // jump/call target
                end
            end
            if (sp_inc) sp <= sp + 8'd1;
            if (sp_dec) sp <= sp - 8'd1;
            if (acc_write && exec_en) acc <= alu_result;
            if (b_write && exec_en) b_reg <= alu_result;
        end
    end

    // ── ROM initialization ──
    // Load from Intel HEX via simple parser
    integer fd, i, addr, byte_val, rec_type, rec_len;
    reg [7:0] hex_bytes [0:255];
    initial begin
        // Default: fill with NOP (0x00) — many 8051 tools emit 0x00 for unused
        for (i = 0; i < 4096; i = i + 1) prom[i] = 8'h00;
        // Try loading hex file
        fd = $fopen("tb/isa_tests/smoke_test.hex", "r");
        if (fd) begin
            while (!$feof(fd)) begin
                $fscanf(fd, ":%2h%4h%2h", rec_len, addr, rec_type);
                if (rec_type == 8'h00) begin
                    for (i = 0; i < rec_len; i = i + 1) begin
                        $fscanf(fd, "%2h", byte_val);
                        prom[addr+i] = byte_val;
                    end
                end
                $fscanf(fd, "%*2h\n"); // skip checksum
            end
            $fclose(fd);
            $display("Loaded %0d bytes from smoke_test.hex", addr + rec_len);
        end else begin
            $display("WARNING: Could not open smoke_test.hex — ROM filled with NOPs");
        end
    end

endmodule
