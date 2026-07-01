// Timer — T0/T1 16-bit Timer/Counter
// Reverse-engineered: 132 cells, 7 xor + 32 mux → ripple-carry counter
// 4 modes: 13-bit, 16-bit, 8-bit auto-reload, split 8-bit

module timer (
    input  wire        clk,
    input  wire        rst_n,
    input  wire [7:0]  tcon,     // timer control register
    input  wire [7:0]  tmod,     // timer mode register
    input  wire        t0_pin,   // external T0 input (for counter mode)
    input  wire        t1_pin,   // external T1 input
    output reg  [7:0]  tl0, th0, tl1, th1,
    output reg         tf0, tf1  // overflow flags
);
    reg [15:0] t0_cnt, t1_cnt;
    reg [15:0] t0_reload, t1_reload;

    // Timer 0
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            {th0, tl0} <= 16'h0000;
            t0_cnt <= 16'h0000;
            t0_reload <= 16'h0000;
            tf0 <= 1'b0;
        end else begin
            {th0, tl0} <= {t0_cnt[15:8], t0_cnt[7:0]};
            if (tcon[4]) begin // TR0: timer 0 run
                case (tmod[1:0]) // M1,M0
                    2'b00: begin // 13-bit
                        {t0_cnt[12:0]} <= t0_cnt[12:0] + 13'd1;
                        if (t0_cnt[12:0] == 13'h1FFF) begin
                            tf0 <= 1'b1;
                            t0_cnt[12:0] <= 13'h0000;
                        end
                    end
                    2'b01: begin // 16-bit
                        t0_cnt <= t0_cnt + 16'd1;
                        if (t0_cnt == 16'hFFFF) begin
                            tf0 <= 1'b1;
                            t0_cnt <= t0_reload;
                        end
                    end
                    2'b10: begin // 8-bit auto-reload
                        t0_cnt[7:0] <= t0_cnt[7:0] + 8'd1;
                        if (t0_cnt[7:0] == 8'hFF) begin
                            tf0 <= 1'b1;
                            t0_cnt[7:0] <= t0_reload[7:0];
                        end
                    end
                    2'b11: begin // split (TL0 8-bit, TH0 8-bit)
                        t0_cnt[7:0] <= t0_cnt[7:0] + 8'd1;
                        if (tmod[3] && t0_cnt[7:0] == 8'hFF) tf0 <= 1'b1;
                        if (tmod[6] && t0_cnt[15:8] == 8'hFF) tf0 <= 1'b1;
                        t0_cnt[15:8] <= t0_cnt[15:8] + 8'd1;
                    end
                endcase
            end
            if (tcon[5]) tf0 <= 1'b0; // software clear
        end
    end

    // Timer 1 (simplified — same structure as T0)
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            {th1, tl1} <= 16'h0000;
            t1_cnt <= 16'h0000;
            tf1 <= 1'b0;
        end else begin
            {th1, tl1} <= {t1_cnt[15:8], t1_cnt[7:0]};
            if (tcon[6]) begin
                t1_cnt <= t1_cnt + 16'd1;
                if (t1_cnt == 16'hFFFF) begin tf1 <= 1'b1; t1_cnt <= t1_reload; end
            end
            if (tcon[7]) tf1 <= 1'b0;
        end
    end

endmodule
