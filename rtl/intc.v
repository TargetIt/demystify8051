// IntC — Interrupt Controller
// 5 interrupt sources, 2 priority levels
// Reverse-engineered: 26 cells (8 and2 + 2 xnor → priority encoder)

module intc (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [4:0]  ie,           // interrupt enable
    input  wire [4:0]  ip,           // interrupt priority
    input  wire        int0_n, int1_n, // external interrupts
    input  wire        tf0, tf1,     // timer overflow
    input  wire        ri, ti,       // serial flags
    output reg         int_active,
    output reg  [15:0] vector_addr   // ISR vector
);
    // Interrupt flags: {Serial, T1, INT1, T0, INT0}
    wire [4:0] flags = {ri | ti, tf1, ~int1_n, tf0, ~int0_n};
    reg  [4:0] enabled;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            int_active <= 1'b0;
            vector_addr <= 16'h0000;
            enabled <= 5'h00;
        end else begin
            enabled <= flags & ie;
            int_active <= |enabled;

            // Priority encoder (high priority)
            if (enabled[0] && ip[0])      vector_addr <= 16'h0003; // INT0 high
            else if (enabled[1] && ip[1]) vector_addr <= 16'h000B; // T0 high
            else if (enabled[2] && ip[2]) vector_addr <= 16'h0013; // INT1 high
            else if (enabled[3] && ip[3]) vector_addr <= 16'h001B; // T1 high
            else if (enabled[4] && ip[4]) vector_addr <= 16'h0023; // Serial high
            // Low priority (default order)
            else if (enabled[0])          vector_addr <= 16'h0003;
            else if (enabled[1])          vector_addr <= 16'h000B;
            else if (enabled[2])          vector_addr <= 16'h0013;
            else if (enabled[3])          vector_addr <= 16'h001B;
            else if (enabled[4])          vector_addr <= 16'h0023;
            else                          vector_addr <= 16'h0000;
        end
    end

endmodule
