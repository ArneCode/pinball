# visitor that walks the tree and evaluates it
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Union
from node import CodeBlockNode, CodeFileNode, FuncArgNode, FuncCallNode, FunctionDefNode, IfNode, NodeVisitor, ReturnNode, SymbolNode, TwoSideOpNode, WordNode, NumberNode, VarNode, VarDefNode, AssignNode, StringNode, whileNode


class Function(ABC):
    @abstractmethod
    def call(self, args: List[Value]) -> Value:
        pass
    def __call__(self, *args: Value) -> Value:
        return self.call(list(args))

class PythonFunction(Function):
    func: Callable[[List[Value]], Value]
    def __init__(self, func: Callable[[List[Value]], Value]):
        self.func = func
    
    def call(self, args: List[Value]) -> Value:
        return self.func(args)

class BallangFunction(Function):
    args: List[FuncArgNode]
    body: CodeBlockNode
    global_scope: Scope
    def __init__(self, args: List[FuncArgNode], body: CodeBlockNode, global_scope: Scope):
        self.args = args
        self.body = body
        self.global_scope = global_scope
    
    def call(self, args: List[Value]) -> Value:
        if len(args) != len(self.args):
            raise Exception("wrong number of arguments")
        local_scope = self.global_scope.create_child({})
        for (i, arg) in enumerate(self.args):
            if args[i] is None:
                raise Exception("cannot pass None as argument")
            local_scope.define(arg.name, args[i])
        #for arg, value in zip(self.args, args):
        #    local_scope.set(arg.name, value)
        try:
            self.body.accept(EvalVisitor(local_scope))
        except ReturnException as e:
            return e.value
        return None


class Scope:
    variables: Dict[str, Value]
    parent: Optional[Scope]
    def __init__(self, variables: Dict[str, Value], parent: Optional[Scope] = None):
        self.variables = variables
        self.parent = parent
    
    def contains(self, name: str) -> bool:
        if name in self.variables:
            return True
        if self.parent is not None:
            return self.parent.contains(name)
        return False
    
    def get(self, name: str) -> Value:
        if name in self.variables:
            return self.variables[name]
        if self.parent is not None:
            return self.parent.get(name)
        raise Exception(f"unknown variable {name}, {self.variables}")
    
    def set(self, name: str, value: Value) -> None:
        if name in self.variables:
            self.variables[name] = value
            return
        if self.parent is not None:
            self.parent.set(name, value)
            return
        raise Exception(f"unknown variable {name}, variables: {self.variables}, value: {value}")
    def define(self, name: str, value: Value) -> None:
        if name in self.variables:
            raise Exception(f"variable {name} already defined")
        self.variables[name] = value
    
    def create_child(self, vars: Dict[str, Value]) -> Scope:
        return Scope(vars, self)
    
    def __str__(self) -> str:
        return f"Scope({self.variables}, parent={self.parent})"
class ReturnException(Exception):
    value: Value
    def __init__(self, value: Value):
        self.value = value
Value = Union[int, float, str, bool, Function, None]
class EvalVisitor(NodeVisitor[Value]):
    # variables
    scope: Scope
    
    def __init__(self, scope: Optional[Scope] = None):
        if scope is None:
            scope = Scope({})
        self.scope = scope
    
    def increase_scope(self) -> EvalVisitor:
        return EvalVisitor(self.scope.create_child({}))

    def visit_two_side_op(self, node: TwoSideOpNode) -> Value:
        left = node.left.accept(self)
        right = node.right.accept(self)
        assert left is not None and right is not None
        assert not isinstance(left, bool) and not isinstance(right, bool)
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
        inner_scope = self.increase_scope()
        for statement in node.statements:
            statement.accept(inner_scope)
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
        raise Exception("cannot evaluate word")
        #if node.word in self.variables:
        #    return self.variables[node.word]
        #raise Exception("unknown variable")
    
    def visit_symbol(self, node: SymbolNode) -> Value:
        raise Exception("cannot evaluate symbol")
    
    def visit_number(self, node: NumberNode) -> Value:
        return node.value
    
    def visit_var(self, node: VarNode) -> Value:
        return self.scope.get(node.name)
    
    def visit_var_def(self, node: VarDefNode) -> Value:
        if node.value is None:
            self.scope.define(node.name, None)
            return None
        self.scope.define(node.name, node.value.accept(self))
        print(f"defined {node.name}, scope: {self.scope}")
        return None
    
    def visit_assign(self, node: AssignNode) -> Value:
        self.scope.set(node.var.name, node.value.accept(self))
        return None
    
    def visit_func_call(self, node: FuncCallNode) -> Value:
        func = self.scope.get(node.func.name)
        if not isinstance(func, Function):
            raise Exception("not a function")
        args = [arg.accept(self) for arg in node.args]
        return func.call(args)
    
    def visit_string(self, node: StringNode) -> Value:
        return node.string
    
    def visit_while(self, node: whileNode) -> Value:
        while node.condition.accept(self):
            node.then_block.accept(self)
        return None
    
    def visit_func_arg(self, node: FuncArgNode) -> Value:
        return None
    
    def visit_function_def(self, node: FunctionDefNode) -> Value:
        self.scope.define(node.name, BallangFunction(node.args, node.body, self.scope))
        return None

    def visit_code_file(self, node: CodeFileNode) -> Value:
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
        if node.value is None:
            raise ReturnException(None)
        raise ReturnException(node.value.accept(self))
