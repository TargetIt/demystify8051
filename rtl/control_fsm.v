// Control FSM — 8051 Main Control State Machine
// Reverse-engineered: 8 dfrtp state FFs, CTRL[7:0] output
// Sequences: FETCH → DECODE → EXEC1 → EXEC2 → WRITEBACK

module control_fsm (
    input  wire        clk,
    input  wire        rst_n,
    input  wire        opcode_valid,     // from decoder: valid opcode decoded
    input  wire [1:0]  operand_bytes,    // number of extra fetches needed
    input  wire        interrupt_pending,// interrupt request active
    output reg  [2:0]  state,            // current FSM state
    output reg  [7:0]  ctrl_out,         // CTRL bus
    output reg         fetch_en,         // enable instruction fetch
    output reg         exec_en           // enable execute phase
);
    localparam FETCH    = 3'd0,
               DECODE   = 3'd1,
               EXEC1    = 3'd2,
               EXEC2    = 3'd3,
               WRITEBK  = 3'd4,
               INT_ACK  = 3'd5,
               FETCH2   = 3'd6,
               FETCH3   = 3'd7;

    reg [1:0] byte_cnt;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= FETCH;
            byte_cnt <= 2'd0;
            fetch_en <= 1'b1;
            exec_en <= 1'b0;
            ctrl_out <= 8'h00;
        end else begin
            case (state)
                FETCH: begin
                    fetch_en <= 1'b1;
                    exec_en <= 1'b0;
                    ctrl_out <= 8'h00;
                    if (interrupt_pending)
                        state <= INT_ACK;
                    else
                        state <= DECODE;
                end
                DECODE: begin
                    fetch_en <= 1'b0;
                    byte_cnt <= operand_bytes;
                    if (operand_bytes == 2'd0)
                        state <= EXEC1;
                    else if (operand_bytes == 2'd1)
                        state <= FETCH2;
                    else
                        state <= FETCH2;
                end
                FETCH2: begin
                    fetch_en <= 1'b1;
                    byte_cnt <= byte_cnt - 2'd1;
                    if (byte_cnt > 2'd1)
                        state <= FETCH3;
                    else
                        state <= EXEC1;
                end
                FETCH3: begin
                    fetch_en <= 1'b1;
                    state <= EXEC1;
                end
                EXEC1: begin
                    fetch_en <= 1'b0;
                    exec_en <= 1'b1;
                    ctrl_out <= 8'h01; // ALU enable
                    state <= EXEC2;
                end
                EXEC2: begin
                    ctrl_out <= 8'h02; // memory/SFR access
                    state <= WRITEBK;
                end
                WRITEBK: begin
                    ctrl_out <= 8'h04; // write-back enable
                    exec_en = 1'b0;     // blocking: prevent double-write in same cycle
                    state <= FETCH;
                end
                INT_ACK: begin
                    // Push PC to stack, jump to vector
                    state <= FETCH;
                end
                default: state <= FETCH;
            endcase
        end
    end

endmodule
