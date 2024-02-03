import json
import math
from typing import List
from form import CircleForm, Form, LineForm, RotateForm, TransformForm
from material import Material
from polynom import Polynom

from vec import Vec


class world:
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

    def get_forms(self):
        """
        returns a list of objects creted from the json file read in __init__
        """
        forms: List[Form] = []
        named_forms: List[Form] = []
        for form in self.data["forms"]:
            
            if form["type"] == "LineForm":
                if "name" in form["params"].keys():
                    name = form["params"]["name"]
                pos_1 = Vec(form["params"]["pos1"]["x"], form["params"]["pos1"]["y"])
                pos_2 = Vec(form["params"]["pos2"]["x"], form["params"]["pos2"]["y"])
                material = Material(form["params"]["material"]["factor_ort"], form["params"]["material"]["factor_par"], form["params"]["material"]["min_ort"], form["params"]["material"]["min_par"])
                color = tuple(int(form["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
                if "name" in form["params"].keys():
                    name = form["params"]["name"]
                    named_forms.append(LineForm(pos_1, pos_2, self.get_global("ball_radius"), material, name))
                else:
                    forms.append(LineForm(pos_1, pos_2, self.get_global("ball_radius"), material))

                
                

            if form["type"] == "CircleForm":
                pos = Vec(form["params"]["pos"]["x"], form["params"]["pos"]["y"])
                radius = form["params"]["radius"]
                min_angle = form["params"]["min_angle"] * ((2*math.pi)/360)
                max_angle = form["params"]["max_angle"] * ((2*math.pi)/360)
                resolution = form["params"]["resolution"]
                material = Material(form["params"]["material"]["factor_ort"], form["params"]["material"]["factor_par"], form["params"]["material"]["min_ort"], form["params"]["material"]["min_par"])
                color = tuple(int(form["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
                if "name" in form["params"].keys():
                    name = form["params"]["name"]
                    named_forms.append(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global("ball_radius"), name))
                else:
                    forms.append(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global("ball_radius")))


            if form["type"] == "RotateForm":
                center = Vec(form["params"]["center"]["x"], form["params"]["center"]["y"])
                start_angle = form["params"]["start_angle"] * ((2*math.pi)/360)
                angle_speed = form["params"]["angle_speed"] * ((2*math.pi)/360)
                start_time = form["params"]["start_time"]

                if form["params"]["form"]["type"] == "LineForm":
                    pos_1 = Vec(form["params"]["form"]["params"]["pos1"]["x"], form["params"]["form"]["params"]["pos1"]["y"])
                    pos_2 = Vec(form["params"]["form"]["params"]["pos2"]["x"], form["params"]["form"]["params"]["pos2"]["y"])
                    material = Material(form["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["material"]["factor_par"], form["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["material"]["min_par"])
                    color = tuple(int(form["params"]["form"]["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
                    if "name" in form["params"].keys():
                        name = form["params"]["name"]
                        named_forms.append(RotateForm(LineForm(pos_1, pos_2, self.get_global("ball_radius"), material), center, start_angle, angle_speed, start_time, name))
                    else:
                        forms.append(RotateForm(LineForm(pos_1, pos_2, self.get_global("ball_radius"), material), center, start_angle, angle_speed, start_time))

                if form["params"]["form"]["type"] == "CircleForm":
                    pos = Vec(form["params"]["form"]["params"]["pos"]["x"], form["params"]["form"]["params"]["pos"]["y"])
                    radius = form["params"]["form"]["params"]["radius"]
                    min_angle = form["params"]["form"]["params"]["min_angle"] * ((2*math.pi)/360)
                    max_angle = form["params"]["form"]["params"]["max_angle"] * ((2*math.pi)/360)
                    reslution = form["params"]["form"]["params"]["resolution"]
                    material = Material(form["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["material"]["factor_par"], form["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["material"]["min_par"])
                    color = tuple(int(form["params"]["form"]["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
                    if "name" in form["params"].keys():
                        name = form["params"]["name"]
                        named_forms.append(RotateForm(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global("ball_radius"), material), center, start_angle, angle_speed, start_time, name))
                    else:
                        forms.append(RotateForm(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global("ball_radius"), material), center, start_angle, angle_speed, start_time))


            if form["type"] == "TransformForm":
                transform = Vec(Polynom(form["params"]["polynome"]["x"]), Polynom(form["params"]["polynome"]["y"]))

                if form["params"]["form"]["type"] == "LineForm":
                    pos_1 = Vec(form["params"]["form"]["params"]["pos1"]["x"], form["params"]["form"]["params"]["pos1"]["y"])
                    pos_2 = Vec(form["params"]["form"]["params"]["pos2"]["x"], form["params"]["form"]["params"]["pos2"]["y"])
                    material = Material(form["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["material"]["factor_par"], form["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["material"]["min_par"])
                    color = tuple(int(form["params"]["form"]["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
                    if "name" in form["params"].keys():
                        name = form["params"]["name"]
                        named_forms.append(TransformForm(LineForm(pos_1, pos_2, self.get_global("ball_radius"), material), transform, name))
                    else:
                        forms.append(TransformForm(LineForm(pos_1, pos_2, self.get_global("ball_radius"), material), transform))
                

                if form["params"]["form"]["type"] == "CircleForm":
                    pos = Vec(form["params"]["form"]["params"]["pos"]["x"], form["params"]["form"]["params"]["pos"]["y"])
                    radius = form["params"]["form"]["params"]["radius"]
                    min_angle = form["params"]["form"]["params"]["min_angle"] * ((2*math.pi)/360)
                    max_angle = form["params"]["form"]["params"]["max_angle"] * ((2*math.pi)/360)
                    reslution = form["params"]["form"]["params"]["resolution"]
                    material = Material(form["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["material"]["factor_par"], form["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["material"]["min_par"])
                    color = tuple(int(form["params"]["form"]["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
                    if "name" in form["params"].keys():
                        name = form["params"]["name"]
                        named_forms.append(TransformForm(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global("ball_radius")), transform, name))
                    else:
                        forms.append(TransformForm(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global("ball_radius")), transform))


                if form["params"]["form"]["type"] == "RotateForm":
                    center = Vec(form["params"]["form"]["params"]["center"]["x"], form["params"]["form"]["params"]["center"]["y"])
                    start_angle = form["params"]["form"]["params"]["start_angle"] * ((2*math.pi)/360)
                    angle_speed = form["params"]["form"]["params"]["angle_speed"] * ((2*math.pi)/360)
                    start_time = form["params"]["form"]["params"]["start_time"]

                    if form["params"]["form"]["params"]["form"]["type"] == "LineForm":
                        pos_1 = Vec(form["params"]["form"]["params"]["form"]["params"]["pos1"]["x"], form["params"]["form"]["params"]["form"]["params"]["pos1"]["y"])
                        pos_2 = Vec(form["params"]["form"]["params"]["form"]["params"]["pos2"]["x"], form["params"]["form"]["params"]["form"]["params"]["pos2"]["y"])
                        material = Material(form["params"]["form"]["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["form"]["params"]["material"]["factor_par"], form["params"]["form"]["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["form"]["params"]["material"]["min_par"])
                        color = tuple(int(form["params"]["form"]["params"]["form"]["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
                        if "name" in form["params"].keys():
                            name = form["params"]["name"]
                            named_forms.append(TransformForm(RotateForm(LineForm(pos_1, pos_2, self.get_global("ball_radius"), material), center, start_angle, angle_speed, start_time), transform, name))
                        else:
                            forms.append(TransformForm(RotateForm(LineForm(pos_1, pos_2, self.get_global("ball_radius"), material), center, start_angle, angle_speed, start_time), transform))

                    if form["params"]["form"]["params"]["form"]["type"] == "CircleForm":
                        pos = Vec(form["params"]["form"]["params"]["form"]["params"]["pos"]["x"], form["params"]["form"]["params"]["form"]["params"]["pos"]["y"])
                        radius = form["params"]["form"]["params"]["form"]["params"]["radius"]
                        min_angle = form["params"]["form"]["params"]["form"]["params"]["min_angle"] * ((2*math.pi)/360)
                        max_angle = form["params"]["form"]["params"]["form"]["params"]["max_angle"] * ((2*math.pi)/360)
                        reslution = form["params"]["form"]["params"]["form"]["params"]["resolution"]
                        material = Material(form["params"]["form"]["params"]["form"]["params"]["material"]["factor_ort"], form["params"]["form"]["params"]["form"]["params"]["material"]["factor_par"], form["params"]["form"]["params"]["form"]["params"]["material"]["min_ort"], form["params"]["form"]["params"]["form"]["params"]["material"]["min_par"])
                        color = tuple(int(form["params"]["form"]["params"]["form"]["params"]["color"][i+1:i+3], 16) for i in (0, 2, 4))
                        if "name" in form["params"].keys():
                            name = form["params"]["name"]
                            named_forms.append(TransformForm(RotateForm(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global("ball_radius")), center, start_angle, angle_speed, start_time), transform, name))
                        else:
                            forms.append(TransformForm(RotateForm(CircleForm(pos, radius, material, color, min_angle, max_angle, resolution, self.get_global("ball_radius")), center, start_angle, angle_speed, start_time), transform))
        

        return forms, named_forms
                
        
        


if __name__ == "__main__":
    world1 = world("pinball.json")
    print(world1)
    print(world1.get_global("ball_radius"))
    #print(world1.get_forms())
    