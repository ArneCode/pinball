# visitor that walks the tree and evaluates it
from typing import Dict, Union
from node import CodeBlockNode, FuncCallNode, IfNode, NodeVisitor, SymbolNode, TwoSideOpNode, WordNode, NumberNode, VarNode, VarDefNode, AssignNode, StringNode, whileNode


Value = Union[int, float, str, bool, None]
class EvalVisitor(NodeVisitor[Value]):
    # variables
    variables: Dict[str, Value] = {}
    
    def __init__(self, variables: Dict[str, Value] = {}):
        self.variables = variables

    def visit_two_side_op(self, node: TwoSideOpNode) -> Value:
        left = node.left.accept(self)
        right = node.right.accept(self)
        assert left is not None and right is not None
#        if isinstance(left, str) or isinstance(right, str):
#            raise Exception("cannot apply operator to string")
        if node.sign == "+":
            if isinstance(left, str) or isinstance(right, str):
                return str(left) + str(right)
            return left + right
        if node.sign == "*":
            if isinstance(left, str) and isinstance(right, int):
                return left * right
            assert not isinstance(left, str) and not isinstance(right, str)
            return left * right
        assert not isinstance(left, str) and not isinstance(right, str)
        if node.sign == "-":
            return left - right

        if node.sign == "/":
            return left / right
        if node.sign == "==":
            return left == right
        if node.sign == "!=":
            return left != right
        if node.sign == "<=":
            return left <= right
        if node.sign == ">=":
            return left >= right
        if node.sign == "<":
            return left < right
        if node.sign == ">":
            return left > right
        raise Exception("unknown operator")
    
    def visit_code_block(self, node: CodeBlockNode) -> Value:
        for statement in node.statements:
            statement.accept(self)
        return None
    
    def visit_if(self, node: IfNode) -> Value:
        if node.condition.accept(self):
            node.then_block.accept(self)
            return None
        for cond, block in zip(node.elif_conds, node.elif_blocks):
            if cond.accept(self):
                block.accept(self)
                return None
        if node.else_block is not None:
            node.else_block.accept(self)
        return None
    
    def visit_word(self, node: WordNode) -> Value:
        if node.word in self.variables:
            return self.variables[node.word]
        raise Exception("unknown variable")
    
    def visit_symbol(self, node: SymbolNode) -> Value:
        raise Exception("cannot evaluate symbol")
    
    def visit_number(self, node: NumberNode) -> Value:
        return node.value
    
    def visit_var(self, node: VarNode) -> Value:
        if node.name in self.variables:
            return self.variables[node.name]
        
        raise Exception("unknown variable")
    
    def visit_var_def(self, node: VarDefNode) -> Value:
        if node.value is None:
            self.variables[node.name] = None
        else:
            self.variables[node.name] = node.value.accept(self)
        return None
    
    def visit_assign(self, node: AssignNode) -> Value:
        self.variables[node.var.name] = node.value.accept(self)
        return None
    
    def visit_func_call(self, node: FuncCallNode) -> Value:
        if node.func.name == "print":
            print(node.arg.accept(self))
            return None
        raise Exception("unknown function")
    def visit_string(self, node: StringNode) -> Value:
        return node.string
    
    def visit_while(self, node: whileNode) -> Value:
        while node.condition.accept(self):
            node.then_block.accept(self)
        return None

