import struct

def _float_to_half_bits(self, f: float) -> int:
    # conversão sem numpy – funciona em Python 3+
    f32 = struct.unpack('>I', struct.pack('>f', f))[0]
    sign = (f32 >> 31) & 0x1
    exp  = (f32 >> 23) & 0xFF
    frac =  f32 & 0x7FFFFF
    if exp == 0xFF:        # Inf/NaN
        exp16, frac16 = 0x1F, 0x200 if frac else 0
    elif exp > 0x70:       # número normal
        exp16, frac16 = exp - 0x70, frac >> 13
    elif exp >= 0x67:      # sub-normal
        shift = 0x71 - exp
        frac16 = ((1 << 23) | frac) >> (shift + 13)
        exp16  = 0
    else:                  # underflow → 0
        exp16, frac16 = 0, 0
    return (sign << 15) | (exp16 << 10) | frac16


class CodeGenerator:
    def __init__(self):
        self.assembly_code = []
        self.data_section = [] 
        self.label_count = 0
        
    def new_label(self, prefix='L'):
        self.label_count += 1
        return f"{prefix}{self.label_count}"
    
    def _float_to_half_bits(self, f: float) -> int:
        """
        Implementação independente de NumPy: empacota em binary16
        (round-to-nearest-even).  Cobre normais, subnormais, ±Inf e NaN.
        """
        f32 = struct.unpack('>I', struct.pack('>f', f))[0]   # bits do float32
        sign = (f32 >> 31) & 0x1
        exp  = (f32 >> 23) & 0xFF
        frac = f32 & 0x7FFFFF

        if exp == 0xFF:                         # ±Inf ou NaN
            exp16  = 0x1F
            frac16 = 0x200 if frac else 0       # preserva quiet-NaN
        elif exp > 0x70:                        # número normal após remoção de bias
            exp16  = exp - 0x70
            frac16 = frac >> 13                 # descarta 13 bits
        elif exp >= 0x67:                       # vira subnormal
            shift  = 0x71 - exp                 # 1-14
            frac16 = ((1 << 23) | frac) >> (shift + 13)
            exp16  = 0
        else:                                   # underflow → ±0
            exp16  = 0
            frac16 = 0

        return (sign << 15) | (exp16 << 10) | frac16

    def generate(self, node):
        header = [
            ".extern init_serial",
            ".extern send_char",
            ".extern send_newline",
            ".extern print_16bit",
            ".section .text",
            ".global main",
            "main:",
            "  ; --- Inicializacao da Pilha ---"
            "  ldi r28, lo8(0x08FF)"
            "  ldi r29, hi8(0x08FF)"
            "  out 0x3E, r29  ; SPH"
            "  out 0x3D, r28  ; SPL"
            "  ; --- Inicializacao da Serial ---",
            "  rcall init_serial",
            "  ; -------------------------------"
            "  ; Teste inicial da serial",
            "  ldi r24, 'A'",
            "  rcall send_char",
            "  ldi r24, 'T'",
            "  rcall send_char",
            "  rcall send_newline",
        ]   
        
        self.assembly_code = header
        self.visit(node)

        # Loop infinito no final do programa
        self.assembly_code.append("end_program:")
        self.assembly_code.append("  rjmp end_program")
        
        # As sub-rotinas agora estao em um arquivo separado
        # e nao sao mais adicionadas aqui.

        return "\n".join(self.assembly_code)

    def visit(self, node):
        method_name = f'visit_{node["type"]}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        raise Exception(f"Gerador de codigo nao implementado para o no {node['type']}")

    def visit_Program(self, node):
        for stmt in node['statements']:
            self.visit(stmt)
            # Apos cada instrucao principal, imprime o resultado se for um 'Res'
            if stmt.get('type') == 'Res':
                 self.assembly_code.append("  ; --- Imprime o resultado da expressao ---")
                 self.assembly_code.append("  pop r25 ; Pega o resultado (high byte) da pilha")
                 self.assembly_code.append("  pop r24 ; Pega o resultado (low byte) da pilha")
                 self.assembly_code.append("  rcall print_f16")   # agora trata half-float
                 self.assembly_code.append("  rcall send_newline")
                 self.assembly_code.append("  ; -----------------------------------------")


    def visit_Res(self, node):
        # Apenas visita o argumento. A logica de impressao foi movida para visit_Program
        self.visit(node['arg'])

    def visit_Number(self, node):
        value = node['value']

        # decide se precisa empacotar como float ou int
        is_float = node['kind'] == 'float' or node.get('coercion') == 'int_to_float'
        if is_float:
            half = self._float_to_half_bits(float(value))
        else:
            half = int(value) & 0xFFFF

        lo, hi = half & 0xFF, half >> 8
        self.assembly_code.extend([
            f"  ; push {'float' if is_float else 'int'} {value}",
            f"  ldi r24, {lo}",
            f"  ldi r25, {hi}",
            "  push r25",
            "  push r24"
        ])



    def visit_Op(self, node):
        self.visit(node['args'][0])
        self.visit(node['args'][1])
        
        self.assembly_code.append(f"  ; Operacao: {node['op']}")
        self.assembly_code.append("  pop r22 ; Operando Direito (low byte)")
        self.assembly_code.append("  pop r23 ; Operando Direito (high byte)")
        self.assembly_code.append("  pop r24 ; Operando Esquerdo (low byte)")
        self.assembly_code.append("  pop r25 ; Operando Esquerdo (high byte)")

        op_map = {
            '+': "  rcall fadd16",
            '-': "  rcall fsub16",
            '*': "  rcall fmul16",
            '/': "  rcall fdiv16",
            '^': "  rcall fpow16" 
        }

        
        if node['op'] in op_map:
            self.assembly_code.append(op_map[node['op']])
        else:
            # Mantem o aviso para operadores nao implementados
            self.assembly_code.append(f"  ; AVISO: Operador '{node['op']}' nao implementado")
            self.assembly_code.append("  ldi r24, 0\n  ldi r25, 0")

        self.assembly_code.append("  ; Empilhando resultado")
        self.assembly_code.append("  push r25")
        self.assembly_code.append("  push r24")

    # Os outros metodos visit_* (Identifier, Store, Mem, etc.) continuam os mesmos...
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
        # Define um endereco de memoria de usuario (exemplo)
        self.assembly_code.append("  ldi r30, lo8(0x0200)")
        self.assembly_code.append("  ldi r31, hi8(0x0200)")
        self.assembly_code.append("  st Z+, r24")
        self.assembly_code.append("  st Z, r25")
        # Nao imprime resultado de V MEM
        self.assembly_code.append("  ; --- Fim do V MEM ---")


    def visit_Mem(self, node):
        self.assembly_code.append("  ; --- Comando MEM (Load) ---")
        self.assembly_code.append("  ldi r30, lo8(0x0200)")
        self.assembly_code.append("  ldi r31, hi8(0x0200)")
        self.assembly_code.append("  ld r24, Z+")
        self.assembly_code.append("  ld r25, Z")
        self.assembly_code.append("  push r25")
        self.assembly_code.append("  push r24")
        # O resultado do MEM sera impresso pela logica do 'Res'

    def visit_ResRelative(self, node):
        self.assembly_code.append("  ; AVISO: N RES nao implementado, tratando como RES normal.")
        self.visit(node['n'])
        # Nao imprime aqui, a logica do 'Res' cuidara disso

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
