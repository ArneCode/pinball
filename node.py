from abc import ABC
from typing import List, Optional


class Node(ABC):
    pass


class PlusNode(Node):
    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f"({self.right} + {self.left})"


class MinusNode(Node):
    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f"({self.left} - {self.right})"


class TimesNode(Node):
    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f"({self.left} * {self.right})"


class DivNode(Node):
    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f"({self.left} / {self.right})"


class NumberNode(Node):
    value: float

    def __init__(self, value: float):
        self.value = value

    def __str__(self) -> str:
        return str(self.value)


class WordNode(Node):
    word: str

    def __init__(self, word: str):
        self.word = word

    def __str__(self) -> str:
        return self.word


class SymbolNode(Node):
    symbol: str

    def __init__(self, symbol: str):
        self.symbol = symbol

    def __str__(self) -> str:
        return self.symbol


class VarNode(Node):
    name: str

    def __init__(self, name: str):
        self.name = name

    def __str__(self) -> str:
        return self.name


class AssignNode(Node):
    var: VarNode
    value: Node

    def __init__(self, var: VarNode, value: Node):
        self.var = var
        self.value = value

    def __str__(self) -> str:
        return f"{self.var} = {self.value}"


class FuncCallNode(Node):
    func: VarNode
    arg: Node

    def __init__(self, func: VarNode, arg: Node):
        self.func = func
        self.arg = arg

    def __str__(self) -> str:
        return f"{self.func}({self.arg})"


class CodeBlockNode(Node):
    statements: List[Node]

    def __init__(self, statements: List[Node]):
        self.statements = statements

    def __str__(self) -> str:
        return "{\n" + "; \n".join(map(str, self.statements)) + "}"


class VarDefNode(Node):
    name: str
    value: Optional[Node]

    def __init__(self, name: str, value: Optional[Node] = None):
        self.name = name
        self.value = value

    def __str__(self) -> str:
        return f"let {self.name} = {self.value}"


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

    def __str__(self) -> str:
        return f"if ({self.condition}) {self.then_block} {' '.join(map(lambda x: f'else if ({x[0]}) {x[1]}', zip(self.elif_conds, self.elif_blocks)))} {'else ' + str(self.else_block) if self.else_block else ''}"


class EqNode(Node):
    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f"{self.left} == {self.right}"


class LessOrEqNode(Node):
    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f"{self.left} <= {self.right}"


class GreaterOrEqNode(Node):
    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f"{self.left} >= {self.right}"


class NeqNode(Node):
    left: Node
    right: Node

    def __init__(self, left: Node, right: Node):
        self.left = left
        self.right = right

    def __str__(self) -> str:
        return f"{self.left} != {self.right}"