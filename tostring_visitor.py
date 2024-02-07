from __future__ import annotations
from typing import Dict, Union
from .node import CodeFileNode, FuncArgNode, FunctionDefNode, NodeVisitor, ReturnNode, StringNode, TwoSideOpNode, Node, CodeBlockNode, IfNode, UnaryOpNode, WordNode, SymbolNode, NumberNode, VarNode, VarDefNode, AssignNode, FuncCallNode, whileNode

# walks the tree and makes string representation of it

class ToStringVisitor(NodeVisitor[str]):
    indent: int = 0

    def __init__(self, indent: int = 0):
        self.indent = indent

    def increase_indent(self) -> ToStringVisitor:
        return ToStringVisitor(self.indent + 1)

    def visit_two_side_op(self, node: TwoSideOpNode) -> str:
        return f"{node.left.accept(self)} {node.sign} {node.right.accept(self)}"
    
    def visit_unary_op(self, node: UnaryOpNode) -> str:
        return f"{node.sign}{node.node.accept(self)}"

    def visit_code_block(self, node: CodeBlockNode) -> str:
        print(f"visiting code block, indent: {self.indent}")
        inner = "{\n"
        for statement in node.statements:
            inner += "\t"*(self.indent+1) + statement.accept(self.increase_indent())+"\n"
        return inner + "\t"*self.indent +"}"
        #return "\n".join(["*"*self.indent + statement.accept(self.increase_indent()) for statement in node.statements])

    def visit_if(self, node: IfNode) -> str:
        result = f"if {node.condition.accept(self)}"
        result += f"{node.then_block.accept(self)}"
        for i, (cond, block) in enumerate(zip(node.elif_conds, node.elif_blocks)):
            result += f"elif {cond.accept(self)}"
            result += f"{block.accept(self)}"
        if node.else_block is not None:
            result += f"else"
            result += f"{node.else_block.accept(self)}"
        return result

    def visit_word(self, node: WordNode) -> str:
        return node.word

    def visit_symbol(self, node: SymbolNode) -> str:
        return node.symbol

    def visit_number(self, node: NumberNode) -> str:
        return str(node.value)

    def visit_var(self, node: VarNode) -> str:
        return node.name

    def visit_var_def(self, node: VarDefNode) -> str:
        if node.value is None:
            return f"let {node.name}"
        return f"let {node.name} = {node.value.accept(self)}"
    
    def visit_assign(self, node: AssignNode) -> str:
        return f"{node.var.accept(self)} = {node.value.accept(self)}"
    
    def visit_func_call(self, node: FuncCallNode) -> str:
        return f"{node.func.accept(self)}({', '.join([arg.accept(self) for arg in node.args])})"
    def visit_string(self, node: StringNode) -> str:
        return f'"{node.string}"'
    def visit_while(self, node: whileNode) -> str:
        return f"while {node.condition.accept(self)} {node.then_block.accept(self)}"
    def visit_func_arg(self, node: FuncArgNode) -> str:
        return f"{node.name}"
    def visit_function_def(self, node: FunctionDefNode) -> str:
        return f"def {node.name}({', '.join([arg.accept(self) for arg in node.args])}) {node.body.accept(self)}"
    def visit_code_file(self, node: CodeFileNode) -> str:
        return "\n".join([function_def.accept(self) for function_def in node.functions.values()])
    def visit_return(self, node: ReturnNode) -> str:
        if node.value is None:
            return "return"
        return f"return {node.value.accept(self)}"
    