from typing import Dict
from .ballang import parse
from .eval_visitor import EvalVisitor, Function, PythonFunction, Scope, Value
from .node import CodeFileNode


def get_ballang_function(file: str, entry_function: str) -> Function:
    """
    Parse the given file and return the function with the given name
    """
    parsed = parse(file)
    assert isinstance(parsed, CodeFileNode)
    print_fn = PythonFunction(lambda args: print(*args))
    global_scope = Scope({"print": print_fn})
    
    for function_def in parsed.functions.values():
        function_def.accept(EvalVisitor(global_scope))
    
    if entry_function is None:
        return None
    func = global_scope.get(entry_function)
    if func is None:
        raise Exception("entry function not found")
    assert isinstance(func, Function)
    return func
def parse_file(file: str, global_functions: dict) -> Scope:
    """
    Parse the given file and return the global scope (with the global functions added to it)
    """
    fns: Dict[str, Value] = {}
    for name, fn in global_functions.items():
        fns[name] = PythonFunction(fn, name)
    global_scope = Scope(fns)
    parsed = parse(file)
    assert isinstance(parsed, CodeFileNode)
    for function_def in parsed.functions.values():
        function_def.accept(EvalVisitor(global_scope))
    return global_scope

def evaluate(file: str, entry_function: str):
    """
    Evaluate the given file with the given entry function
    """
    func = get_ballang_function(file, entry_function)
    func.call([])

if __name__ == "__main__":
    i = 0
    def fib(n):
        global i
        i += 1
        if n == 0:
            return 0
        if n == 1:
            return 1
        return fib(n-1) + fib(n-2)
    
    # fibonacci
    file = """
    def fib(n)
    {
        if n == 0 {
            return 0;
        }
        if n == 1 {
            return 1;
        }
        return fib(n-1) + fib(n-2);
    }
    """
    ball_fib = get_ballang_function(file, "fib")
    n = 30
    # measure time
    import time
    if True:
        start = time.time()
        result = ball_fib(n)
        print(result)
        end = time.time()
        ball_duration = end - start
        print(f"ballang fib({n}) took {ball_duration} seconds")
    # measure time
    start = time.time()
    result = fib(n)
    print(result)
    end = time.time()
    python_duration = end - start
    print(f"python fib({n}) took {python_duration} seconds")
    print(f"python is {ball_duration / python_duration} times faster")
    print(f"fib({n}) used {i} function calls, that is {i / ball_duration} calls per second")

