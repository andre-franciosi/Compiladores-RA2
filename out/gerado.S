.extern init_serial
.extern send_char
.extern send_newline
.extern print_16bit
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
  ; push float 3.2
  ldi r24, 102
  ldi r25, 66
  push r25
  push r24
  ; push float 4.8
  ldi r24, 204
  ldi r25, 68
  push r25
  push r24
  ; Operacao: +
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  rcall fadd16
  ; Empilhando resultado
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_f16
  rcall send_newline
  ; -----------------------------------------
  ; push int 2
  ldi r24, 2
  ldi r25, 0
  push r25
  push r24
  ; push int 3
  ldi r24, 3
  ldi r25, 0
  push r25
  push r24
  ; Operacao: ^
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  rcall fpow16
  ; Empilhando resultado
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_f16
  rcall send_newline
  ; -----------------------------------------
  ; push float 8
  ldi r24, 0
  ldi r25, 72
  push r25
  push r24
  ; push float 2
  ldi r24, 0
  ldi r25, 64
  push r25
  push r24
  ; Operacao: /
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  rcall fdiv16
  ; Empilhando resultado
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_f16
  rcall send_newline
  ; -----------------------------------------
  ; push float 1.5
  ldi r24, 0
  ldi r25, 62
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_f16
  rcall send_newline
  ; -----------------------------------------
  ; --- Comando V MEM (Store) ---
  ; push float 15.0
  ldi r24, 128
  ldi r25, 75
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
  rcall print_f16
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
  rcall print_f16
  rcall send_newline
  ; -----------------------------------------
  ; push int 3
  ldi r24, 3
  ldi r25, 0
  push r25
  push r24
  ; push int 4
  ldi r24, 4
  ldi r25, 0
  push r25
  push r24
  ; Operacao: +
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  rcall fadd16
  ; Empilhando resultado
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_f16
  rcall send_newline
  ; -----------------------------------------
  ; push int 5
  ldi r24, 5
  ldi r25, 0
  push r25
  push r24
  ; push int 6
  ldi r24, 6
  ldi r25, 0
  push r25
  push r24
  ; Operacao: -
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  rcall fsub16
  ; Empilhando resultado
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_f16
  rcall send_newline
  ; -----------------------------------------
  ; push int 2
  ldi r24, 2
  ldi r25, 0
  push r25
  push r24
  ; push int 2
  ldi r24, 2
  ldi r25, 0
  push r25
  push r24
  ; Operacao: ^
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  rcall fpow16
  ; Empilhando resultado
  push r25
  push r24
  ; --- Imprime o resultado da expressao ---
  pop r25 ; Pega o resultado (high byte) da pilha
  pop r24 ; Pega o resultado (low byte) da pilha
  rcall print_f16
  rcall send_newline
  ; -----------------------------------------
end_program:
  rjmp end_program