; Smoke Test for echo_8051
; Tests basic instruction set: MOV, ADD, SUBB, ANL, ORL, XRL, INC, DEC, DJNZ, SJMP
; Compile: asm51 smoke_test.asm  (or SDCC)
; Hex format: Intel HEX

    ORG 0000H

START:
    ; Test 1: MOV immediate
    MOV  A, #55H        ; ACC = 0x55
    MOV  B, #0AAH       ; B = 0xAA

    ; Test 2: ADD
    ADD  A, B           ; ACC = 0x55 + 0xAA = 0xFF, CY=0
    MOV  R0, A          ; R0 = 0xFF

    ; Test 3: ANL (bitwise AND)
    MOV  A, #0FH        ; ACC = 0x0F
    ANL  A, #0F0H       ; ACC = 0x00

    ; Test 4: ORL
    MOV  A, #0AH        ; ACC = 0x0A
    ORL  A, #0A0H       ; ACC = 0xAA

    ; Test 5: XRL
    XRL  A, #0FFH       ; ACC = 0x55

    ; Test 6: INC
    INC  A               ; ACC = 0x56

    ; Test 7: DEC
    DEC  A               ; ACC = 0x55

    ; Test 8: SUBB
    MOV  A, #10H        ; ACC = 0x10
    MOV  B, #01H        ; B = 0x01
    CLR  C              ; CY = 0
    SUBB A, B           ; ACC = 0x0F

    ; Test 9: MOV to internal RAM
    MOV  30H, A         ; RAM[0x30] = 0x0F
    MOV  A, 30H         ; ACC = 0x0F

    ; Test 10: DJNZ (loop)
    MOV  R1, #05H       ; counter = 5
LOOP:
    INC  A               ; ACC++
    DJNZ R1, LOOP        ; loop 5 times (ACC = 0x0F + 5 = 0x14)

    ; Test 11: PUSH / POP
    MOV  SP, #70H       ; init stack pointer
    PUSH ACC            ; push ACC to stack
    MOV  A, #00H        ; clear ACC
    POP  ACC            ; restore ACC = 0x14

    ; Test 12: SWAP
    MOV  A, #12H        ; ACC = 0x12
    SWAP A              ; ACC = 0x21

    ; End: infinite loop
END:
    SJMP END

    END
