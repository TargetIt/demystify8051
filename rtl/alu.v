// ALU — 8-bit Arithmetic Logic Unit
// Reverse-engineered: 317 XOR/XNOR cells → ripple-carry adder + logic unit
// CTRL bus selects operation mode via _07110_[3:0]
// Operations: ADD, ADDC, SUBB, ANL, ORL, XRL, INC, DEC, DA, RL, RLC, RR, RRC, SWAP, CPL, CLR

module alu (
    input  wire [7:0]  a,           // operand A (ACC)
    input  wire [7:0]  b,           // operand B (from DB_B or immediate)
    input  wire        carry_in,    // from PSW.CY
    input  wire [3:0]  op,          // ALU operation select
    output reg  [7:0]  result,
    output reg         carry_out,   // CY flag
    output reg         aux_carry,   // AC flag (bit 3→4 carry)
    output reg         overflow     // OV flag
);
    // Operation encoding (inferred from CTRL bus analysis)
    localparam ADD  = 4'h0, ADDC = 4'h1, SUBB = 4'h2,
               ANL  = 4'h3, ORL  = 4'h4, XRL  = 4'h5,
               INC  = 4'h6, DEC  = 4'h7, DA   = 4'h8,
               RL   = 4'h9, RLC  = 4'hA, RR   = 4'hB,
               RRC  = 4'hC, SWAP = 4'hD, CPL  = 4'hE,
               CLR  = 4'hF;

    wire [8:0] add_result = {1'b0, a} + {1'b0, b} + {8'h00, carry_in & (op == ADDC || op == SUBB)};
    wire [8:0] sub_result = {1'b0, a} - {1'b0, b} - {8'h00, ~carry_in & (op == SUBB)};

    always @(*) begin
        result = 8'h00;
        {carry_out, aux_carry, overflow} = 3'b000;

        case (op)
            ADD, ADDC: begin
                result = add_result[7:0];
                carry_out = add_result[8];
                aux_carry = (a[3] & b[3]) | (b[3] & ~add_result[3]) | (~add_result[3] & a[3]);
                overflow = (a[7] & b[7] & ~add_result[7]) | (~a[7] & ~b[7] & add_result[7]);
            end
            SUBB: begin
                result = sub_result[7:0];
                carry_out = ~sub_result[8]; // borrow inverted
                aux_carry = ~((a[3] & ~b[3]) | (~b[3] & sub_result[3]) | (sub_result[3] & a[3]));
                overflow = (a[7] & ~b[7] & ~sub_result[7]) | (~a[7] & b[7] & sub_result[7]);
            end
            ANL:  result = a & b;
            ORL:  result = a | b;
            XRL:  result = a ^ b;
            INC:  {carry_out, result} = {1'b0, a} + 9'd1;
            DEC:  {carry_out, result} = {1'b0, a} - 9'd1;
            DA: begin // BCD adjust
                if (a[3:0] > 4'd9 || aux_carry) result[3:0] = a[3:0] + 4'd6;
                else result[3:0] = a[3:0];
                if (a[7:4] > 4'd9 || carry_out) result[7:4] = a[7:4] + 4'd6;
                else result[7:4] = a[7:4];
                carry_out = (a[7:4] > 4'd9);
            end
            RL:   result = {a[6:0], a[7]};
            RLC:  result = {a[6:0], carry_in};
            RR:   result = {a[0], a[7:1]};
            RRC:  result = {carry_in, a[7:1]};
            SWAP: result = {a[3:0], a[7:4]};
            CPL:  result = ~a;
            CLR:  result = 8'h00;
            default: result = 8'h00;
        endcase
    end

endmodule
