class SemanticAnalyzer:
    def __init__(self):
        self.symbol_table = {}
        self.errors = []

    def error(self, message, node):
        line = node.get('line', '?') # Pega a linha do nó, se existir
        self.errors.append(f"Erro Semântico (linha {line}): {message}")

    def visit(self, node):
        method_name = f'visit_{node["type"]}'
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node):
        self.error(f"Nó do tipo '{node['type']}' não possui método de visitação.", node)
        return {'type': 'error'}

    def visit_Program(self, node):
        # Esta função será chamada a partir do loop principal em main.py
        # para cada instrução, então não precisamos iterar aqui.
        pass

    def visit_Res(self, node):
        return self.visit(node['arg'])

    def visit_Number(self, node):
        return {'type': node['kind']}

    def visit_Identifier(self, node):
        var_name = node['name']
        if var_name not in self.symbol_table:
            self.error(f"Variável '{var_name}' não definida.", node)
            return {'type': 'error'}
        return self.symbol_table[var_name]

    def visit_Mem(self, node):
        return {'type': 'float'}

    def visit_Op(self, node):
        left_type_info = self.visit(node['args'][0])
        right_type_info = self.visit(node['args'][1])

        left_type = left_type_info.get('type')
        right_type = right_type_info.get('type')

        if left_type == 'error' or right_type == 'error':
            return {'type': 'error'}
        
        if node['op'] == '/':
            if left_type == 'int':
                node['args'][0]['coercion'] = 'int_to_float'
            if right_type == 'int':
                node['args'][1]['coercion'] = 'int_to_float'
            return {'type': 'float'}

        if left_type == 'float' or right_type == 'float':
            if left_type == 'int':
                node['args'][0]['coercion'] = 'int_to_float'
            if right_type == 'int':
                node['args'][1]['coercion'] = 'int_to_float'
            return {'type': 'float'}
        
        return {'type': 'int'}

    def visit_Store(self, node):
        val_info = self.visit(node['val'])
        if val_info.get('type') == 'error':
            self.error("Valor inválido para armazenamento em V MEM.", node)
        return {'type': 'void'}

    def visit_ResRelative(self, node):
        n_info = self.visit(node['n'])
        if n_info.get('type') != 'int':
            self.error("N RES requer um argumento inteiro.", node)
        return {'type': 'void'}

    def visit_If(self, node):
        cond_info = self.visit(node['cond'])
        if cond_info.get('type') == 'error':
            self.error("Condição inválida no 'if'.", node)
        
        self.visit(node['then_b'])
        if node['else_b']:
            self.visit(node['else_b'])
        
        return {'type': 'void'}

    def visit_For(self, node):
        var_name = node['id']['name']
        
        start_info = self.visit(node['start'])
        end_info = self.visit(node['end'])

        if start_info.get('type') != 'int' or end_info.get('type') != 'int':
            self.error("Início e fim do 'for' devem ser inteiros.", node)

        self.symbol_table[var_name] = {'type': 'int'}
        self.visit(node['body'])
        del self.symbol_table[var_name]

        return {'type': 'void'}