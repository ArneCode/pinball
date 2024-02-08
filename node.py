"""
Contains the AST nodes for the Ballang language.

The nodes are used to represent the parsed code. They are used to represent the code in a way that is easy to work with and manipulate.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, TypeVar


# T is a generic type variable. It is used to allow the NodeVisitor to return different types depending on the node it visits.
T = TypeVar('T')
class Node(ABC):
    """
    Interface for AST nodes
    """
    @abstractmethod
    def accept(self, visitor: NodeVisitor[T]) -> T:
        """
        Accept a visitor

        Args:
            visitor (NodeVisitor[T]): the visitor to accept

        Returns:
            T: the result of the visit
        """
        pass

    def __str__(self) -> str:
        """
        Convert the node to a string
        """
        # This is a workaround to avoid circular imports
        from .tostring_visitor import ToStringVisitor
        return self.accept(ToStringVisitor())


class TwoSideOpNode(Node):
    """
    A node representing a two sided operator
    
    Attributes:
        left (Node): the left side of the operator
        right (Node): the right side of the operator
        sign (str): the operator symbol
    """
    left: Node
    right: Node
    sign: str

    def __init__(self,sign: str,  left: Node, right: Node):
        """
        Create a new TwoSideOpNode

        Args:
            sign (str): the operator symbol
            left (Node): the left side of the operator
            right (Node): the right side of the operator
        """
        self.sign = sign
        self.left = left
        self.right = right

    def accept(self, visitor: NodeVisitor[T]) -> T:
        """
        Accept a visitor

        Args:
            visitor (NodeVisitor[T]): the visitor to accept

        Returns:
            T: the result of the visit
        """
        return visitor.visit_two_side_op(self)
class UnaryOpNode(Node):
    """
    A node representing a unary operator
    
    Attributes:
        node (Node): the operand of the operator
        sign (str): the operator symbol
    """
    sign: str
    node: Node

    def __init__(self, sign: str, node: Node):
        """
        Create a new UnaryOpNode

        Args:
            sign (str): the operator symbol
            node (Node): the operand of the operator
        """
        self.sign = sign
        self.node = node
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        """
        Accept a visitor

        Args:
            visitor (NodeVisitor[T]): the visitor to accept

        Returns:
            T: the result of the visit
        """
        return visitor.visit_unary_op(self)


class NumberNode(Node):
    """
    Represents a node that holds a numeric value.
    """

    value: float

    def __init__(self, value: float):
        self.value = value
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_number(self)


class WordNode(Node):
    """
    Represents a node containing a word.
    """

    word: str

    def __init__(self, word: str):
        self.word = word

    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_word(self)

class StringNode(Node):
    """
    Represents a node that holds a string value.
    """

    string: str

    def __init__(self, string: str):
        self.string = string

    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_string(self)

class SymbolNode(Node):
    """
    Represents a node in the abstract syntax tree that holds a symbol. This is only used during parsing.
    """

    symbol: str

    def __init__(self, symbol: str):
        self.symbol = symbol
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_symbol(self)


class VarNode(Node):
    """
    Represents a node in the abstract syntax tree that holds a variable name.

    Attributes:
        name (str): the name of the variable
    """
    name: str

    def __init__(self, name: str):
        self.name = name

    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_var(self)


class AssignNode(Node):
    """
    Represents a node in the abstract syntax tree that holds an assignment.
    
    Attributes:
        var (VarNode): the variable to assign to
        value (Node): the value to assign
    """
    var: VarNode
    value: Node

    def __init__(self, var: VarNode, value: Node):
        self.var = var
        self.value = value
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_assign(self)


class FuncCallNode(Node):
    """
    Represents a node in the abstract syntax tree that holds a function call.

    Attributes:
        func (VarNode): the function to call
        args (List[Node]): the arguments to pass to the function
    """
    func: VarNode
    args: List[Node]

    def __init__(self, func: VarNode, args: List[Node]):
        self.func = func
        self.args = args
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_func_call(self)


class CodeBlockNode(Node):
    """
    Represents a node in the abstract syntax tree that holds a block of code.

    Attributes:
        statements (List[Node]): the statements in the block
    """
    statements: List[Node]

    def __init__(self, statements: List[Node]):
        self.statements = statements
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_code_block(self)


class VarDefNode(Node):
    """
    Represents a node in the abstract syntax tree that holds a variable definition.

    Attributes:
        name (str): the name of the variable
        value (Optional[Node]): the value to assign to the variable
    """
    name: str
    value: Optional[Node]

    def __init__(self, name: str, value: Optional[Node] = None):
        self.name = name
        self.value = value
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_var_def(self)


class IfNode(Node):
    """
    Represents a node in the abstract syntax tree that holds an if statement.

    Attributes:
        condition (Node): the condition of the if statement
        then_block (CodeBlockNode): the block to execute if the condition is true
        elif_conds (List[Node]): the conditions of the elif statements
        elif_blocks (List[CodeBlockNode]): the blocks to execute if the elif conditions are true
        else_block (Optional[CodeBlockNode]): the block to execute if none of the conditions are true
    """
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
    """
    Represents a node in the abstract syntax tree that holds a while loop.

    Attributes:
        condition (Node): the condition of the while loop
        then_block (CodeBlockNode): the block to execute while the condition is true
    """
    condition: Node
    then_block: CodeBlockNode

    def __init__(self, condition: Node, then_block: CodeBlockNode):
        self.condition = condition
        self.then_block = then_block
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_while(self)
class FuncArgNode(Node):
    """
    Represents a node in the abstract syntax tree that holds a function argument.
    """
    name: str

    def __init__(self, name: str):
        self.name = name
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_func_arg(self)
class ReturnNode(Node):
    """
    Represents a node in the abstract syntax tree that holds a return statement.

    Attributes:
        value (Optional[Node]): the value to return
    """
    value: Optional[Node]

    def __init__(self, value: Optional[Node] = None):
        self.value = value
    
    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_return(self)
class FunctionDefNode(Node):
    """
    Represents a node in the abstract syntax tree that holds a function definition.

    Attributes:
        name (str): the name of the function
        body (CodeBlockNode): the body of the function
        args (List[FuncArgNode]): the arguments of the function
    """
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
    """
    Represents a node in the abstract syntax tree that holds a file of code.

    Attributes:
        functions (Dict[str, FunctionDefNode]): the functions in the file
    """
    functions: Dict[str, FunctionDefNode]

    def __init__(self, functions: List[FunctionDefNode]):
        self.functions = {func.name: func for func in functions}

    def accept(self, visitor: NodeVisitor[T]) -> T:
        return visitor.visit_code_file(self)
    
    

# Had To place this in this file because of circular imports. Otherwise I couldn't use type hinting in nodevisitor.py
class NodeVisitor(Generic[T], ABC):
    """
    Interface for AST node visitors
    """
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