from __future__ import annotations
from typing import Dict, List, Optional
import copy
from ball import Ball

from form import Form
from path import Path


class FormHandler:
    forms: List[Form]
    named_forms: Dict[str, Form]

    def __init__(self, forms: Optional[List[Form]] = None, named_forms: Optional[Dict[str, Form]] = None):
        if forms is None:
            forms = []
        if named_forms is None:
            named_forms = {}
        self.forms = forms
        self.named_forms = named_forms
    def clone(self) -> FormHandler:
        return FormHandler(copy.copy(self.forms), copy.copy(self.named_forms))

    def add_form(self, form: Form):
        self.forms.append(form)
    def set_named_form(self, name: str, form: Form):
        self.named_forms[name] = form
    def get_named_form(self, name: str) -> Optional[Form]:
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

    def find_collision(self, ball: Ball, ignore: List[Path] = []):
        first_coll = None
        for form in self.forms + list(self.named_forms.values()):
            coll = form.find_collision(ball, ignore)
            if coll is None:
                continue
            if first_coll is None or coll.time < first_coll.time:
                first_coll = coll
        return first_coll
