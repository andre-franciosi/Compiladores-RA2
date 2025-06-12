; =============================================================================
; funcoes_assembly.S
; Biblioteca de rotinas para Aritmética e Comunicação Serial (v3 - Autocontida)
; =============================================================================

; --- Definicoes de Hardware para ATmega328P ---
.equ UDR0,   0xC6
.equ UCSR0A, 0xC0
.equ UCSR0B, 0xC1
.equ UCSR0C, 0xC2
.equ UBRR0L, 0xC4
.equ UBRR0H, 0xC5
.equ UDRE0,  5
.equ TXEN0,  3
.equ UCSZ00, 1
.equ UCSZ01, 2

.section .text
.global main

; =============================================================================
; === ROTINAS DE COMUNICAÇÃO SERIAL
; =============================================================================

.global init_serial
init_serial:
    ; Configura o Baud Rate para 9600 (F_CPU = 16MHz)
    ; UBRR = (F_CPU / (16 * BAUD)) - 1 = (16000000 / (16 * 9600)) - 1 = 103
    ldi r24, hi8(103)
    ldi r25, lo8(103)
    sts UBRR0H, r24
    sts UBRR0L, r25
    ; Habilita o transmissor (TXEN0)
    ldi r24, (1<<TXEN0)
    sts UCSR0B, r24
    ; Configura o formato do frame: 8 data, 1 stop bit
    ldi r24, (1<<UCSZ01) | (1<<UCSZ00)
    sts UCSR0C, r24
    ret

; Envia um único caractere que está no registrador r24
.global send_char
send_char:
    push r25
send_char_wait:
    lds r25, UCSR0A
    sbrs r25, UDRE0  ; Pula a próxima instrução se o buffer de envio estiver pronto
    rjmp send_char_wait
    sts UDR0, r24   ; Envia o caractere
    pop r25
    ret

; Envia uma nova linha (CR LF)
.global send_newline
send_newline:
    push r24
    ldi r24, 13 ; CR (Carriage Return)
    rcall send_char
    ldi r24, 10 ; LF (Line Feed)
    rcall send_char
    pop r24
    ret

; Imprime um número de 16 bits (de r25:r24) como decimal
.global print_16bit_decimal
print_16bit_decimal:
    push r16
    push r17
    push r18
    push r19
    
    ; Inicializa contador de dígitos
    clr r19
    
    ; Verifica se o número é zero
    tst r24
    brne not_zero
    tst r25
    brne not_zero
    ldi r24, '0'
    rcall send_char
    rjmp print_end

not_zero:
    ; Configura divisor inicial (10000)
    ldi r18, lo8(10000)
    ldi r19, hi8(10000)
    rcall div16_print_digit
    
    ; Divisor 1000
    ldi r18, lo8(1000)
    ldi r19, hi8(1000)
    rcall div16_print_digit
    
    ; Divisor 100
    ldi r18, lo8(100)
    ldi r19, hi8(100)
    rcall div16_print_digit
    
    ; Divisor 10
    ldi r18, lo8(10)
    ldi r19, hi8(10)
    rcall div16_print_digit
    
    ; Último dígito
    mov r24, r22
    subi r24, -'0'
    rcall send_char

print_end:
    pop r19
    pop r18
    pop r17
    pop r16
    ret

; Sub-rotina: Divide e imprime dígito
div16_print_digit:
    ; Entradas:
    ;   - r25:r24 = número (dividendo)
    ;   - r19:r18 = divisor (constante 10000, 1000, 100, 10)
    ; Objetivo: imprimir o quociente (se != 0) e manter número (dividendo) intacto
    ; Usa r27:r26 como temporário

    movw r26, r24        ; Salva número original em r27:r26
    movw r22, r18        ; Coloca divisor em r23:r22
    movw r24, r26        ; Restaura número em r25:r24 (dividendo)

    rcall div16_unsigned_remainder   ; quociente -> r25:r24, resto -> r23:r22

    tst r24              ; Dígito = quociente low
    breq skip_zero
    subi r24, -'0'       ; Converte para ASCII
    rcall send_char

skip_zero:
    movw r24, r26        ; Restaura número original para próximos divisores
    ret

; =============================================================================
; === ROTINAS ARITMÉTICAS DE 16 BITS
; =============================================================================

.global mult16
mult16:
  clr r27
  clr r26
  ldi r18, 16
mult16_loop:
  sbrc r22, 0
  add r26, r24
  sbrc r22, 0
  adc r27, r25
  lsr r23
  ror r22
  lsl r24
  rol r25
  dec r18
  brne mult16_loop
  movw r24, r26
  ret

.global div16_unsigned_remainder
div16_unsigned_remainder:
    push r16
    push r17
    movw r16, r24       ; Salva dividendo
    movw r24, r22       ; Move divisor para r25:r24
    movw r22, r16       ; Move dividendo para r23:r22
    clr r16
    clr r17
    ldi r18, 17
div16_loop:
    rol r22
    rol r23
    rol r16
    rol r17
    sub r16, r24
    sbc r17, r25
    brcc div16_skip
    add r16, r24
    adc r17, r25
    clc
    rjmp div16_next
div16_skip:
    sec
div16_next:
    dec r18
    brne div16_loop
    movw r24, r22       ; Quociente em r25:r24
    movw r22, r16       ; Resto em r23:r22
    pop r17
    pop r16
    ret

.global pow16
pow16:
    push r16
    push r17
    movw r16, r24   ; Salva base
    ldi r24, 1      ; Inicia resultado = 1
    clr r25
pow16_loop:
    tst r22
    brne pow16_mult
    tst r23
    breq pow16_end
pow16_mult:
    movw r18, r24   ; Resultado temporário
    movw r20, r16   ; Base
    rcall mult16    ; Multiplica resultado pela base
    subi r22, 1          ; low byte (expoente--)
    sbci r23, 0          ; high byte with carry
    rjmp pow16_loop
pow16_end:
    pop r17
    pop r16
    ret