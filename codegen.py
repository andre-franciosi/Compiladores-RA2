# codegen.py

class CodeGenerator:
    def __init__(self):
        self.assembly_code = []
        self.data_section = []
        self.label_count = 0
        # Adiciona uma variável de memória para os comandos MEM e V MEM
        self.data_section.append("user_memory: .byte 2  ; 2 bytes (16 bits) para V/MEM")

    def new_label(self, prefix='L'):
        self.label_count += 1
        return f"{prefix}{self.label_count}"

    def generate(self, node):
        # Setup inicial do código Assembly
        header = [
            ".section .text",
            ".global main",
            "main:",
            "  ; --- Inicialização da Pilha ---",
            "  ldi r28, lo8(RAMEND)",
            "  ldi r29, hi8(RAMEND)",
            "  out SPH, r29",
            "  out SPL, r28",
            "  ; ----------------------------"
        ]
        self.assembly_code.extend(header)
        
        # Visita a AST para gerar o código principal
        self.visit(node)

        # Final do programa
        self.assembly_code.append("end_program:")
        self.assembly_code.append("  rjmp end_program ; Loop infinito")

        # Adiciona sub-rotinas auxiliares
        self.add_subroutines()

        # Monta o arquivo final com a seção de dados no topo
        final_code = [".section .data"] + self.data_section + [""] + self.assembly_code
        return "\n".join(final_code)

    def visit(self, node):
        method_name = f'visit_{node["type"]}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"Gerador de código não implementado para o nó {node['type']}")

    def visit_Program(self, node):
        for stmt in node['statements']:
            self.visit(stmt)
            # Limpa o resultado da expressão da pilha para evitar que se acumule
            # Cada instrução deve deixar a pilha como a encontrou, a menos que seja um resultado final
            if stmt.get('type') == 'Res':
                 self.assembly_code.append("  pop r24 ; Limpa lixo da pilha")
                 self.assembly_code.append("  pop r25 ; Limpa lixo da pilha")

    def visit_Res(self, node):
        self.visit(node['arg'])
        # O resultado já está no topo da pilha. A limpeza é feita no nó do Programa.

    def visit_Number(self, node):
        value = node['value']
        if node.get('coercion') == 'int_to_float' or node['kind'] == 'float':
             self.assembly_code.append(f"  ; AVISO: Ponto flutuante ({value}) tratado como inteiro")
             value = int(value)

        self.assembly_code.append(f"  ; Empilhando número {value}")
        self.assembly_code.append(f"  ldi r24, lo8({value})")
        self.assembly_code.append(f"  ldi r25, hi8({value})")
        self.assembly_code.append("  push r25")
        self.assembly_code.append("  push r24")

    def visit_Op(self, node):
        self.visit(node['args'][0])
        self.visit(node['args'][1])
        
        self.assembly_code.append(f"  ; Operação: {node['op']}")
        self.assembly_code.append("  pop r22 ; Operando Direito (low byte)")
        self.assembly_code.append("  pop r23 ; Operando Direito (high byte)")
        self.assembly_code.append("  pop r24 ; Operando Esquerdo (low byte)")
        self.assembly_code.append("  pop r25 ; Operando Esquerdo (high byte)")

        op_map = {
            '+': "  add r24, r22\n  adc r25, r23",
            '-': "  sub r24, r22\n  sbc r25, r23",
            '*': "  rcall mult16",
            '/': "  rcall div16"
        }
        
        if node['op'] in op_map:
            self.assembly_code.append(op_map[node['op']])
        else:
            self.assembly_code.append(f"  ; AVISO: Operador '{node['op']}' não implementado para geração de código")
            # Devolve um zero para não quebrar a pilha
            self.assembly_code.append("  ldi r24, 0\n  ldi r25, 0")

        self.assembly_code.append("  ; Empilhando resultado")
        self.assembly_code.append("  push r25")
        self.assembly_code.append("  push r24")

    def visit_Identifier(self, node):
        # Para loops 'for'. Carrega o valor da variável de loop.
        # Esta é uma implementação simplificada que requer uma área de memória para a variável.
        # Por enquanto, vamos empilhar 0 como um placeholder.
        self.assembly_code.append(f"  ; Carregando ID '{node['name']}' (placeholder)")
        self.assembly_code.append("  ldi r24, 0")
        self.assembly_code.append("  ldi r25, 0")
        self.assembly_code.append("  push r25")
        self.assembly_code.append("  push r24")

    # --- Funções que faltavam ---
    
    def visit_Store(self, node):
        self.assembly_code.append("  ; --- Comando V MEM (Store) ---")
        self.visit(node['val']) # Empilha o valor a ser guardado
        self.assembly_code.append("  pop r24 ; Pega valor da pilha (low byte)")
        self.assembly_code.append("  pop r25 ; Pega valor da pilha (high byte)")
        self.assembly_code.append("  ; Armazena em 'user_memory'")
        self.assembly_code.append("  ldi r30, lo8(user_memory)")
        self.assembly_code.append("  ldi r31, hi8(user_memory)")
        self.assembly_code.append("  st Z+, r24")
        self.assembly_code.append("  st Z, r25")

    def visit_Mem(self, node):
        self.assembly_code.append("  ; --- Comando MEM (Load) ---")
        self.assembly_code.append("  ; Carrega de 'user_memory'")
        self.assembly_code.append("  ldi r30, lo8(user_memory)")
        self.assembly_code.append("  ldi r31, hi8(user_memory)")
        self.assembly_code.append("  ld r24, Z+")
        self.assembly_code.append("  ld r25, Z")
        self.assembly_code.append("  ; Empilha o valor carregado")
        self.assembly_code.append("  push r25")
        self.assembly_code.append("  push r24")
    
    def visit_ResRelative(self, node):
        self.assembly_code.append("  ; AVISO: N RES não implementado, tratando como RES normal.")
        self.visit(node['n']) # Avalia N, mas não usa
        # Limpa o valor de N da pilha
        self.assembly_code.append("  pop r24")
        self.assembly_code.append("  pop r25")

    def visit_If(self, node):
        else_label = self.new_label("ELSE")
        end_if_label = self.new_label("END_IF")

        self.assembly_code.append("  ; --- Estrutura IF ---")
        self.visit(node['cond']) # Avalia a condição
        
        self.assembly_code.append("  ; Verifica se o resultado da condição é zero")
        self.assembly_code.append("  pop r24")
        self.assembly_code.append("  pop r25")
        self.assembly_code.append("  or r24, r25 ; Se r24 | r25 == 0, o número é 0")
        # Se o resultado for zero (falso), pula para o bloco ELSE (ou para o final se não houver ELSE)
        self.assembly_code.append(f"  brne THEN_BLOCK_{else_label}") # Branch if Not Equal (to zero)
        self.assembly_code.append(f"  rjmp {else_label if node['else_b'] else end_if_label}")

        self.assembly_code.append(f"THEN_BLOCK_{else_label}:")
        self.visit(node['then_b'])
        self.assembly_code.append(f"  rjmp {end_if_label}") # Pula o ELSE após executar o THEN

        if node['else_b']:
            self.assembly_code.append(f"{else_label}:")
            self.visit(node['else_b'])
        
        self.assembly_code.append(f"{end_if_label}:")
        self.assembly_code.append("  ; --- Fim do IF ---")

    def visit_For(self, node):
        # Implementação simplificada do FOR. Assume que a variável de loop não é usada dentro do corpo.
        start_loop_label = self.new_label("FOR_START")
        end_loop_label = self.new_label("FOR_END")
        
        self.assembly_code.append(f"  ; --- Estrutura FOR ({node['id']['name']}) ---")
        # Inicializa o contador (vamos usar r20:r21)
        self.visit(node['start'])
        self.assembly_code.append("  pop r20")
        self.assembly_code.append("  pop r21")

        # Avalia o valor final (em r22:r23)
        self.visit(node['end'])
        self.assembly_code.append("  pop r22")
        self.assembly_code.append("  pop r23")

        self.assembly_code.append(f"{start_loop_label}:")
        # Compara o contador com o valor final
        self.assembly_code.append("  cp r20, r22")
        self.assembly_code.append("  cpc r21, r23")
        self.assembly_code.append(f"  brge {end_loop_label} ; Sai do loop se contador >= fim")

        # Corpo do loop
        self.visit(node['body'])

        # Incrementa o contador
        self.assembly_code.append("  adiw r20, 1")
        self.assembly_code.append(f"  rjmp {start_loop_label}")

        self.assembly_code.append(f"{end_loop_label}:")
        self.assembly_code.append("  ; --- Fim do FOR ---")

    def add_subroutines(self):
        # Adiciona subrotinas de 16-bit que podem ser chamadas com RCALL
        subroutines = """
; --- Sub-rotinas de 16 bits ---
; Multiplicação 16x16: (r25:r24) * (r23:r22) -> r25:r24
mult16:
  ; Algoritmo de multiplicação simples (shift-and-add)
  ; Zera o resultado (r27:r26)
  clr r27
  clr r26
  ; Loop 16 vezes
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
  ; Shift left no resultado (r27:r26)
  lsl r26
  rol r27
  dec r18
  brne mult16_loop
  ; Move o resultado para r25:r24
  movw r24, r26
  ret

; Divisão 16/16: (r25:r24) / (r23:r22) -> r25:r24 (quociente), r23:r22 (resto)
div16:
  ; Implementação simples de divisão por subtrações sucessivas
  clr r26  ; Zera o quociente (low byte)
  clr r27  ; Zera o quociente (high byte)
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
  ; O resto já está em r25:r24
  ; Move o quociente (r27:r26) para r25:r24
  movw r24, r26
  ret
"""
        self.assembly_code.append(subroutines)