// IO Ports — P0-P3 Bidirectional I/O
// Reverse-engineered: dfstp FFs (reset=0xFF, set-to-1 on reset)
// P0: open-drain, address/data multiplexed
// P1: quasi-bidirectional
// P2: quasi-bidirectional, high address byte
// P3: quasi-bidirectional, alternate functions

module io_ports (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  p0_wr, p1_wr, p2_wr, p3_wr, // from SFR
    input  wire        p0_wr_en, p1_wr_en, p2_wr_en, p3_wr_en,
    output reg  [7:0]  p0_rd, p1_rd, p2_rd, p3_rd, // to internal bus
    output wire [7:0]  p0_out, p1_out, p2_out, p3_out,
    input  wire [7:0]  p0_in, p1_in, p2_in, p3_in
);
    reg [7:0] p0_reg, p1_reg, p2_reg, p3_reg;

    assign p0_out = p0_reg; assign p1_out = p1_reg;
    assign p2_out = p2_reg; assign p3_out = p3_reg;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            p0_reg <= 8'h03; p1_reg <= 8'h3C;
            p2_reg <= 8'h03; p3_reg <= 8'h03;
        end else begin
            if (p0_wr_en) p0_reg <= p0_wr;
            if (p1_wr_en) p1_reg <= p1_wr;
            if (p2_wr_en) p2_reg <= p2_wr;
            if (p3_wr_en) p3_reg <= p3_wr;
        end
    end

    always @(*) begin
        p0_rd = p0_in; p1_rd = p1_in;
        p2_rd = p2_in; p3_rd = p3_in;
    end

endmodule
