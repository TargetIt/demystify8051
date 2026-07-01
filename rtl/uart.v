// UART — Full-Duplex Serial Port
// 4 modes: 0 (sync shift), 1 (8-bit UART, variable baud), 2 (9-bit UART, fixed), 3 (9-bit, variable)
// Reverse-engineered: 88 cells, shift register + baud generator

module uart (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        rxd,
    output wire        txd,
    input  wire [7:0]  scon,         // serial control
    input  wire [7:0]  sbuf_in,      // data to transmit (from SFR write)
    output reg  [7:0]  sbuf_out,     // received data
    output reg         ri, ti,       // interrupt flags
    input  wire [15:0] baud_div      // baud rate divisor (from Timer1)
);
    reg [9:0] tx_shift;    // 10-bit TX shift: start(0) + 8 data + stop(1)
    reg [9:0] rx_shift;
    reg [3:0] tx_bit_cnt, rx_bit_cnt;
    reg [15:0] baud_cnt;
    reg       tx_busy;
    wire      baud_tick = (baud_cnt == baud_div);

    // Baud rate generator
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) baud_cnt <= 16'd0;
        else if (baud_tick || !tx_busy) baud_cnt <= 16'd0;
        else baud_cnt <= baud_cnt + 16'd1;
    end

    // TX
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            tx_shift <= 10'h3FF; // idle high
            tx_bit_cnt <= 4'd0;
            tx_busy <= 1'b0;
            ti <= 1'b0;
        end else begin
            if (!tx_busy && (scon[4] || ti)) begin // start TX on SBUF write
                tx_shift <= {1'b1, sbuf_in[7:0], 1'b0}; // stop, data, start
                tx_bit_cnt <= 4'd10;
                tx_busy <= 1'b1;
            end else if (tx_busy && baud_tick) begin
                tx_shift <= {1'b1, tx_shift[9:1]};
                tx_bit_cnt <= tx_bit_cnt - 4'd1;
                if (tx_bit_cnt == 4'd1) begin
                    tx_busy <= 1'b0;
                    ti <= 1'b1; // TX complete
                end
            end
        end
    end

    assign txd = tx_shift[0];

    // RX (simplified — 8-bit UART mode 1)
    reg [1:0] rxd_sync;
    reg [7:0] rx_reg;
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rxd_sync <= 2'b11;
            rx_bit_cnt <= 4'd0;
            rx_reg <= 8'h00;
            sbuf_out <= 8'h00;
            ri <= 1'b0;
        end else begin
            rxd_sync <= {rxd_sync[0], rxd};
            if (rxd_sync == 2'b10 && rx_bit_cnt == 4'd0) begin // start bit
                rx_bit_cnt <= 4'd8;
            end else if (rx_bit_cnt > 0 && baud_tick) begin
                rx_reg <= {rxd_sync[1], rx_reg[7:1]};
                rx_bit_cnt <= rx_bit_cnt - 4'd1;
                if (rx_bit_cnt == 4'd1) begin
                    sbuf_out <= {rxd_sync[1], rx_reg[7:1]};
                    ri <= 1'b1;
                end
            end
        end
    end

endmodule
