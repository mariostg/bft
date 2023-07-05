import numpy as np
from costcenter.models import FundCenterManager

"""
This class serves for the management of organisation breakdown structure.
"""


class Structure:
    def is_descendant_of_parent(self, parent, child) -> bool:
        if len(child) <= len(parent):
            return False
        for k, v in enumerate(parent):
            if child[k] == v:
                continue
            else:
                return False
        return True

    def is_child_of_parent(self, parent, child) -> bool:
        if len(child) - 2 != len(parent):
            return False

        return self.is_descendant_of_parent(parent, child)

    def get_descendants(self, family, parent) -> list:
        if parent not in family:
            raise ParentDoesNotExistError

        descendants = []
        for d in family:
            if self.is_descendant_of_parent(parent, d):
                descendants.append(d)
        return descendants

    def get_direct_descendants(self, family: list, parent: str) -> list:
        if parent not in family:
            raise ParentDoesNotExistError

        descendants = []
        for d in family:
            if self.is_child_of_parent(parent, d):
                descendants.append(d)
        return descendants

    def create_child(self, family: list, parent: str = None, seqno=None) -> str:
        if parent:
            seqno = FundCenterManager().fundcenter(parent).sequence
        children = self.get_direct_descendants(family, seqno)
        if children == []:
            new_born = seqno + ".1"
            family.append(new_born)
            return new_born
        splitted = [i.split(".") for i in children]
        splitted = np.array(splitted).astype(int)
        oldest = list(splitted.max(axis=0))
        new_born = oldest
        new_born[-1] = int(new_born[-1]) + 1
        new_born = [str(i) for i in new_born]
        new_born = ".".join(new_born)
        family.append(new_born)
        return new_born


class ParentDoesNotExistError(Exception):
    def __init__(self, parent=None):
        self.message = f"The parent specified: {parent} does not exist"

    def __str__(self):
        return self.message
