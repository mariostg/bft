import numpy as np

from bft import exceptions

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
            raise exceptions.ParentDoesNotExistError

        descendants = []
        for d in family:
            if self.is_descendant_of_parent(parent, d):
                descendants.append(d)
        return descendants

    def get_direct_descendants(self, family: list, parent: str) -> list:
        if parent not in family:
            raise exceptions.ParentDoesNotExistError

        descendants = []
        for d in family:
            if self.is_child_of_parent(parent, d):
                descendants.append(d)
        return descendants

    def create_child(self, family: list, parent: str = None, seqno: str = None) -> str:
        from costcenter.models import FundCenterManager

        """Create a new sequence number to be attributed to a cost center or a fund center.
        Either parent or seqno is required, not both or Exception will be raised.

        Args:
            family (list): A list of sequence no representing the members of the family 
            where the child will be added'
            parent (str, optional): A string representing the parent Fund Center. 
            Defaults to None.
            seqno (str, optional): A string representing the sequence number to be givent to the child. 
            Defaults to None.

        Returns:
            str: The sequence number of the child.
        """
        if parent and seqno:
            raise exceptions.IncompatibleArgumentsError(fundcenter=parent, seqno=seqno)
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
