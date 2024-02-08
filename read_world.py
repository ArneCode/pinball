import json
import math
from typing import Dict, List, Tuple
from ballang_interop import prepare_coll_function, prepare_init_function, prepare_keydown_function, prepare_update_function
from ballang_vars import VarHandler
from collision.coll_direction import CollDirection
from game import GameState, PinballGame, make_rotating
from objects.ball import Ball
from objects.form import Form
from objects.formhandler import FormHandler
from objects.forms.lineform import LineForm
from objects.forms.circleform import CircleForm
from objects.forms.periodicform import PeriodicForm
from objects.forms.polygonform import PolygonForm
from objects.forms.rotateform import RotateForm
from objects.forms.tempform import TempForm
from objects.forms.transformform import TransformForm

from objects.material import Material
from math_utils.polynom import Polynom

from math_utils.vec import Vec


class World:
    '''
    Eine Klasse die die json welt datei einliest und daten daraus zurückgeben kann.
    Erzeugt auch direkt objekte.
    '''

    def __init__(self, file):
        """
        reads a json file on creatig and object and creates a dictionary out of it
        """
        self.file = file

        with open(self.file, 'r') as f:
            data = json.load(f)

        self.data = data
        self.ballang_funcs = {}

    def __str__(self):
        """
        returns the dictionary from the json file by first covertig it to a json string with indentation for better readability for the user (can get quite large)
        """
        return json.dumps(self.data, indent=4)

    def get_global(self, variable):
        """
        returns the value of a variable safed under global in the json file
        """
        return self.data["global"][variable]
    def parse_vec(self, vec_dict):
        x = vec_dict["x"]
        y = vec_dict["y"]

        assert isinstance(x, (int, float))
        assert isinstance(y, (int, float))

        return Vec(x, y)
    def parse_material(self, material_dict):
        factor_ort = material_dict["factor_ort"]
        factor_par = material_dict["factor_par"]
        min_ort = material_dict["min_ort"]
        min_par = material_dict["min_par"]

        assert isinstance(factor_ort, (int, float))
        assert isinstance(factor_par, (int, float))
        assert isinstance(min_ort, (int, float))
        assert isinstance(min_par, (int, float))

        return Material(factor_ort, factor_par, min_ort, min_par)
    def parse_line_form(self, form_dict):
        if "name" in form_dict.keys():
            name = form_dict["name"]
        pos_1 = self.parse_vec(form_dict["pos1"])
        pos_2 = self.parse_vec(form_dict["pos2"])
        material = self.parse_material(form_dict["material"])
        #color = tuple(
        #    int(form_dict["color"][i+1:i+3], 16) for i in (0, 2, 4))
        if "effects" in form_dict.keys():
            effects = form_dict["effects"]
        else:
            effects = []
        on_collision = []
        for effect in effects:
            on_collision.append(self.parse_ballang(effect))
        if "name" in form_dict.keys():
            name = form_dict["name"]
            return LineForm(pos_1, pos_2, self.get_global("ball_radius"), material, name, on_collision=on_collision)
        else:
            return LineForm(pos_1, pos_2, self.get_global("ball_radius"), material, on_collision=on_collision)
    def parse_circle_form(self, form_dict):
        pos = self.parse_vec(form_dict["pos"])
        radius = form_dict["radius"]
        min_angle = form_dict["min_angle"] * ((2*math.pi)/360)
        max_angle = form_dict["max_angle"] * ((2*math.pi)/360)
        resolution = form_dict["resolution"]
        material = self.parse_material(form_dict["material"])
        color = tuple(
            int(form_dict["color"][i+1:i+3], 16) for i in (0, 2, 4))
        if "effects" in form_dict.keys():
            effects = form_dict["effects"]
        else:
            effects = []
        on_collision = []
        for effect in effects:
            on_collision.append(self.parse_ballang(effect))
        if "name" in form_dict.keys():
            name = form_dict["name"]
            return CircleForm(pos, radius, material, color, min_angle,
                               max_angle, resolution, self.get_global("ball_radius"), name, on_collision=on_collision)
        else:
            return CircleForm(pos, radius, material, color, min_angle,
                              max_angle, resolution, self.get_global("ball_radius"), on_collision=on_collision)
    def parse_rotate_form(self, form_dict):
        center = self.parse_vec(form_dict["center"])
        start_angle = form_dict["start_angle"] * ((2*math.pi)/360)
        angle_speed = form_dict["angle_speed"] * ((2*math.pi)/360)
        start_time = form_dict["start_time"]
        form = self.parse_form(form_dict["form"])
        if "name" in form_dict.keys():
            name = form_dict["name"]
            return RotateForm(form, center, start_angle, angle_speed, start_time, name)
        else:
            return RotateForm(form, center, start_angle, angle_speed, start_time)
    def parse_periodic_form(self, form_dict):
        forms = []
        for form_info in form_dict["forms"]:
            form = self.parse_form(form_info["form"])
            duration = form_info["duration"]
            assert isinstance(duration, (int, float))
            forms.append((form, duration))

        return PeriodicForm(forms)
    
    def parse_inf_rotating_form(self, form_dict):
        form = self.parse_form(form_dict["form"])
        rot_point = self.parse_vec(form_dict["rot_point"])
        period = form_dict["period"]
        return make_rotating(form, rot_point, period)

    def parse_transform_form(self, form_dict):
        transform = self.parse_bahnkurve(form_dict["transform"])
        form = self.parse_form(form_dict["form"])
        if "name" in form_dict.keys():
            name = form_dict["name"]
            return TransformForm(form, transform, name)
        else:
            return TransformForm(form, transform)
    def parse_polynom(self, polynom_dict):
        koefs = polynom_dict["koefs"]
        assert isinstance(koefs, list)
        for koef in koefs:
            assert isinstance(koef, (int, float))
        return Polynom(polynom_dict)
    def parse_bahnkurve(self, bahnkurve_dict):
        x = self.parse_polynom(bahnkurve_dict["x"])
        y = self.parse_polynom(bahnkurve_dict["y"])
        return Vec(x, y)
    
    def parse_polygon(self, polygon_dict):
        points = []
        for point in polygon_dict["points"]:
            points.append(self.parse_vec(point))
        
        material = self.parse_material(polygon_dict["material"])

        self_coll_direction_str = polygon_dict["self_coll_direction"]
        if self_coll_direction_str == "ALLOW_ALL":
            self_coll_direction = CollDirection.ALLOW_ALL
        elif self_coll_direction_str == "ALLOW_FROM_INSIDE":
            self_coll_direction = CollDirection.ALLOW_FROM_INSIDE
        elif self_coll_direction_str == "ALLOW_FROM_OUTSIDE":
            self_coll_direction = CollDirection.ALLOW_FROM_OUTSIDE
        else:
            raise ValueError("self_coll_direction_str not known")
        
        line_coll_direction_str = polygon_dict["line_coll_direction"]
        if line_coll_direction_str == "ALLOW_ALL":
            line_coll_direction = CollDirection.ALLOW_ALL
        elif line_coll_direction_str == "ALLOW_FROM_INSIDE":
            line_coll_direction = CollDirection.ALLOW_FROM_INSIDE
        elif line_coll_direction_str == "ALLOW_FROM_OUTSIDE":
            line_coll_direction = CollDirection.ALLOW_FROM_OUTSIDE
        else:
            raise ValueError("line_coll_direction_str not known")
        if "effects" in polygon_dict.keys():
            effects = polygon_dict["effects"]
        else:
            effects = []
        on_collision = []
        for effect in effects:
            on_collision.append(self.parse_ballang(effect))
        if "filled" in polygon_dict.keys():
            filled = polygon_dict["filled"]
        else:
            filled = False
        if "do_reflect" in polygon_dict.keys():
            do_reflect = polygon_dict["do_reflect"]
        else:
            do_reflect = True
        if "overwrite_ball_radius" in polygon_dict.keys():
            ball_radius = polygon_dict["overwrite_ball_radius"]
        else:
            ball_radius = self.get_global("ball_radius")
        return PolygonForm(points, material=material, self_coll_direction=self_coll_direction, line_coll_direction=line_coll_direction, on_collision=on_collision, ball_radius=ball_radius, filled=filled, do_reflect=do_reflect)
    def parse_temp_form(self, temp_form_dict):
        start_form = self.parse_form(temp_form_dict["start_form"])
        form_duration = temp_form_dict["form_duration"]
        end_form = self.parse_form(temp_form_dict["end_form"])
        return TempForm(start_form, form_duration, end_form)
    def parse_ballang_str(self, ballang_str_dict):
        func_name = ballang_str_dict["func_name"]
        code = ballang_str_dict["code"]
        self.ballang_funcs[func_name] = code
        return func_name
    def parse_ballang_inline(self, ballang_inline_dict):
        code = ballang_inline_dict["code"]
        name = f"inline_{len(self.ballang_funcs)}"
        code = f"""
def {name}(t,ball_id){{
{code};
}}
"""
        self.ballang_funcs[name] = code
        return name
    def parse_ballang_file(self, ballang_file_dict):
        path = ballang_file_dict["path"]
        name = ballang_file_dict["name"]
        with open(path, "r") as f:
            code = f.read()
        self.ballang_funcs[name] = code
        return name
    def parse_ballang(self, ballang_dict):
        print(f"ballang_dict: {ballang_dict}")
        if ballang_dict["type"] == "BallangString":
            return self.parse_ballang_str(ballang_dict["params"])
        elif ballang_dict["type"] == "BallangInline":
            return self.parse_ballang_inline(ballang_dict["params"])
        elif ballang_dict["type"] == "BallangFile":
            return self.parse_ballang_file(ballang_dict["params"])
        else:
            raise ValueError(f"ballang_dict['type'] not known, got {ballang_dict['type']}")


    def parse_form(self, form_dict):
        if form_dict["type"] == "LineForm":
            return self.parse_line_form(form_dict["params"])
        elif form_dict["type"] == "CircleForm":
            return self.parse_circle_form(form_dict["params"])
        elif form_dict["type"] == "RotateForm":
            return self.parse_rotate_form(form_dict["params"])
        elif form_dict["type"] == "TransformForm":
            return self.parse_transform_form(form_dict["params"])
        elif form_dict["type"] == "PolygonForm":
            return self.parse_polygon(form_dict["params"])
        elif form_dict["type"] == "TempForm":
            return self.parse_temp_form(form_dict["params"])
        elif form_dict["type"] == "PeriodicForm":
            return self.parse_periodic_form(form_dict["params"])
        elif form_dict["type"] == "InfRotatingForm":
            return self.parse_inf_rotating_form(form_dict["params"])
        else:
            raise ValueError(f"form_dict['type'] not known, got {form_dict['type']}")
    def get_forms(self) -> Tuple[FormHandler, Dict[str, str]]:
        """
        returns a list of objects creted from the json file read in __init__
        """
        forms: List[Form] = []
        named_forms: Dict[str, Form] = {}
        hidden_forms: Dict[str, Form] = {}

        for form in self.data["forms"]:
            forms.append(self.parse_form(form))
        
        for name, form in self.data["namedForms"].items():
            named_forms[name] = self.parse_form(form)
        for name, form in self.data["hiddenForms"].items():
            hidden_forms[name] = self.parse_form(form)
        
        form_handler = FormHandler(forms = forms, named_forms = named_forms, hidden_forms = hidden_forms)
        return form_handler, self.ballang_funcs
    def parse_ball(self, ball_dict):
        pos = self.parse_vec(ball_dict["pos"])
        vel = self.parse_vec(ball_dict["vel"])
        acc = self.parse_vec(ball_dict["acc"])
        color = (255,0,0)
        radius = self.get_global("ball_radius")

        return Ball(pos, radius, color).with_acc(acc).with_vel(vel)
    def get_balls(self):
        balls = []
        for ball in self.data["balls"]:
            balls.append(self.parse_ball(ball))
        return balls
    def parse_game(self):
        game_dict = self.data
        forms, ballang_funcs = self.get_forms()
        balls = self.get_balls()
        coll_fns = {}
        for name, code in ballang_funcs.items():
            coll_fns[name] = prepare_coll_function(code, name)
        globals = VarHandler()
        if "on_update" in game_dict.keys():
            on_update = self.parse_ballang(game_dict["on_update"])
            on_update = prepare_update_function(self.ballang_funcs[on_update], on_update)
        else:
            on_update = None
        if "on_keydown" in game_dict.keys():
            on_keydown = self.parse_ballang(game_dict["on_keydown"])
            on_keydown = prepare_keydown_function(self.ballang_funcs[on_keydown], on_keydown)
        else:
            on_keydown = None
        if "on_init" in game_dict.keys():
            on_init = self.parse_ballang(game_dict["on_init"])
            on_init = prepare_init_function(self.ballang_funcs[on_init], on_init)
        else:
            on_init = None
        #forms.add_form(rotating_polygon)
        state = GameState(forms, balls, globals)
        game = PinballGame(start_state=state,
                            on_keydown=on_keydown, on_update=on_update, on_init = on_init, speed=9.0, coll_fns=coll_fns)
        return game
#         for form in self.data["forms"]:

#             if form["type"] == "LineForm":
#                 if "name" in form["params"].keys():
#                     name = form["params"]["name"]
#                 pos_1 = Vec(form["params"]["pos1"]["x"],
#                             form["params"]["pos1"]["y"])
#                 pos_2 = Vec(form["params"]["pos2"]["x"],
#                             form["params"]["pos2"]["y"])
#                 material = Material(form["params"]["material"]["factor_ort"], form["params"]["material"]
#                                     ["factor_par"], form["params"]["material"]["min_ort"], form["params"]["material"]["min_par"])
#                 color = tuple(
#                     int(form["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
#                 if "name" in form["params"].keys():
#                     name = form["params"]["name"]
#                     named_forms.append(
#                         LineForm(pos_1, pos_2, self.get_global("ball_radius"), material, name))
#                 else:
#                     forms.append(
#                         LineForm(pos_1, pos_2, self.get_global("ball_radius"), material))

#             if form["type"] == "CircleForm":
#                 pos = Vec(form["params"]["pos"]["x"],
#                           form["params"]["pos"]["y"])
#                 radius = form["params"]["radius"]
#                 min_angle = form["params"]["min_angle"] * ((2*math.pi)/360)
#                 max_angle = form["params"]["max_angle"] * ((2*math.pi)/360)
#                 resolution = form["params"]["resolution"]
#                 material = Material(form["params"]["material"]["factor_ort"], form["params"]["material"]
#                                     ["factor_par"], form["params"]["material"]["min_ort"], form["params"]["material"]["min_par"])
#                 color = tuple(
#                     int(form["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
#                 if "name" in form["params"].keys():
#                     name = form["params"]["name"]
#                     named_forms.append(CircleForm(pos, radius, material, color, min_angle,
#                                        max_angle, resolution, self.get_global("ball_radius"), name))
#                 else:
#                     forms.append(CircleForm(pos, radius, material, color, min_angle,
#                                  max_angle, resolution, self.get_global("ball_radius")))

#             if form["type"] == "RotateForm":
#                 center = Vec(form["params"]["center"]["x"],
#                              form["params"]["center"]["y"])
#                 start_angle = form["params"]["start_angle"] * ((2*math.pi)/360)
#                 angle_speed = form["params"]["angle_speed"] * ((2*math.pi)/360)
#                 start_time = form["params"]["start_time"]

#                 if form["params"]["form"]["type"] == "LineForm":
#                     pos_1 = Vec(form["params"]["form"]["params"]["pos1"]
#                                 ["x"], form["params"]["form"]["params"]["pos1"]["y"])
#                     pos_2 = Vec(form["params"]["form"]["params"]["pos2"]
#                                 ["x"], form["params"]["form"]["params"]["pos2"]["y"])
#                     material = Material(form["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["material"]
#                                         ["factor_par"], form["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["material"]["min_par"])
#                     color = tuple(
#                         int(form["params"]["form"]["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
#                     if "name" in form["params"].keys():
#                         name = form["params"]["name"]
#                         named_forms.append(RotateForm(LineForm(pos_1, pos_2, self.get_global(
#                             "ball_radius"), material), center, start_angle, angle_speed, start_time, name))
#                     else:
#                         forms.append(RotateForm(LineForm(pos_1, pos_2, self.get_global(
#                             "ball_radius"), material), center, start_angle, angle_speed, start_time))

#                 if form["params"]["form"]["type"] == "CircleForm":
#                     pos = Vec(form["params"]["form"]["params"]["pos"]["x"],
#                               form["params"]["form"]["params"]["pos"]["y"])
#                     radius = form["params"]["form"]["params"]["radius"]
#                     min_angle = form["params"]["form"]["params"]["min_angle"] * \
#                         ((2*math.pi)/360)
#                     max_angle = form["params"]["form"]["params"]["max_angle"] * \
#                         ((2*math.pi)/360)
#                     reslution = form["params"]["form"]["params"]["resolution"]
#                     material = Material(form["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["material"]
#                                         ["factor_par"], form["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["material"]["min_par"])
#                     color = tuple(
#                         int(form["params"]["form"]["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
#                     if "name" in form["params"].keys():
#                         name = form["params"]["name"]
#                         named_forms.append(RotateForm(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global(
#                             "ball_radius"), material), center, start_angle, angle_speed, start_time, name))
#                     else:
#                         forms.append(RotateForm(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global(
#                             "ball_radius"), material), center, start_angle, angle_speed, start_time))

#             if form["type"] == "TransformForm":
#                 transform = Vec(Polynom(form["params"]["polynome"]["x"]), Polynom(
#                     form["params"]["polynome"]["y"]))

#                 if form["params"]["form"]["type"] == "LineForm":
#                     pos_1 = Vec(form["params"]["form"]["params"]["pos1"]
#                                 ["x"], form["params"]["form"]["params"]["pos1"]["y"])
#                     pos_2 = Vec(form["params"]["form"]["params"]["pos2"]
#                                 ["x"], form["params"]["form"]["params"]["pos2"]["y"])
#                     material = Material(form["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["material"]
#                                         ["factor_par"], form["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["material"]["min_par"])
#                     color = tuple(
#                         int(form["params"]["form"]["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
#                     if "name" in form["params"].keys():
#                         name = form["params"]["name"]
#                         named_forms.append(TransformForm(LineForm(
#                             pos_1, pos_2, self.get_global("ball_radius"), material), transform, name))
#                     else:
#                         forms.append(TransformForm(
#                             LineForm(pos_1, pos_2, self.get_global("ball_radius"), material), transform))

#                 if form["params"]["form"]["type"] == "CircleForm":
#                     pos = Vec(form["params"]["form"]["params"]["pos"]["x"],
#                               form["params"]["form"]["params"]["pos"]["y"])
#                     radius = form["params"]["form"]["params"]["radius"]
#                     min_angle = form["params"]["form"]["params"]["min_angle"] * \
#                         ((2*math.pi)/360)
#                     max_angle = form["params"]["form"]["params"]["max_angle"] * \
#                         ((2*math.pi)/360)
#                     reslution = form["params"]["form"]["params"]["resolution"]
#                     material = Material(form["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["material"]
#                                         ["factor_par"], form["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["material"]["min_par"])
#                     color = tuple(
#                         int(form["params"]["form"]["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
#                     if "name" in form["params"].keys():
#                         name = form["params"]["name"]
#                         named_forms.append(TransformForm(CircleForm(
#                             pos, radius, material, color, min_angle, max_angle, resolution, self.get_global("ball_radius")), transform, name))
#                     else:
#                         forms.append(TransformForm(CircleForm(pos, radius, material, color, min_angle,
#                                      max_angle, resolution, self.get_global("ball_radius")), transform))

#                 if form["params"]["form"]["type"] == "RotateForm":
#                     center = Vec(form["params"]["form"]["params"]["center"]
#                                  ["x"], form["params"]["form"]["params"]["center"]["y"])
#                     start_angle = form["params"]["form"]["params"]["start_angle"] * (
#                         (2*math.pi)/360)
#                     angle_speed = form["params"]["form"]["params"]["angle_speed"] * (
#                         (2*math.pi)/360)
#                     start_time = form["params"]["form"]["params"]["start_time"]

#                     if form["params"]["form"]["params"]["form"]["type"] == "LineForm":
#                         pos_1 = Vec(form["params"]["form"]["params"]["form"]["params"]["pos1"]
#                                     ["x"], form["params"]["form"]["params"]["form"]["params"]["pos1"]["y"])
#                         pos_2 = Vec(form["params"]["form"]["params"]["form"]["params"]["pos2"]
#                                     ["x"], form["params"]["form"]["params"]["form"]["params"]["pos2"]["y"])
#                         material = Material(form["params"]["form"]["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["form"]["params"]["material"]
#                                             ["factor_par"], form["params"]["form"]["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["form"]["params"]["material"]["min_par"])
#                         color = tuple(int(form["params"]["form"]["params"]["form"]
#                                       ["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
#                         if "name" in form["params"].keys():
#                             name = form["params"]["name"]
#                             named_forms.append(TransformForm(RotateForm(LineForm(pos_1, pos_2, self.get_global(
#                                 "ball_radius"), material), center, start_angle, angle_speed, start_time), transform, name))
#                         else:
#                             forms.append(TransformForm(RotateForm(LineForm(pos_1, pos_2, self.get_global(
#                                 "ball_radius"), material), center, start_angle, angle_speed, start_time), transform))

#                     if form["params"]["form"]["params"]["form"]["type"] == "CircleForm":
#                         pos = Vec(form["params"]["form"]["params"]["form"]["params"]["pos"]["x"],
#                                   form["params"]["form"]["params"]["form"]["params"]["pos"]["y"])
#                         radius = form["params"]["form"]["params"]["form"]["params"]["radius"]
#                         min_angle = form["params"]["form"]["params"]["form"]["params"]["min_angle"] * (
#                             (2*math.pi)/360)
#                         max_angle = form["params"]["form"]["params"]["form"]["params"]["max_angle"] * (
#                             (2*math.pi)/360)
#                         reslution = form["params"]["form"]["params"]["form"]["params"]["resolution"]
#                         material = Material(form["params"]["form"]["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["form"]["params"]["material"]
#                                             ["factor_par"], form["params"]["form"]["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["form"]["params"]["material"]["min_par"])
#                         color = tuple(int(form["params"]["form"]["params"]["form"]
#                                       ["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
#                         if "name" in form["params"].keys():
#                             name = form["params"]["name"]
#                             named_forms.append(TransformForm(RotateForm(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global(
#                                 "ball_radius")), center, start_angle, angle_speed, start_time), transform, name))
#                         else:
#                             forms.append(TransformForm(RotateForm(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global(
#                                 "ball_radius")), center, start_angle, angle_speed, start_time), transform))

#         return forms, named_forms


# if __name__ == "__main__":
#     world1 = world("pinball.json")
#     print(world1)
#     print(world1.get_global("ball_radius"))
#     # print(world1.get_forms())
