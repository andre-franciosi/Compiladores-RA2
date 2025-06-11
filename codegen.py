# codegen.py

class CodeGenerator:
    def __init__(self):
        self.assembly_code = []
        self.data_section = [] 
        self.label_count = 0
        
    def new_label(self, prefix='L'):
        self.label_count += 1
        return f"{prefix}{self.label_count}"

    def generate(self, node):
        header = [
            ".equ user_memory, 0x0100", 
            "",
            ".section .text",
            ".global main",
            "main:",
            "  ; --- Inicializacao da Pilha ---",
            "  ldi r28, lo8(0x08FF) ; RAMEND low byte",
            "  ldi r29, hi8(0x08FF) ; RAMEND high byte",
            "  out 0x3E, r29      ; Endereco I/O do SPH",
            "  out 0x3D, r28      ; Endereco I/O do SPL",
            "  ; ----------------------------"
        ]
        
        self.assembly_code = header
        self.visit(node)

        self.assembly_code.append("end_program:")
        self.assembly_code.append("  rjmp end_program ; Loop infinito")
        
        # ADICIONADO DE VOLTA: Inclui as sub-rotinas no final do arquivo
        self.add_subroutines()

        return "\n".join(self.assembly_code)

    # --- ADICIONE ESTA FUNÇÃO DE VOLTA NO FINAL DA CLASSE ---
    def add_subroutines(self):
        subroutines = """
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
"""
        self.assembly_code.append(subroutines)

    # ... (todas as suas outras funções visit_* continuam aqui, sem alterações) ...
    def visit(self, node):
        method_name = f'visit_{node["type"]}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"Gerador de codigo nao implementado para o no {node['type']}")

    def visit_Program(self, node):
        for stmt in node['statements']:
            self.visit(stmt)
            if stmt.get('type') == 'Res':
                 self.assembly_code.append("  pop r24 ; Limpa lixo da pilha")
                 self.assembly_code.append("  pop r25 ; Limpa lixo da pilha")

    def visit_Res(self, node):
        self.visit(node['arg'])

    def visit_Number(self, node):
        value = node['value']
        if node.get('coercion') == 'int_to_float' or node['kind'] == 'float':
             self.assembly_code.append(f"  ; AVISO: Ponto flutuante ({value}) tratado como inteiro")
             value = int(value)

        self.assembly_code.append(f"  ; Empilhando numero {value}")
        self.assembly_code.append(f"  ldi r24, lo8({value})")
        self.assembly_code.append(f"  ldi r25, hi8({value})")
        self.assembly_code.append("  push r25")
        self.assembly_code.append("  push r24")

    def visit_Op(self, node):
        self.visit(node['args'][0])
        self.visit(node['args'][1])
        
        self.assembly_code.append(f"  ; Operacao: {node['op']}")
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
            self.assembly_code.append(f"  ; AVISO: Operador '{node['op']}' nao implementado")
            self.assembly_code.append("  ldi r24, 0\n  ldi r25, 0")

        self.assembly_code.append("  ; Empilhando resultado")
        self.assembly_code.append("  push r25")
        self.assembly_code.append("  push r24")

    def visit_Identifier(self, node):
        self.assembly_code.append(f"  ; Carregando ID '{node['name']}' (placeholder)")
        self.assembly_code.append("  ldi r24, 0")
        self.assembly_code.append("  ldi r25, 0")
        self.assembly_code.append("  push r25")
        self.assembly_code.append("  push r24")
    
    def visit_Store(self, node):
        self.assembly_code.append("  ; --- Comando V MEM (Store) ---")
        self.visit(node['val'])
        self.assembly_code.append("  pop r24")
        self.assembly_code.append("  pop r25")
        self.assembly_code.append("  ; Armazena em 'user_memory' (0x0100)")
        self.assembly_code.append("  ldi r30, lo8(user_memory)")
        self.assembly_code.append("  ldi r31, hi8(user_memory)")
        self.assembly_code.append("  st Z+, r24")
        self.assembly_code.append("  st Z, r25")

    def visit_Mem(self, node):
        self.assembly_code.append("  ; --- Comando MEM (Load) ---")
        self.assembly_code.append("  ; Carrega de 'user_memory' (0x0100)")
        self.assembly_code.append("  ldi r30, lo8(user_memory)")
        self.assembly_code.append("  ldi r31, hi8(user_memory)")
        self.assembly_code.append("  ld r24, Z+")
        self.assembly_code.append("  ld r25, Z")
        self.assembly_code.append("  ; Empilha o valor carregado")
        self.assembly_code.append("  push r25")
        self.assembly_code.append("  push r24")
    
    def visit_ResRelative(self, node):
        self.assembly_code.append("  ; AVISO: N RES nao implementado, tratando como RES normal.")
        self.visit(node['n'])
        self.assembly_code.append("  pop r24")
        self.assembly_code.append("  pop r25")

    def visit_If(self, node):
        else_label = self.new_label("ELSE")
        end_if_label = self.new_label("END_IF")

        self.assembly_code.append("  ; --- Estrutura IF ---")
        self.visit(node['cond'])
        
        self.assembly_code.append("  ; Verifica se o resultado da condicao e zero")
        self.assembly_code.append("  pop r24")
        self.assembly_code.append("  pop r25")
        self.assembly_code.append("  or r24, r25")
        
        false_jump_target = else_label if node.get('else_b') else end_if_label
        
        self.assembly_code.append(f"  breq {false_jump_target}")
        
        self.visit(node['then_b'])
        self.assembly_code.append(f"  rjmp {end_if_label}")

        if node.get('else_b'):
            self.assembly_code.append(f"{else_label}:")
            self.visit(node['else_b'])
        
        self.assembly_code.append(f"{end_if_label}:")
        self.assembly_code.append("  ; --- Fim do IF ---")

    def visit_For(self, node):
        start_loop_label = self.new_label("FOR_START")
        end_loop_label = self.new_label("FOR_END")
        
        self.assembly_code.append(f"  ; --- Estrutura FOR ({node['id']['name']}) ---")
        self.visit(node['start'])
        self.assembly_code.append("  pop r20")
        self.assembly_code.append("  pop r21")

        self.assembly_code.append(f"{start_loop_label}:")
        self.visit(node['end'])
        self.assembly_code.append("  pop r22")
        self.assembly_code.append("  pop r23")

        self.assembly_code.append("  cp r20, r22")
        self.assembly_code.append("  cpc r21, r23")
        self.assembly_code.append(f"  brge {end_loop_label}")

        self.visit(node['body'])

        self.assembly_code.append("  adiw r20, 1")
        self.assembly_code.append(f"  rjmp {start_loop_label}")

        self.assembly_code.append(f"{end_loop_label}:")
        self.assembly_code.append("  ; --- Fim do FOR ---")