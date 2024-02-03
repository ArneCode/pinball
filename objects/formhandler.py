from __future__ import annotations
from typing import Dict, List, Optional
import copy
from objects.ball import Ball

from objects.form import Form
from objects.path import Path


class FormHandler:
    """
    Handels all forms in the game
    """
    forms: List[Form]
    named_forms: Dict[str, Form]

    def __init__(self, forms: Optional[List[Form]] = None, named_forms: Optional[Dict[str, Form]] = None):
        """
        initializes the formhandler

        Args:
            forms (List[Form], optional): list of forms. Defaults to None.
            named_forms (Dict[str, Form], optional): dict of named forms. Defaults to None.
        """
        if forms is None:
            forms = []
        if named_forms is None:
            named_forms = {}
        self.forms = forms
        self.named_forms = named_forms

    def clone(self) -> FormHandler:
        """
        clones the formhandler

        Returns:
            FormHandler: the cloned formhandler
        """
        return FormHandler(copy.copy(self.forms), copy.copy(self.named_forms))

    def add_form(self, form: Form):
        """Adds a form to the formhandler

        Args:
            form (Form): the form to add
        """
        self.forms.append(form)

    def set_named_form(self, name: str, form: Form):
        """Sets a named form

        Args:
            name (str): the name of the form
            form (Form): the form to set
        """
        self.named_forms[name] = form

    def get_named_form(self, name: str) -> Optional[Form]:
        """Returns a named form

        Args:
            name (str): the name of the form

        Returns:
            Optional[Form]: the form or None if not found
        """
        if name not in self.named_forms:
            return None
        return self.named_forms[name]

    def remove_named_form(self, name: str):
        print(f"removing named form {name}, forms: {self.named_forms}")
        del self.named_forms[name]

    def draw(self, screen, color, time: float):
        """Draws all forms in this formhandler"""
        for form in self.forms:
            form.draw(screen, color, time)
        for name, form in self.named_forms.items():
            form.draw(screen, color, time)

    def find_collision(self, ball: Ball, ignore: List[Form] = []):
        first_coll = None
        for form in self.forms + list(self.named_forms.values()):
            if form in ignore:
                continue
            coll = form.find_collision(ball)
            if coll is None:
                continue
            if first_coll is None or coll.get_coll_t() < first_coll.get_coll_t():
                # print(f"resetting first_coll: to {coll.get_coll_t()}")
                first_coll = coll
            else:
                pass
                # print(f"no reset, coll_t: {coll.get_coll_t()}, first_coll_t: {first_coll.get_coll_t()}")
        if first_coll is not None and False:
            print(f"first_coll: {first_coll.get_coll_t()}")
        return first_coll
