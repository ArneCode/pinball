from abc import ABC, abstractmethod
from objects.material import Material
from math_utils.vec import Vec

#from path import Path
class Collision(ABC):
    @abstractmethod
    def get_result_dir(self) -> Vec:
        pass
    @abstractmethod
    def get_coll_t(self) -> float:
        pass
    @abstractmethod
    def get_obj_form(self) -> "StaticForm":
        pass
class SimpleCollision(Collision):
    time: float
    bahn: Vec
    #obj: Path  # replace with interface

    def __init__(self, time: float, bahn: Vec, obj):
        self.time = time
        self.bahn = bahn
        self.obj = obj
    def get_obj_form(self):
        return self.obj.get_form()

    def get_result_dir(self) -> Vec:
       # print(f"obj: {self.obj}")
        material: Material = self.obj.get_material()
        normal = self.obj.get_normal(self.bahn.apply(self.time))
        #print(f"normal: {normal}")
        vel_before = self.bahn.deriv().apply(self.time)

        vel_ort, vel_par = vel_before.decompose(normal)
        if vel_ort.magnitude() < material.min_ort:
            vel_ort = vel_ort.normalize()*material.min_ort
        if vel_par.magnitude() < material.min_par:
            vel_par = vel_par.normalize()*material.min_par
        #print(f"vel_before: {vel_before}, vel_ort: {vel_ort}, vel_par: {vel_par}")
        #raise ValueError("stop")
        return vel_par*material.factor_par - vel_ort*material.factor_ort#(vel_par*0.95 - vel_ort*0.8)
    def __str__(self):
        return f"Collision(time: {self.time}, bahn: {self.bahn}, obj: {self.obj})"
    def get_coll_t(self) -> float:
        return self.time
class RotatedCollision(Collision):
    angle: float
    static_coll: Collision
    def __init__(self, collision: Collision, angle: float):
        self.static_coll = collision
        self.angle = angle
    def get_result_dir(self) -> Vec:
        return self.static_coll.get_result_dir().rotate(-self.angle, Vec(0,0))
    def get_coll_t(self) -> float:
        return self.static_coll.get_coll_t()
    def get_obj_form(self):
        return self.static_coll.get_obj_form()

class TimedCollision(Collision):
    time: float
    static_coll: Collision
    def __init__(self, collision: Collision, time: float):
        self.static_coll = collision
        self.time = time
    def get_result_dir(self) -> Vec:
        return self.static_coll.get_result_dir()
#        raise NotImplementedError("not implemented yet")
    def get_coll_t(self) -> float:
        return self.time
    def get_obj_form(self):
        return self.static_coll.get_obj_form()