// Cross-validation testbench — dumps CPU state after each instruction
`timescale 1ns/1ps

module tb_crossval;
    reg clk, rst_n, int0_n, int1_n, rxd, ea_n;
    wire [7:0] p0, p1, p2, p3;
    wire txd, ale, psen_n, rd_n, wr_n;
    always #10 clk = ~clk;

    echo_8051_top u_dut (.clk(clk),.rst_n(rst_n),.int0_n(int0_n),.int1_n(int1_n),
        .p0(p0),.p1(p1),.p2(p2),.p3(p3),.rxd(rxd),.txd(txd),
        .ale(ale),.psen_n(psen_n),.rd_n(rd_n),.wr_n(wr_n),.ea_n(ea_n));

    integer trace_fd, instr_count;
    reg  [2:0] prev_state;

    // Helper: read SFR byte (offset from 0x80)
    function [7:0] sfr_byte;
        input [6:0] offset;
        begin
            // sfr_block internal array: sfr[offset]
            sfr_byte = u_dut.u_sfr.sfr[offset];
        end
    endfunction

    initial begin
        clk=0; rst_n=0; int0_n=1; int1_n=1; rxd=1; ea_n=1;
        instr_count = 0; prev_state = 0;
        trace_fd = $fopen("rtl_trace.txt", "w");
        #100 rst_n=1;
        $fwrite(trace_fd, "# RTL instruction trace\n");
        $fwrite(trace_fd, "# format: INSTR_NUM|PC|ACC|PSW|SP|IRAM_DIFF\n");
    end

    // Detect instruction completion: state transitions TO S_FETCH (0)
    // Capture on negedge so SFR NBA writes from posedge are visible.
    reg capture_flag;
    always @(posedge clk) begin
        if (!rst_n) begin
            prev_state <= 0;
            capture_flag <= 0;
        end else begin
            capture_flag <= (u_dut.u_cpu.state == 3'd0 && prev_state != 3'd0);
            prev_state <= u_dut.u_cpu.state;
        end
    end

    always @(negedge clk) begin
        if (capture_flag) begin
            instr_count = instr_count + 1;
            $fwrite(trace_fd, "%0d|%04X|%02X|%02X|%02X|",
                instr_count,
                u_dut.u_cpu.pc,           // PC points to NEXT instruction
                sfr_byte(7'h60),           // ACC at 0xE0
                sfr_byte(7'h50),           // PSW at 0xD0
                sfr_byte(7'h01));          // SP  at 0x81
            $fwrite(trace_fd, "\n");
            if (instr_count >= 200) begin
                $fclose(trace_fd);
                $display("Trace complete: %0d instructions", instr_count);
                $finish;
            end
        end
    end

    initial begin
        $dumpfile("tb_crossval.vcd");
        $dumpvars(0, tb_crossval);
    end
endmodule
