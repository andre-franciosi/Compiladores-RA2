.extern init_serial
.extern send_char
.extern send_newline
.extern print_16bit_decimal
.section .text
.global main
main:
  ; --- Inicializacao da Pilha ---  ldi r28, lo8(0x08FF)  ldi r29, hi8(0x08FF)  out 0x3E, r29  ; SPH  out 0x3D, r28  ; SPL  ; --- Inicializacao da Serial ---
  rcall init_serial
  ; -------------------------------  ; Teste inicial da serial
  ldi r24, 'A'
  rcall send_char
  ldi r24, 'T'
  rcall send_char
  rcall send_newline
  ; AVISO: Ponto flutuante (3.2) tratado como inteiro
  ; Empilhando numero 3
  ldi r24, lo8(3)
  ldi r25, hi8(3)
  push r25
  push r24
  ; AVISO: Ponto flutuante (4.8) tratado como inteiro
  ; Empilhando numero 4
  ldi r24, lo8(4)
  ldi r25, hi8(4)
  push r25
  push r24
  ; Operacao: +
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  add r24, r22
  adc r25, r23
  ; Empilhando resultado
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_16bit_decimal
  rcall send_newline
  ; -----------------------------------------
  ; Empilhando numero 8
  ldi r24, lo8(8)
  ldi r25, hi8(8)
  push r25
  push r24
  ; Empilhando numero 2
  ldi r24, lo8(2)
  ldi r25, hi8(2)
  push r25
  push r24
  ; Operacao: /
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  rcall div16_unsigned_remainder
  ; Empilhando resultado
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_16bit_decimal
  rcall send_newline
  ; -----------------------------------------
  ; AVISO: Ponto flutuante (1.5) tratado como inteiro
  ; Empilhando numero 1
  ldi r24, lo8(1)
  ldi r25, hi8(1)
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_16bit_decimal
  rcall send_newline
  ; -----------------------------------------
  ; --- Comando V MEM (Store) ---
  ; AVISO: Ponto flutuante (15.0) tratado como inteiro
  ; Empilhando numero 15
  ldi r24, lo8(15)
  ldi r25, hi8(15)
  push r25
  push r24
  pop r24
  pop r25
  ldi r30, lo8(0x0200)
  ldi r31, hi8(0x0200)
  st Z+, r24
  st Z, r25
  ; --- Fim do V MEM ---
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_16bit_decimal
  rcall send_newline
  ; -----------------------------------------
  ; --- Comando MEM (Load) ---
  ldi r30, lo8(0x0200)
  ldi r31, hi8(0x0200)
  ld r24, Z+
  ld r25, Z
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_16bit_decimal
  rcall send_newline
  ; -----------------------------------------
  ; Empilhando numero 3
  ldi r24, lo8(3)
  ldi r25, hi8(3)
  push r25
  push r24
  ; Empilhando numero 4
  ldi r24, lo8(4)
  ldi r25, hi8(4)
  push r25
  push r24
  ; Operacao: +
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  add r24, r22
  adc r25, r23
  ; Empilhando resultado
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_16bit_decimal
  rcall send_newline
  ; -----------------------------------------
  ; Empilhando numero 5
  ldi r24, lo8(5)
  ldi r25, hi8(5)
  push r25
  push r24
  ; Empilhando numero 6
  ldi r24, lo8(6)
  ldi r25, hi8(6)
  push r25
  push r24
  ; Operacao: -
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  sub r24, r22
  sbc r25, r23
  ; Empilhando resultado
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_16bit_decimal
  rcall send_newline
  ; -----------------------------------------
  ; Empilhando numero 2
  ldi r24, lo8(2)
  ldi r25, hi8(2)
  push r25
  push r24
  ; Empilhando numero 2
  ldi r24, lo8(2)
  ldi r25, hi8(2)
  push r25
  push r24
  ; Operacao: ^
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  rcall pow16
  ; Empilhando resultado
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_16bit_decimal
  rcall send_newline
  ; -----------------------------------------
end_program:
  rjmp end_program