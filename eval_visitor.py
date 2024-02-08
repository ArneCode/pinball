# visitor that walks the tree and evaluates it
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union

from .node import CodeBlockNode, CodeFileNode, FuncArgNode, FuncCallNode, FunctionDefNode, IfNode, NodeVisitor, ReturnNode, SymbolNode, TwoSideOpNode, UnaryOpNode, WordNode, NumberNode, VarNode, VarDefNode, AssignNode, StringNode, whileNode


class Function(ABC):
    """
    Interface for a function
    """
    @abstractmethod
    def call(self, args: List[Value]) -> Value:
        """
        Call the function with the given arguments as a list

        Args:
            args (List[Value]): the arguments

        Returns:
            Value: the return value of the function (if any)
        """
        pass
    def __call__(self, *args: Value) -> Value:
        return self.call(list(args))

class PythonFunction(Function):
    """
    Ballang wrapper for a python function, implementing the Function interface

    Member Variables:
        func (Callable[[List[Value]], Value]): the python function
        name (str): the name of the function (mostly for debugging purposes)
    """
    func: Callable[[List[Value]], Value]
    name: str
    def __init__(self, func: Callable[[List[Value]], Value], name:str = "PythonFunction"):
        """
        Constructor

        Args:
            func (Callable[[List[Value]], Value]): the python function
            name (str, optional): the name of the function (mostly for debugging purposes). Defaults to "PythonFunction".
        """
        self.func = func
        self.name = name
    
    def call(self, args: List[Value]) -> Value:
        """
        Call the function with the given arguments as a list

        Args:
            args (List[Value]): the arguments

        Returns:
            Value: the return value of the function (if any)
        """
        return self.func(args)
    def __str__(self) -> str:
        """
        Do I need to explain this?
        """
        return f"PythonFunction({self.name}, {self.func})"
class BallangFunction(Function):
    """
    Ballang function, implementing the Function interface. Produced using an eval_visitor object

    Member Variables:
        args (List[FuncArgNode]): the arguments
        body (CodeBlockNode): the body of the function
        global_scope (Scope): the global scope the function was defined in
    """
    args: List[FuncArgNode]
    body: CodeBlockNode
    global_scope: Scope
    def __init__(self, args: List[FuncArgNode], body: CodeBlockNode, global_scope: Scope):
        self.args = args
        self.body = body
        self.global_scope = global_scope
    
    def call(self, args: List[Value]) -> Value:
        """
        Call the function with the given arguments as a list

        Args:
            args (List[Value]): the arguments

        Returns:
            Value: the return value of the function (if any)
        """
        if len(args) != len(self.args):
            raise Exception("wrong number of arguments")
        
        # create a new scope for the function for local variables
        local_scope = self.global_scope.create_child({})

        # define the arguments in the local scope
        for (i, arg) in enumerate(self.args):
            if args[i] is None:
                raise Exception("cannot pass None as argument")
            local_scope.define(arg.name, args[i])
        
        # using try-except to catch the return statement
        try:
            # run the body of the function using the visitor pattern
            self.body.accept(EvalVisitor(local_scope))
        except ReturnException as e:
            return e.value
        return None
    def __str__(self) -> str:
        return f"BallangFunction({self.args}, {self.body})"

class ReturnException(Exception):
    """
    Exception to be thrown when a return statement is encountered. Used to break out of the visitor pattern

    Member Variables:
        value (Value): the value to return
    """
    value: Value
    def __init__(self, value: Value):
        self.value = value

# Value represents the types that the visitor expects. Others might work but are not guaranteed. 
# I also use Vec as a type in the pinball code
Value = Union[int, float, str, bool, Function, None]
class Scope:
    """
    Stores Variables and Functions accessible in a certain scope

    Member Variables:
        variables (Dict[str, Value]): the variables in the scope
        parent (Optional[Scope]): the parent scope this scope inherits from, optional

    Args:
        variables (Dict[str, Value]): the variables in the scope (functions are also stored as variables)
        parent (Optional[Scope], optional): the parent scope. Defaults to None.
    """
    variables: Dict[str, Value]
    parent: Optional[Scope]
    def __init__(self, variables: Dict[str, Value], parent: Optional[Scope] = None):
        """
        Constructor
        
        Args:
            variables (Dict[str, Value]): the variables in the scope (functions are also stored as variables)
            parent (Optional[Scope], optional): the parent scope. Defaults to None.
        """
        self.variables = variables
        self.parent = parent
    
    def contains(self, name: str) -> bool:
        """
        Check if a variable with the given name is defined in this scope or any parent scope

        Args:
            name (str): the name of the variable

        Returns:
            bool: True if the variable is defined, False otherwise
        """
        if name in self.variables:
            return True
        if self.parent is not None:
            return self.parent.contains(name)
        return False
    
    def get(self, name: str) -> Value:
        """
        Get the value of a variable with the given name

        Args:
            name (str): the name of the variable

        Returns:
            Value: the value of the variable, either in this scope or a parent scope

        Raises:
            Exception: if the variable is not defined
        """
        if name in self.variables:
            return self.variables[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise Exception(f"unknown variable {name}, {self.variables}")
    
    def set(self, name: str, value: Value) -> None:
        """
        Set the value of a variable with the given name

        Args:
            name (str): the name of the variable
            value (Value): the value to set

        Raises:
            Exception: if the variable is not defined
        """
        if name in self.variables:
            self.variables[name] = value
            return
        if self.parent is not None:
            self.parent.set(name, value)
            return
        raise Exception(f"unknown variable {name}, variables: {self.variables}, value: {value}")
    def define(self, name: str, value: Value) -> None:
        """
        Define a variable with the given name and value

        Args:
            name (str): the name of the variable
            value (Value): the value to set

        Raises:
            Exception: if the variable is already defined
        """
        if name in self.variables:
            raise Exception(f"variable {name} already defined")
        self.variables[name] = value
    
    def create_child(self, vars: Dict[str, Value]) -> Scope:
        """
        Create a child scope which inherits from this one with the given variables

        Args:
            vars (Dict[str, Value]): the variables in the child scope

        Returns:
            Scope: the child scope
        """
        return Scope(vars, self)
    
    def __str__(self) -> str:
        return f"Scope({self.variables}, parent={self.parent})"

class EvalVisitor(NodeVisitor[Value]):
    """
    Visitor that walks the tree and evaluates it. Implements the NodeVisitor interface

    Member Variables:
        scope (Scope): the current scope
    """
    scope: Scope
    
    def __init__(self, scope: Optional[Scope] = None):
        """
        Constructor

        Args:
            scope (Optional[Scope], optional): the initial scope. Defaults to None.
        """

        if scope is None:
            scope = Scope({})
        self.scope = scope
    
    def increase_scope(self) -> EvalVisitor:
        """
        Create a new EvalVisitor with a child scope of the current scope. Used to create a new scope for a code block (if, while, function body)

        Returns:
            EvalVisitor: the new EvalVisitor
        """
        return EvalVisitor(self.scope.create_child({}))

    def visit_two_side_op(self, node: TwoSideOpNode) -> Value:
        """
        Visit a two-sided operator node
        
        Args:
            node (TwoSideOpNode): the node to visit
            
        Returns:
            Value: the result of the operation

        Raises:
            Exception: if the operation is not defined for the given types or the operator is not known
        """
        left = node.left.accept(self)
        right = node.right.accept(self)
        assert left is not None and right is not None
        #assert not isinstance(left, bool) and not isinstance(right, bool)
        assert not isinstance(left, Function) and not isinstance(right, Function)
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

        elif node.sign == "/":
            return left / right
        elif node.sign == "==":
            return left == right
        elif node.sign == "!=":
            return left != right
        elif node.sign == "<=":
            return left <= right
        elif node.sign == ">=":
            return left >= right
        elif node.sign == "<":
            return left < right
        elif node.sign == ">":
            return left > right
        elif node.sign == "&&":
            return left and right
        elif node.sign == "||":
            return left or right
        raise Exception("unknown operator")
    def visit_unary_op(self, node: UnaryOpNode) -> Value:
        """
        Visit a unary operator node

        Args:
            node (UnaryOpNode): the node to visit

        Returns:
            Value: the result of the operation

        Raises:
            Exception: if the operation is not known
        """
        value = node.node.accept(self)
        assert value is not None
        if node.sign == "-":
            return -value
        elif node.sign == "!":
            return not value
        raise Exception("unknown operator")
    
    def visit_code_block(self, node: CodeBlockNode) -> Value:
        """
        Visit a code block node ({ ... })

        Args:
            node (CodeBlockNode): the node to visit

        Returns:
            Value: None
        """

        inner_scope = self.increase_scope()
        for statement in node.statements:
            statement.accept(inner_scope)
        return None
    
    def visit_if(self, node: IfNode) -> Value:
        """
        Evaluate an if statement

        Args:
            node (IfNode): the node to visit

        Returns:
            Value: None
        """
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
        """
        Visit a word node. These Nodes are only used during parsing and should not be evaluated

        Args:
            node (WordNode): the node to visit

        Raises:
            Exception: always
        """
        raise Exception("cannot evaluate word")
        #if node.word in self.variables:
        #    return self.variables[node.word]
        #raise Exception("unknown variable")
    
    def visit_symbol(self, node: SymbolNode) -> Value:
        """
        Visit a symbol node. These Nodes are only used during parsing and should not be evaluated

        Args:
            node (SymbolNode): the node to visit

        Raises:
            Exception: always
        """
        raise Exception("cannot evaluate symbol")
    
    def visit_number(self, node: NumberNode) -> Value:
        """
        Visit a number node

        Args:
            node (NumberNode): the node to visit

        Returns:
            Value: the value of the number
        """
        return node.value
    
    def visit_var(self, node: VarNode) -> Value:
        """
        Visit a variable node

        Args:
            node (VarNode): the node to visit

        Returns:
            Value: the value of the variable

        Raises:
            Exception: if the variable is not defined
        """
        return self.scope.get(node.name)
    
    def visit_var_def(self, node: VarDefNode) -> Value:
        """
        Define a variable in the current scope

        Args:
            node (VarDefNode): the node to visit

        Returns:
            Value: None
        """
        if node.value is None:
            self.scope.define(node.name, None)
            return None
        self.scope.define(node.name, node.value.accept(self))
        #print(f"defined {node.name}, scope: {self.scope}")
        return None
    
    def visit_assign(self, node: AssignNode) -> Value:
        """
        Assign a value to a variable in the current scope

        Args:
            node (AssignNode): the node to visit

        Returns:
            Value: None
        """
        self.scope.set(node.var.name, node.value.accept(self))
        return None
    
    def visit_func_call(self, node: FuncCallNode) -> Value:
        """
        Call a function

        Args:
            node (FuncCallNode): the node to visit

        Returns:
            Value: the return value of the function
        """
        func = self.scope.get(node.func.name)
        if not isinstance(func, Function):
            raise Exception("not a function")
        # evaluate the arguments
        args = [arg.accept(self) for arg in node.args]
        # call the function with the arguments
        return func.call(args)
    
    def visit_string(self, node: StringNode) -> Value:
        """
        Visit a string node

        Args:
            node (StringNode): the node to visit

        Returns:
            Value: the value of the string
        """
        return node.string
    
    def visit_while(self, node: whileNode) -> Value:
        """
        Evaluate a while loop. Executes the condition and then the body as long as the condition is true

        Args:
            node (whileNode): the node to visit

        Returns:
            Value: None
        """
        while node.condition.accept(self):
            node.then_block.accept(self)
        return None
    
    def visit_func_arg(self, node: FuncArgNode) -> Value:
        return None
    
    def visit_function_def(self, node: FunctionDefNode) -> Value:
        """
        Define a function in the current scope
        
        Args:
            node (FunctionDefNode): the node to visit
            
        Returns:
            Value: None
        """
        self.scope.define(node.name, BallangFunction(node.args, node.body, self.scope))
        return None

    def visit_code_file(self, node: CodeFileNode) -> Value:
        """
        Evaluate a code file node. This is not defined in the grammar and should not be used. Instead look at the functions in __init__.py
        or evaluate.py

        Raises:
            Exception: always
        """
        raise Exception("cannot evaluate code file")
        #for function_def in node.functions.values():
        #    function_def.accept(self)
        #if self.entry_function is None:
        #    return None
        #func = self.scope.get(self.entry_function)
        #if not isinstance(func, Function):
        #    raise Exception("not a function")
        #return func.call([])
    def visit_return(self, node: ReturnNode) -> Value:
        """
        Return a value from a function by throwing a ReturnException

        Args:
            node (ReturnNode): the node to visit

        Raises:
            ReturnException: always, with the value of the return statement
        """
        if node.value is None:
            raise ReturnException(None)
        raise ReturnException(node.value.accept(self))
