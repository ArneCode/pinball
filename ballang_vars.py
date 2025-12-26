from typing import Any, Dict, Tuple


class VarHandler:
    """
    Handles variables for ballang
    """
    vars: Dict[str, Tuple[Any, float]]

    def __init__(self):
        self.vars = {}
    
    def set_var(self, name: str, value: Any, time: float):
        if name in self.vars:
            prev_time = self.vars[name][1]
            if time < prev_time:
                return
        self.vars[name] = (value, time)
    
    def get_var(self, name: str) -> Any:
        if name in self.vars:
            return self.vars[name][0]
        return None
    def is_defined(self, name: str) -> bool:
        return name in self.vars
    def merge(self, other: "VarHandler"):
        for name, (value, time) in other.vars.items():
            self.set_var(name, value, time)