from typing import Callable, Dict
from .ballang import parse
from .eval_visitor import EvalVisitor, PythonFunction, Scope, Value
from .node import CodeFileNode

def wrap_function(fn: Callable) -> PythonFunction:
    def wrapped(args: list) -> Value:
        return fn(*args)
    return wrapped

def parse_file(file: str, global_functions: dict) -> Scope:
    fns: Dict[str, Value] = {}
    for name, curr_fn in global_functions.items():
        fns[name] = PythonFunction(wrap_function(curr_fn), name)
    global_scope = Scope(fns)
    parsed = parse(file)
    assert isinstance(parsed, CodeFileNode)
    for function_def in parsed.functions.values():
        function_def.accept(EvalVisitor(global_scope))
    return global_scope
