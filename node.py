from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, TypeVar



T = TypeVar('T')
class Node(ABC):
    @abstractmethod
    def accept(self, visitor: NodeVisitor[T]) -> T:
        pass

    def __str__(self) -> str:
        from .tostring_visitor import ToStringVisitor
        return self.accept(ToStringVisitor())


class TwoSideOpNode(Node):
    left: Node
    right: Node
    sign: str

    def __init__(self,sign: str,  left: Node, right: Node):
        self.sign = sign
        self.left = left
        self.right = right

    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_two_side_op(self)
class UnaryOpNode(Node):
    sign: str
    node: Node

    def __init__(self, sign: str, node: Node):
        self.sign = sign
        self.node = node
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_unary_op(self)


class NumberNode(Node):
    value: float

    def __init__(self, value: float):
        self.value = value
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_number(self)


class WordNode(Node):
    word: str

    def __init__(self, word: str):
        self.word = word

    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_word(self)

class StringNode(Node):
    string: str

    def __init__(self, string: str):
        self.string = string

    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_string(self)

class SymbolNode(Node):
    symbol: str

    def __init__(self, symbol: str):
        self.symbol = symbol
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_symbol(self)


class VarNode(Node):
    name: str

    def __init__(self, name: str):
        self.name = name

    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_var(self)


class AssignNode(Node):
    var: VarNode
    value: Node

    def __init__(self, var: VarNode, value: Node):
        self.var = var
        self.value = value
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_assign(self)


class FuncCallNode(Node):
    func: VarNode
    args: List[Node]

    def __init__(self, func: VarNode, args: List[Node]):
        self.func = func
        self.args = args
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_func_call(self)


class CodeBlockNode(Node):
    statements: List[Node]

    def __init__(self, statements: List[Node]):
        self.statements = statements
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_code_block(self)


class VarDefNode(Node):
    name: str
    value: Optional[Node]

    def __init__(self, name: str, value: Optional[Node] = None):
        self.name = name
        self.value = value
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_var_def(self)


class IfNode(Node):
    condition: Node
    then_block: CodeBlockNode
    elif_conds: List[Node]
    elif_blocks: List[CodeBlockNode]
    else_block: Optional[CodeBlockNode]

    def __init__(self, condition: Node, then_block: CodeBlockNode, elif_conds: List[Node], elif_blocks: List[CodeBlockNode], else_block: Optional[CodeBlockNode]):
        self.condition = condition
        self.then_block = then_block
        self.elif_conds = elif_conds
        self.elif_blocks = elif_blocks
        self.else_block = else_block
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_if(self)

class whileNode(Node):
    condition: Node
    then_block: CodeBlockNode

    def __init__(self, condition: Node, then_block: CodeBlockNode):
        self.condition = condition
        self.then_block = then_block
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_while(self)
class FuncArgNode(Node):
    name: str

    def __init__(self, name: str):
        self.name = name
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_func_arg(self)
class ReturnNode(Node):
    value: Optional[Node]

    def __init__(self, value: Optional[Node] = None):
        self.value = value
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_return(self)
class FunctionDefNode(Node):
    name: str
    body: CodeBlockNode
    args: List[FuncArgNode]

    def __init__(self, name: str, body: CodeBlockNode, args: List[FuncArgNode]):
        self.name = name
        self.body = body
        self.args = args
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_function_def(self)
    
class CodeFileNode(Node):
    functions: Dict[str, FunctionDefNode]

    def __init__(self, functions: List[FunctionDefNode]):
        self.functions = {func.name: func for func in functions}

    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_code_file(self)
    
    

# Had To place this in this file because of circular imports. Otherwise I couldn't use type hinting in nodevisitor.py
class NodeVisitor(Generic[T], ABC):
    @abstractmethod
    def visit_two_side_op(self, node: TwoSideOpNode) -> T:
        pass

    @abstractmethod
    def visit_unary_op(self, node: UnaryOpNode) -> T:
        pass
    
    @abstractmethod
    def visit_code_block(self, node: CodeBlockNode) -> T:
        pass

    @abstractmethod
    def visit_if(self, node: IfNode) -> T:
        pass

    @abstractmethod
    def visit_word(self, node: WordNode) -> T:
        pass

    @abstractmethod
    def visit_string(self, node: StringNode) -> T:
        pass

    @abstractmethod
    def visit_symbol(self, node: SymbolNode) -> T:
        pass

    @abstractmethod
    def visit_number(self, node: NumberNode) -> T:
        pass

    @abstractmethod
    def visit_var(self, node: VarNode) -> T:
        pass

    @abstractmethod
    def visit_var_def(self, node: VarDefNode) -> T:
        pass

    @abstractmethod
    def visit_assign(self, node: AssignNode) -> T:
        pass

    @abstractmethod
    def visit_func_call(self, node: FuncCallNode) -> T:
        pass

    @abstractmethod
    def visit_while(self, node: whileNode) -> T:
        pass

    @abstractmethod
    def visit_func_arg(self, node: FuncArgNode) -> T:
        pass

    @abstractmethod
    def visit_function_def(self, node: FunctionDefNode) -> T:
        pass

    @abstractmethod
    def visit_code_file(self, node: CodeFileNode) -> T:
        pass

    @abstractmethod
    def visit_return(self, node: ReturnNode) -> T:
        pass