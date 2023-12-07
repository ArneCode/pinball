from vec import Vec
from importlib import import_module

#from path import Path

class Collision:
    time: float
    bahn: Vec
    #obj#: Path  # replace with interface

    def __init__(self, time: float, bahn: Vec, obj):
        self.time = time
        self.bahn = bahn
        self.obj = obj

    def get_result_dir(self) -> Vec:
        
        normal = self.obj.get_normal(self.bahn.apply(self.time))
        print(f"normal: {normal}")
        vel_before = self.bahn.deriv().apply(self.time)

        vel_ort, vel_par = vel_before.decompose(normal)
        print(f"vel_before: {vel_before}, vel_ort: {vel_ort}, vel_par: {vel_par}")
        #raise ValueError("stop")
        return vel_par*0.99 - vel_ort*0.8