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
       # print(f"obj: {self.obj}")
        normal = self.obj.get_normal(self.bahn.apply(self.time))
        #print(f"normal: {normal}")
        vel_before = self.bahn.deriv().apply(self.time)

        vel_ort, vel_par = vel_before.decompose(normal)
        min_ort = 20.0
        if vel_ort.magnitude() < min_ort:
            vel_ort = vel_ort.normalize()*min_ort
        #print(f"vel_before: {vel_before}, vel_ort: {vel_ort}, vel_par: {vel_par}")
        #raise ValueError("stop")
        return vel_par - vel_ort*0.9#(vel_par*0.95 - vel_ort*0.8)
class RotatedCollision(Collision):
    angle: float
    def __init__(self, collision: Collision, angle: float):
        super().__init__(collision.time, collision.bahn, collision.obj)
        self.angle = angle
    def get_result_dir(self) -> Vec:
        return super().get_result_dir().rotate(-self.angle, Vec(0,0))