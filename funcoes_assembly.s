.section .text

; --- Sub-rotinas de 16 bits ---
; Multiplicacao 16x16: (r25:r24) * (r23:r22) -> r25:r24
mult16:
  ; Algoritmo de multiplicacao simples (shift-and-add)
  ; Zera o resultado (r27:r26) e o contador
  clr r27
  clr r26
  ldi r18, 16
mult16_loop:
  ; Adiciona o multiplicando (r25:r24) ao resultado se LSB do multiplicador for 1
  sbrc r22, 0
  add r26, r24
  sbrc r22, 0
  adc r27, r25
  ; Shift right no multiplicador (r23:r22)
  lsr r23
  ror r22
  ; Shift left no multiplicando para a proxima iteracao
  lsl r24
  rol r25
  dec r18
  brne mult16_loop
  ; Move o resultado para r25:r24
  movw r24, r26
  ret

; Divisao 16/16: (r25:r24) / (r23:r22) -> r25:r24 (quociente), r23:r22 (resto)
div16:
  ; Implementacao simples de divisao por subtracoes sucessivas
  clr r26 ; Zera o quociente (low byte)
  clr r27 ; Zera o quociente (high byte)
div16_loop:
  ; Compara dividendo com divisor
  cp r24, r22
  cpc r25, r23
  brlo div16_end ; Se dividendo < divisor, fim
  ; Subtrai divisor do dividendo
  sub r24, r22
  sbc r25, r23
  ; Incrementa quociente
  adiw r26, 1
  rjmp div16_loop
div16_end:
  ; O resto ja esta em r25:r24
  ; Move o quociente (r27:r26) para r25:r24
  movw r24, r26
  ret