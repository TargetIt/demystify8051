// IRAM — 128-Byte Internal RAM
// Reverse-engineered: 160 dfxtp FFs (_06895_ through _07054_)
// Address bus: _07143_[7:0], Control: _07112_[2:0]
// Address space:
//   0x00-0x1F: 4 banks × 8 registers (R0-R7)
//   0x20-0x2F: bit-addressable area (128 bits)
//   0x30-0x7F: general purpose RAM

module iram (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        ram_rd,          // read enable
    input  wire        ram_wr,          // write enable
    input  wire [7:0]  addr,            // 8-bit address (0x00-0x7F)
    input  wire [7:0]  wdata,           // write data
    output reg  [7:0]  rdata            // read data
);
    // 128 × 8-bit storage
    reg [7:0] mem [0:127];

    // Write
    always @(posedge clk) begin
        if (ram_wr && addr[7] == 1'b0)  // only 0x00-0x7F writable
            mem[addr[6:0]] <= wdata;
    end

    // Read (combinational for speed — matches gate-level mux tree)
    always @(*) begin
        if (ram_rd && addr[7] == 1'b0)
            rdata = mem[addr[6:0]];
        else
            rdata = 8'h00;
    end

endmodule
