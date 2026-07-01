// SFR Block — Special Function Register Block
// Contains all 21 SFRs mapped at addresses 0x80-0xFF
// Reverse-engineered: ~48 8-bit registers (dfrtp + dfstp), address decoder

module sfr_block (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        sfr_rd,
    input  wire        sfr_wr,
    input  wire [7:0]  addr,         // SFR address (0x80-0xFF)
    input  wire [7:0]  wdata,        // write data from internal bus
    output reg  [7:0]  rdata,        // read data to internal bus
    // Direct outputs for key SFRs
    output wire [7:0]  p0_out, p1_out, p2_out, p3_out,
    output wire [7:0]  sp_out,       // stack pointer
    output wire [15:0] dptr_out,     // data pointer
    output wire [7:0]  tcon_out, tmod_out,
    output wire [7:0]  scon_out, sbuf_out,
    output wire [4:0]  ie_out, ip_out,
    // Timer data
    output wire [7:0]  tl0_out, tl1_out, th0_out, th1_out
);
    // SFR registers
    reg [7:0] p0, p1, p2, p3;
    reg [7:0] sp;
    reg [7:0] dpl, dph;
    reg [4:0] pcon;     // only 5 bits used
    reg [7:0] tcon, tmod;
    reg [7:0] tl0, tl1, th0, th1;
    reg [7:0] scon, sbuf;
    reg [4:0] ie, ip;    // only 5 bits each

    assign p0_out = p0; assign p1_out = p1; assign p2_out = p2; assign p3_out = p3;
    assign sp_out = sp; assign dptr_out = {dph, dpl};
    assign tcon_out = tcon; assign tmod_out = tmod;
    assign scon_out = scon; assign sbuf_out = sbuf;
    assign ie_out = ie; assign ip_out = ip;
    assign tl0_out = tl0; assign tl1_out = tl1; assign th0_out = th0; assign th1_out = th1;

    // SFR initialization: Ports=0xFF, SP=0x07, others=0x00
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p0 <= 8'h03; p1 <= 8'h3C; p2 <= 8'h03; p3 <= 8'h03;
            sp <= 8'h07;
            {dph, dpl} <= 16'h0000;
            pcon <= 5'h00;
            tcon <= 8'h00; tmod <= 8'h00;
            {th0, tl0} <= 16'h0000; {th1, tl1} <= 16'h0000;
            scon <= 8'h00; sbuf <= 8'h00;
            ie <= 5'h00; ip <= 5'h00;
        end else if (sfr_wr) begin
            case (addr)
                8'h80: p0 <= wdata;
                8'h81: sp <= wdata;
                8'h82: dpl <= wdata;
                8'h83: dph <= wdata;
                8'h87: pcon <= wdata[4:0];
                8'h88: tcon <= wdata;
                8'h89: tmod <= wdata;
                8'h8A: tl0 <= wdata;
                8'h8B: tl1 <= wdata;
                8'h8C: th0 <= wdata;
                8'h8D: th1 <= wdata;
                8'h90: p1 <= wdata;
                8'h98: scon <= wdata;
                8'h99: sbuf <= wdata;
                8'hA0: p2 <= wdata;
                8'hA8: ie <= wdata[4:0];
                8'hB0: p3 <= wdata;
                8'hB8: ip <= wdata[4:0];
                default: ; // unmapped addresses: read-only or unimplemented
            endcase
        end
    end

    // SFR read mux
    always @(*) begin
        if (sfr_rd) begin
            case (addr)
                8'h80: rdata = p0;    8'h81: rdata = sp;
                8'h82: rdata = dpl;   8'h83: rdata = dph;
                8'h87: rdata = {3'b000, pcon};
                8'h88: rdata = tcon;  8'h89: rdata = tmod;
                8'h8A: rdata = tl0;   8'h8B: rdata = tl1;
                8'h8C: rdata = th0;   8'h8D: rdata = th1;
                8'h90: rdata = p1;
                8'h98: rdata = scon;  8'h99: rdata = sbuf;
                8'hA0: rdata = p2;
                8'hA8: rdata = {3'b000, ie};
                8'hB0: rdata = p3;
                8'hB8: rdata = {3'b000, ip};
                8'hD0: rdata = 8'h00; // PSW (handled separately)
                8'hE0: rdata = 8'h00; // ACC (handled separately)
                8'hF0: rdata = 8'h00; // B (handled separately)
                default: rdata = 8'h00;
            endcase
        end else begin
            rdata = 8'h00;
        end
    end

endmodule
