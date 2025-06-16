.section .text

_unpack_f16:
        ; sinal
        mov     r16, r31
        andi    r16, 0x80
        lsr     r16
        lsr     r16
        lsr     r16
        lsr     r16
        lsr     r16
        lsr     r16
        lsr     r16            ; bit0 = sign

        ; expoente
        mov     r17, r31
        andi    r17, 0x7C      ; bits 14-10
        lsr     r17
        lsr     r17            ; exp em 0-31

        ; mantissa (10 bits) + bit extra
        mov     r18, r30       ; low
        mov     r19, r31
        andi    r19, 0x03      ; bits 9-8

        ; se exp != 0 ➜ adiciona “1”
        cpi     r17, 0
        breq    1f
        ori     r19, 0x04      ; bit extra = 1
1:      ret


; --- _pack_f16 ---------------------------------------------------------------
; Entrada : r16 sign, r17 exp (0-31), r19:r18 mantissa (10 bits)
; Saída   : r25:r24 half-float
; ----------------------------------------------------------------------------
_pack_f16:
        mov     r24, r18
        mov     r25, r19
        andi    r25, 0x03      ; zera bits sobrando

        ; sinal
        bst     r16, 0
        bld     r25, 7

        ; expoente → bits 14-10 (r25 bits 6-2)
        swap    r17            ; exp[4:0] → bits7-3
        andi    r17, 0xF0
        or      r25, r17
        ret


; --- _normalize_left ---------------------------------------------------------
; Normaliza mantissa após subtração (shift << até bit extra ficar 1).
; Entrada : r17 exp, r19:r18 mant.  Saída mesmos regs.
; ----------------------------------------------------------------------------
_normalize_left:
2:      sbrc    r19, 2          ; bit extra já 1?
        rjmp    3f
        cpi     r17, 0
        breq    3f
        lsl     r18
        rol     r19
        dec     r17
        rjmp    2b
3:      ret


; --- _normalize_right --------------------------------------------------------
; Normaliza mantissa após soma/mul (se overflow bit3).
; Entrada: r17 exp, r19:r18 mant.
; ----------------------------------------------------------------------------
_normalize_right:
        sbrc    r19, 3
        rjmp    4f
        ret
4:      lsr     r19
        ror     r18
        inc     r17
        ret


; --- _round_RNE --------------------------------------------------------------
; Arredonda 11→10 bits (Round-to-Nearest-Even).
; Mantissa antes: r19:r18 (bit0 = guard).  Saída r19:r18.
; ----------------------------------------------------------------------------
_round_RNE:
        lsr     r18            ; guard → C
        ror     r19
        brcc    5f             ; C=0 → já está
        subi    r18, 0xFF      ; +1
        sbci    r19, 0xFF
5:      ret


; ----------------------------------------------------------------------------
; === Operações primárias =====================================================
; ----------------------------------------------------------------------------
; Convenção de chamada (todas):
;   A = r25:r24,  B = r23:r22,  saída = r25:r24
; ----------------------------------------------------------------------------

; ---------- fadd16  (A + B) --------------------------------------------------
.global fadd16
fadd16:
        push    r20
        push    r21
        push    r26
        push    r27
        push    r28
        push    r29
        push    r30
        push    r31

        ; --- desempacota A ---------------------------------------------------
        mov     r30, r24
        mov     r31, r25
        rcall   _unpack_f16
        mov     r20, r16        ; signA
        mov     r21, r17        ; expA
        mov     r26, r18
        mov     r27, r19        ; mantA r27:r26

        ; --- desempacota B ---------------------------------------------------
        mov     r30, r22
        mov     r31, r23
        rcall   _unpack_f16     ; devolve sign em r16, exp em r17, mant em r19:r18

        ; --- garante expA >= expB -------------------------------------------
        mov     r28, r17        ; expB
        mov     r29, r16        ; signB
        mov     r30, r18        ; mantB low
        mov     r31, r19        ; mantB high

        cp      r21, r28
        brge    6f              ; já OK
        ; troca tudo
        mov     r21, r28
        mov     r20, r29
        mov     r18, r26
        mov     r19, r27
        mov     r26, r30
        mov     r27, r31
6:
        ; diff = expA - expB (r21 - r28)  → r28
        mov     r28, r21
        sub     r28, r17

        ; mantA = r27:r26, mantB = r31:r30
        mov     r30, r22
        mov     r31, r23        ; mantB já em r31:r30
        mov     r18, r30
        mov     r19, r31

        ; --- alinha mantB ----------------------------------------------------
7:      tst     r28
        breq    8f
        lsr     r19
        ror     r18
        dec     r28
        rjmp    7b
8:
        ; --- soma ou sub -----------------------------------------------------
        eor     r29, r20        ; sinais iguais? 0=soma, 1=sub
        brne    9f

        ; soma
        add     r18, r26
        adc     r19, r27
        rcall   _normalize_right
        rjmp    10f
9:      ; subtrai (A - B)  – A maior
        sub     r26, r18
        sbc     r27, r19
        mov     r18, r26
        mov     r19, r27
        rcall   _normalize_left
10:
        mov     r16, r20        ; sinal final
        mov     r17, r21        ; exp final

        rcall   _round_RNE
        rcall   _pack_f16

        pop     r31
        pop     r30
        pop     r29
        pop     r28
        pop     r27
        pop     r26
        pop     r21
        pop     r20
        ret


; ---------- fsub16  (A - B) --------------------------------------------------
.global fsub16
fsub16:
        push    r16
        ldi     r16, 0x80
        eor     r23, r16        ; inverte sinal de B
        rcall   fadd16
        pop     r16
        ret


; ---------- fmul16 (A * B) ---------------------------------------------------
.global fmul16
fmul16:
        push    r20
        push    r21
        push    r26
        push    r27
        push    r30
        push    r31

        ; desempacota A
        mov     r30, r24
        mov     r31, r25
        rcall   _unpack_f16
        mov     r20, r16
        mov     r21, r17
        mov     r26, r18
        mov     r27, r19

        ; desempacota B
        mov     r30, r22
        mov     r31, r23
        rcall   _unpack_f16

        eor     r16, r20        ; sinal
        add     r17, r21
        subi    r17, 15         ; –bias

        ; multiplica mantissas (11×11 → 22 bits) ------------------------------
        ; usa mult16 (lower16 * lower16)  r26:r27  ×  r18:r19
        ; copias
        mov     r24, r26
        mov     r25, r27
        mov     r22, r18
        mov     r23, r19
        rcall   mult16          ;   resultado 32 bit  r27:r26:r25:r24
        ; mantissa = r26:r25  (21:6)
        mov     r18, r24
        mov     r19, r25
        rcall   _normalize_right

        mov     r16, r16        ; sinal já
        mov     r17, r17        ; exp já

        rcall   _round_RNE
        rcall   _pack_f16

        pop     r31
        pop     r30
        pop     r27
        pop     r26
        pop     r21
        pop     r20
        ret


; ---------- fdiv16 (A / B) ---------------------------------------------------
.global fdiv16
fdiv16:
        push    r20
        push    r21
        push    r26
        push    r27
        push    r30
        push    r31

        ; desempacota A
        mov     r30, r24
        mov     r31, r25
        rcall   _unpack_f16
        mov     r20, r16
        mov     r21, r17
        mov     r26, r18
        mov     r27, r19

        ; desempacota B
        mov     r30, r22
        mov     r31, r23
        rcall   _unpack_f16

        eor     r16, r20        ; sinal
        sub     r21, r17
        subi    r21, -15        ; +bias

        ; divide mantissas (11/11) → 11 bits
        ; r26:r27 ÷ r18:r19  (unsigned)  → quociente em r25:r24
        mov     r24, r26
        mov     r25, r27
        mov     r22, r18
        mov     r23, r19
        rcall   div16_unsigned_remainder

        mov     r18, r24
        mov     r19, r25
        rcall   _normalize_left

        rcall   _round_RNE
        rcall   _pack_f16

        pop     r31
        pop     r30
        pop     r27
        pop     r26
        pop     r21
        pop     r20
        ret


; ---------- fpow16 (stub: devolve NaN) ---------------------------------------
; Se precisar mesmo da potência, implemente depois e lembre-se de
; obedecer às restrições de registrador.
.global fpow16
fpow16:
        ldi     r25, 0x7E       ; quiet-NaN 0x7E00
        ldi     r24, 0x00
        ret


; ----------------------------------------------------------------------------
; === Utilitários de 16 bits ==================================================
; ----------------------------------------------------------------------------

; --- mult16: 16×16 → 32 bits -------------------------------------------------
; Entrada : A=r25:r24, B=r23:r22
; Saída    : r27:r26:r25:r24 (alto→baixo)
; ----------------------------------------------------------------------------
.global mult16
mult16:
        push    r0
        push    r1
        clr     r26
        clr     r27
        ; byte baixo × baixo
        mul     r24, r22        ; r1:r0
        mov     r24, r0
        mov     r25, r1
        clr     r1
        ; baixo A × alto B
        mul     r24, r23
        add     r25, r0
        adc     r26, r1
        clr     r1
        ; alto A × baixo B
        mul     r25, r22
        add     r25, r0
        adc     r26, r1
        clr     r1
        ; alto A × alto B
        mul     r25, r23
        add     r26, r0
        adc     r27, r1
        clr     r1
        pop     r1
        pop     r0
        ret


; --- div16_unsigned_remainder ------------------------------------------------
; Entrada : A=r25:r24 (dividendo), B=r23:r22 (divisor)
; Saída    : quociente r25:r24  (resto descartado)
; ----------------------------------------------------------------------------
.global div16_unsigned_remainder
div16_unsigned_remainder:
        push    r20
        push    r21
        push    r22
        push    r23
        clr     r20             ; resto high
        clr     r21             ; resto low
        ldi     r22, 16
1:      lsl     r24
        rol     r25
        rol     r21
        rol     r20
        movw    r30, r20        ; resto em r31:r30
        cp      r30, r22
        cpc     r31, r23
        brcs    2f
        sub     r30, r22
        sbc     r31, r23
        movw    r20, r30
        ori     r24, 0x01
2:      dec     r22
        brne    1b
        pop     r23
        pop     r22
        pop     r21
        pop     r20
        ret


; ----------------------------------------------------------------------------
; === Rotina de saída (hexadecimal) ===========================================
; ----------------------------------------------------------------------------
; Requer função externa:   send_char   (caractere em r24 ➜ UART)

;  print_f16  –  imprime half-float em formato 0xHHLL\r\n
; ----------------------------------------------------------------------------
.global print_f16
print_f16:
        push    r24
        push    r30
        push    r31

        ; "0x"
        ldi     r24, '0'
        rcall   send_char
        ldi     r24, 'x'
        rcall   send_char

        ; byte alto
        mov     r30, r25
        rcall   print_byte_hex

        ; byte baixo
        mov     r30, r24
        rcall   print_byte_hex

        ; CRLF
        ldi     r24, 13
        rcall   send_char
        ldi     r24, 10
        rcall   send_char

        pop     r31
        pop     r30
        pop     r24
        ret


; --- print_byte_hex ----------------------------------------------------------
; Entrada : r30 = byte
; Saída   : envia dois dígitos ASCII
print_byte_hex:
        push    r24
        ; nibble alto
        mov     r24, r30
        swap    r24
        rcall   nibble2ascii
        ; nibble baixo
        mov     r24, r30
        rcall   nibble2ascii
        pop     r24
        ret


; --- nibble2ascii ------------------------------------------------------------
; Entrada : r24 (0-15),  Saída: envia ASCII
nibble2ascii:
        andi    r24, 0x0F
        cpi     r24, 10
        brlo    3f
        subi    r24, -('A' - 10)
        rjmp    4f
        subi    r24, -'0'
        rcall   send_char
        ret
        
        .section .bss

        ; ---- Registros de I/O (endereços em data-space) --------------------
        .equ    UDR0    , 0x00C6
        .equ    UBRR0L  , 0x00C4
        .equ    UBRR0H  , 0x00C5
        .equ    UCSR0A  , 0x00C0
        .equ    UCSR0B  , 0x00C1
        .equ    UCSR0C  , 0x00C2

        ; ---- Bits ----------------------------------------------------------
        .equ    TXEN0   , 3
        .equ    UDRE0   , 5
        .equ    UCSZ00  , 1
        .equ    UCSZ01  , 2

        ; ---- Constante de baud ---------------------------------------------
        ; BAUD_DIV = 16 000 000 / (16·9 600) − 1 = 103
        .equ    BAUD_DIV, 103

; ----------------------------------------------------------------------------
.global init_serial
init_serial:
        ldi     r24, lo8(BAUD_DIV)
        sts     UBRR0L, r24
        ldi     r24, hi8(BAUD_DIV)
        sts     UBRR0H, r24

        ldi     r24, (1<<TXEN0)               ; habilita transmissor
        sts     UCSR0B, r24

        ldi     r24, (1<<UCSZ00)|(1<<UCSZ01)  ; 8 N 1
        sts     UCSR0C, r24
        ret

; ----------------------------------------------------------------------------
.global send_char
send_char:                                    ; r24 = caractere
        push    r18
        lds     r18, UCSR0A
        sbrs    r18, UDRE0                    ; espera buffer vazio
        rjmp    1b
        sts     UDR0, r24
        pop     r18
        ret

; ----------------------------------------------------------------------------
.global send_newline
send_newline:
        push    r24
        ldi     r24, 13
        rcall   send_char
        ldi     r24, 10
        rcall   send_char
        pop     r24
        ret
