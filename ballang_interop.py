import time
from typing import Dict, List
from objects.ball import Ball
from ballang import parse_file
from ballang.eval_visitor import Function, Value
from objects.formhandler import FormHandler

def prepare_functions(form_handler: FormHandler, balls: List[Ball], global_vars: Dict[str, Value]) -> Dict:
    def read_global(name: str) -> Value:
        assert name in global_vars, f"global variable {name} not found"
        return global_vars[name]
    def write_global(name: str, value: Value) -> None:
        global_vars[name] = value
    def remove_ball(ball_id: int) -> None:
        for i, ball in enumerate(balls):
            if i == ball_id:
                del balls[i]
                return
        raise Exception(f"ball with id {ball_id} not found")
    
    funcs = {
        "read_global": read_global,
        "write_global": write_global,
        "remove_ball": remove_ball,
        "print": print,
    }
    return funcs

if __name__ == "__main__":
    global_vars: Dict[str, Value] = {}
    file = """
    def main() {
        print("Hello, world!");
    }
    """
    start_time = time.time()
    funcs = prepare_functions(FormHandler(), [], global_vars)
    global_scope = parse_file(file, funcs)
    main = global_scope.get("main")
    assert isinstance(main, Function)
    main.call([])
    print("elapsed time:", time.time() - start_time)