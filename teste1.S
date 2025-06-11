.equ user_memory, 0x0100

.section .text
.global main
main:
  ; --- Inicializacao da Pilha ---
  ldi r28, lo8(0x08FF) ; RAMEND low byte
  ldi r29, hi8(0x08FF) ; RAMEND high byte
  out 0x3E, r29      ; Endereco I/O do SPH
  out 0x3D, r28      ; Endereco I/O do SPL
  ; ----------------------------
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
  pop r24 ; Limpa lixo da pilha
  pop r25 ; Limpa lixo da pilha
  ; Empilhando numero 5
  ldi r24, lo8(5)
  ldi r25, hi8(5)
  push r25
  push r24
  ; Empilhando numero 2
  ldi r24, lo8(2)
  ldi r25, hi8(2)
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
  pop r24 ; Limpa lixo da pilha
  pop r25 ; Limpa lixo da pilha
  ; Empilhando numero 6
  ldi r24, lo8(6)
  ldi r25, hi8(6)
  push r25
  push r24
  ; Empilhando numero 2
  ldi r24, lo8(2)
  ldi r25, hi8(2)
  push r25
  push r24
  ; Operacao: %
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  ; AVISO: Operador '%' nao implementado
  ldi r24, 0
  ldi r25, 0
  ; Empilhando resultado
  push r25
  push r24
  pop r24 ; Limpa lixo da pilha
  pop r25 ; Limpa lixo da pilha
  ; Empilhando numero 2
  ldi r24, lo8(2)
  ldi r25, hi8(2)
  push r25
  push r24
  ; Empilhando numero 3
  ldi r24, lo8(3)
  ldi r25, hi8(3)
  push r25
  push r24
  ; Operacao: ^
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  ; AVISO: Operador '^' nao implementado
  ldi r24, 0
  ldi r25, 0
  ; Empilhando resultado
  push r25
  push r24
  pop r24 ; Limpa lixo da pilha
  pop r25 ; Limpa lixo da pilha
  ; Empilhando numero 8
  ldi r24, lo8(8)
  ldi r25, hi8(8)
  push r25
  push r24
  ; Empilhando numero 4
  ldi r24, lo8(4)
  ldi r25, hi8(4)
  push r25
  push r24
  ; Operacao: *
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  rcall mult16
  ; Empilhando resultado
  push r25
  push r24
  pop r24 ; Limpa lixo da pilha
  pop r25 ; Limpa lixo da pilha
  ; Empilhando numero 9
  ldi r24, lo8(9)
  ldi r25, hi8(9)
  push r25
  push r24
  ; Empilhando numero 3
  ldi r24, lo8(3)
  ldi r25, hi8(3)
  push r25
  push r24
  ; Operacao: /
  pop r22 ; Operando Direito (low byte)
  pop r23 ; Operando Direito (high byte)
  pop r24 ; Operando Esquerdo (low byte)
  pop r25 ; Operando Esquerdo (high byte)
  rcall div16
  ; Empilhando resultado
  push r25
  push r24
  pop r24 ; Limpa lixo da pilha
  pop r25 ; Limpa lixo da pilha
  ; Empilhando numero 1
  ldi r24, lo8(1)
  ldi r25, hi8(1)
  push r25
  push r24
  pop r24 ; Limpa lixo da pilha
  pop r25 ; Limpa lixo da pilha
  ; --- Comando V MEM (Store) ---
  ; Empilhando numero 20
  ldi r24, lo8(20)
  ldi r25, hi8(20)
  push r25
  push r24
  pop r24
  pop r25
  ; Armazena em 'user_memory' (0x0100)
  ldi r30, lo8(user_memory)
  ldi r31, hi8(user_memory)
  st Z+, r24
  st Z, r25
  pop r24 ; Limpa lixo da pilha
  pop r25 ; Limpa lixo da pilha
  ; --- Comando MEM (Load) ---
  ; Carrega de 'user_memory' (0x0100)
  ldi r30, lo8(user_memory)
  ldi r31, hi8(user_memory)
  ld r24, Z+
  ld r25, Z
  ; Empilha o valor carregado
  push r25
  push r24
  pop r24 ; Limpa lixo da pilha
  pop r25 ; Limpa lixo da pilha
end_program:
  rjmp end_program ; Loop infinito

; --- Sub-rotinas de 16 bits ---
; Multiplicacao 16x16: (r25:r24) * (r23:r22) -> r25:r24
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

; Divisao 16/16: (r25:r24) / (r23:r22) -> r25:r24 (quociente)
div16:
  clr r26
  clr r27
  ldi r18, 17
div16_loop:
  rol r24
  rol r25
  rol r26
  rol r27
  dec r18
  cp r25, r23
  cpc r24, r22
  brlo div16_skip
  sub r24, r22
  sbc r25, r23
div16_skip:
  brne div16_loop
  com r26
  movw r24, r26
  ret
