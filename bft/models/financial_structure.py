
import numpy as np
import pandas as pd
from django.db import models
from django.db.models import QuerySet
from pandas.io.formats.style import Styler

from bft import exceptions

class FinancialStructureManager(models.Manager):
    """A Django model manager class for handling financial structure operations.

    This manager class provides methods for managing and querying the hierarchical
    financial structure consisting of Fund Centers and Cost Centers. It handles
    operations such as creating sequence numbers, checking parent-child relationships,
    and managing the financial structure hierarchy.

    Methods:
        FundCenters(fundcenter: str = None, seqno: str = None, fcid: int = None):
            Retrieves Fund Center objects based on various search criteria.

        has_children(fundcenter: "FundCenter|str") -> int:
            Returns the total number of direct children (both Fund Centers and Cost Centers).

        has_fund_centers(fundcenter: "FundCenter|str") -> int:
            Returns the number of Fund Center children.

        has_cost_centers(fundcenter: "FundCenter|str") -> int:
            Returns the number of Cost Center children.

        is_child_of(parent: "FundCenter", child: "FundCenter | CostCenter") -> bool:
            Checks if a given entity is a direct child of a parent Fund Center.

        is_descendant_of(parent: "FundCenter", child: "FundCenter | CostCenter") -> bool:
            Checks if a given entity is a descendant of a parent Fund Center.

        sequence_exists(seqno: str = None) -> bool:
            Checks if a given sequence number exists in the system.

        set_parent(fundcenter_parent: "FundCenter" = None, costcenter_child: bool = False) -> str:
            Creates a new sequence number for a child entity.

        is_sequence_descendant_of(seq_parent: str, seq_child: str) -> bool:
            Checks if one sequence number is a descendant of another.

        is_sequence_child_of(seq_parent: str, seq_child: str) -> bool:
            Checks if one sequence number is a direct child of another.

        get_fundcenter_descendants(fundcenter: "FundCenter") -> QuerySet | None:
            Retrieves all Fund Center descendants of a given Fund Center.

        get_fund_center_cost_centers(fundcenter: "FundCenter") -> QuerySet | None:
            Retrieves all Cost Centers that are direct children of a Fund Center.

        get_sequence_direct_descendants(seq_parent: str) -> list:
            Returns a list of direct descendant sequence numbers.

        create_child(parent: str = None, costcenter_child: bool = False) -> str:
            Generates a new sequence number for a child entity.

        last_root() -> str | None:
            Finds the highest sequence number among root elements.

        new_root() -> str:
            Creates a new root sequence number.

        financial_structure_dataframe() -> pd.DataFrame:
            Creates a pandas DataFrame representing the entire financial structure.

        financial_structure_styler(data: pd.DataFrame):
            Applies styling to the financial structure DataFrame.

        CostCenters(fundcenter: "str|FundCenter"):
            Retrieves Cost Centers associated with a Fund Center.

        all():
            Placeholder for retrieving all financial structure records.
    """

    def FundCenters(self, fundcenter: str = None, seqno: str = None, fcid: int = None):
        """
        Retrieve Fund Center objects based on provided search criteria.

        This method queries the FundCenter model to find matching records based on the
        provided parameters. Only one parameter should be provided at a time.

        Args:
            fundcenter (str, optional): Fund center code to search for (case-insensitive).
            seqno (str, optional): Sequence number prefix to search for.
            fcid (int, optional): Specific fund center ID to retrieve.

        Returns:
            QuerySet: A QuerySet containing matching FundCenter objects.
                     Returns all FundCenter objects if no parameters are provided.
                     Returns None if an exception occurs.

        Raises:
            FundCenterExceptionError: If there is an error processing the fund center query.
        """
        try:
            if fundcenter:
                obj = FundCenter.objects.filter(fundcenter=fundcenter.upper())
            elif seqno:
                obj = FundCenter.objects.filter(sequence__startswith=seqno)
            elif fcid:
                obj = FundCenter.objects.filter(id=fcid)
            else:
                obj = FundCenter.objects.all()
        except exceptions.FundCenterExceptionError(fundcenter=fundcenter, seqno=seqno):
            return None
        return obj

    def has_children(self, fundcenter: "FundCenter|str") -> int:

        """
        Checks if a fund center has any child elements (cost centers or fund centers).

        Args:
            fundcenter (Union[FundCenter, str]): The fund center to check. Can be either a FundCenter
                object or a fund center code string.

        Returns:
            int: The total number of child elements (sum of cost centers and fund centers).
                Returns 0 if the fund center does not exist.
        """

        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter)
            except FundCenter.DoesNotExist:
                return 0
        return self.has_cost_centers(fundcenter) + self.has_fund_centers(fundcenter)

    def has_fund_centers(self, fundcenter: "FundCenter|str") -> int:
        """
        Check if the given fund center has associated child fund centers.

        Args:
            fundcenter (Union[FundCenter, str]): A FundCenter instance or fund center code string to check

        Returns:
            int: Number of child fund centers associated with the given fund center.
                 Returns 0 if fund center doesn't exist.
        """
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter)
            except FundCenter.DoesNotExist:
                return 0
        return FundCenter.objects.filter(fundcenter_parent=fundcenter).count()

    def has_cost_centers(self, fundcenter: "FundCenter|str") -> int:
        """
        Check if a Fund Center has associated Cost Centers.

        Args:
            fundcenter (Union[FundCenter, str]): The Fund Center to check. Can be either a
                FundCenter object or a string representing the Fund Center code.

        Returns:
            int: The number of Cost Centers associated with the Fund Center.
                Returns 0 if the Fund Center does not exist.

        Example:
            >>> fc = FundCenter.objects.get(fundcenter='FC001')
            >>> fc.has_cost_centers()
            2  # Returns number of associated cost centers
        """
        if isinstance(fundcenter, str):
            try:
                fundcenter = FundCenter.objects.get(fundcenter=fundcenter)
            except FundCenter.DoesNotExist:
                return 0
        return CostCenter.objects.filter(costcenter_parent=fundcenter).count()

    def is_child_of(
        self, parent: "FundCenter", child: "FundCenter | CostCenter"
    ) -> bool:
        """Check if child object is a direct descendant of parent

        Args:
            parent (FundCenter): A fund center object.
            child (FundCenter | CostCenter): A fund center or cost center object

        Returns:
            bool: True is child is direct descendant of parent.
        """
        if isinstance(child, FundCenter):
            try:
                _parent = FundCenter.objects.get(fundcenter=parent.fundcenter)
            except FundCenter.DoesNotExist:
                return False
            except ValueError:
                return False
            try:
                _child = FundCenter.objects.get(fundcenter=child.fundcenter)
            except FundCenter.DoesNotExist:
                return False
            return self.is_sequence_child_of(_parent.sequence, _child.sequence)
        elif isinstance(child, CostCenter):
            try:
                _parent = FundCenter.objects.get(fundcenter=parent.fundcenter)
            except FundCenter.DoesNotExist:
                return False
            try:
                _child = CostCenter.objects.get(costcenter=child.costcenter)
            except CostCenter.DoesNotExist:
                return False
            return _parent.fundcenter == _child.costcenter_parent.fundcenter
        else:
            return False

    def is_descendant_of(
        self, parent: "FundCenter", child: "FundCenter | CostCenter"
    ) -> bool:
        """Check if child is a direct descendant of parent.

        Args:
            parent (FundCenter): A Fund Center object which is potential parent.
            child (FundCenter | CostCenter): A Fund Center or Cost Center object that could be a descendant.

        Returns:
            bool: Returns True if the child argument is a descendant of parent argument.
        """
        return self.is_sequence_descendant_of(parent.sequence, child.sequence)

    def sequence_exists(self, seqno: str = None) -> bool:
        """Determine if the given sequence number exists in the system.

        Args:
            seqno (str, optional): A string representing a valid sequence number. Defaults to None.

        Returns:
            bool: Returns True if the sequence number exists in the system.
        """
        if seqno:
            return seqno in [x.sequence for x in self.FundCenters(seqno=seqno)]

    def set_parent(
        self, fundcenter_parent: "FundCenter" = None, costcenter_child: bool = False
    ) -> str:
        """
        Create a sequence number by refering to the sequence numbers of the family of fundcenter_parent.
        The sequence number created contains the parent sequence plus the portion of the child.

        Args:
            fundcenter_parent (FundCenter, optional): The fund center that is the parent of the sub center that need a sequence number. Defaults to None.
            costcenter_child (bool, optional): If parent is for cost center, costcenter_child must be True. This will affect the way the sequence number is created. Defaults to False.

        Returns:
            str: A string the represents the child sequence number.
        """
        if fundcenter_parent is None:
            last_root = FinancialStructureManager().last_root()
            if not last_root:
                parent = "1"
            else:
                parent = str(int(last_root) + 1)
            return parent
        new_seq = self.create_child(fundcenter_parent.fundcenter, costcenter_child)
        return new_seq

    def is_sequence_descendant_of(self, seq_parent: str, seq_child: str) -> bool:
        """Compare two sequence numbers to determine if one is a descendant of the other.

        Args:
            seq_parent (str): The sequence number of the parent.
            seq_child (str): The sequence number of the descendant.

        Returns:
            bool: Returns True if the child sequence number is contained in the parent sequence number.
        """
        if ".0." in seq_parent or seq_parent.endswith(".0"):
            raise AttributeError("Parent connot contains .0. in sequence number")
        if len(seq_child) == len(seq_parent):
            return False
        if seq_child.startswith(seq_parent):
            return True
        return False

    def is_sequence_child_of(self, seq_parent: str, seq_child: str) -> bool:
        """Compare two sequence numbers to determine if one is a direct descendant of the other.

        Args:
            seq_parent (str): The sequence number of the parent.
            seq_child (str): Teh sequence number of the child.

        Returns:
            bool: Returns True if the child sequence number is contained in the parent sequence number.
        """

        if not self.is_sequence_descendant_of(seq_parent, seq_child):
            return False
        if ".0." not in seq_child and len(seq_child) - 2 == len(seq_parent):
            return True
        if ".0." in seq_child:
            seq_child = seq_child.replace(".0.", ".")
            return self.is_sequence_child_of(seq_parent, seq_child)
        return False

    def get_fundcenter_descendants(self, fundcenter: "FundCenter") -> QuerySet | None:
        """Create a QuerySet of fundcenters that are descendants of the fund center passed as argument.

        Args:
            fundcenter (FundCenter): A fund center object which the descendants are desired.

        Returns:
            QuerySet: Returns a QuerySet of FundCenter objects that are descendants.  Returns None if no descendants exists.
        """
        try:
            return FundCenter.objects.filter(sequence__startswith=fundcenter.sequence)
        except AttributeError:
            return None

    def get_fund_center_cost_centers(self, fundcenter: "FundCenter") -> QuerySet | None:
        """Create a QuerySet of Cost Centers that are direct children of the given Fund Center.

        Args:
            fundcenter (FundCenter): A Fund Center object

        Returns:
            QuerySet | None: Returns a QuerySet of Cost Centers that are children.  Return None if there are no children.
        """
        cc = CostCenter.objects.filter(costcenter_parent=fundcenter)
        return cc

    def get_sequence_direct_descendants(self, seq_parent: str) -> list:
        """Provide a list of sequence numbers representing the direct descendants of
        the given parent sequence number.

        Args:
            seq_parent (str): the sequence number of the parent.

        Raises:
            exceptions.ParentDoesNotExistError: Will be raised if the parent is not found in the list.

        Returns:
            list: A list of sequence numbers that are direct descendants of the parent.  The parent is not included in the returned list.
        """
        family = list(self.FundCenters().values_list("sequence", flat=True))
        if CostCenter.objects.all().count():
            cc_seq = list(CostCenter.objects.values_list("sequence", flat=True))
            family = family + cc_seq
        if seq_parent not in family:
            raise exceptions.ParentDoesNotExistError

        descendants = []
        for d in family:
            if self.is_sequence_child_of(seq_parent, d):
                descendants.append(d)
        return descendants

    def create_child(self, parent: str = None, costcenter_child: bool = False) -> str:
        """Create a new sequence number to be attributed to a cost center or a fund center.

        Args:
            parent (str, optional): A string representing the parent Fund Center.
            Defaults to None.
            costcenter_child (bool, optional): If parent is for cost center, costcenter_child must be True. This will affect the way the sequence number is created. Defaults to False.

        Returns:
            str: The sequence number of the child.
        """
        FCM = FundCenterManager()
        parent = FCM.fundcenter(parent)
        if costcenter_child:
            children = FCM.get_cost_centers(parent)
        else:
            children = FCM.get_fund_centers(parent)
        if children == []:
            suffix = ".0.1" if costcenter_child else ".1"
            new_born = parent.sequence + suffix
            return new_born
        else:
            pass
        splitted = [i["sequence"].split(".") for i in children]
        splitted = np.array(splitted).astype(int)
        oldest = list(splitted.max(axis=0))
        new_born = oldest
        new_born[-1] = int(new_born[-1]) + 1
        new_born = [str(i) for i in new_born]
        new_born = ".".join(new_born)
        return new_born

    def last_root(self) -> str | None:
        """A root element is one where the sequence number does not contain a dot ('.').
        last_root function finds the highest sequence number amongst the root elements.

        Returns:
            str | None: The last sequence number assigned as a root element or None if there is no root element.
        """
        seq = list(FundCenter.objects.all().values_list("sequence", flat=True))
        if not seq:
            return None

        return str(max([int(s) for s in seq if "." not in s]))

    def new_root(self) -> str:
        lr = self.last_root()
        if not lr:
            return "1"
        return str(int(lr) + 1)

    def financial_structure_dataframe(self) -> pd.DataFrame:
        """
        Creates a DataFrame representing the financial structure by merging fund centers and cost centers data.

        Returns:
            pd.DataFrame: A DataFrame containing the merged financial structure with the following columns:
                - FC Path: Fund center hierarchical path
                - Fund Center: Fund center identifier
                - Fund Center Name: Name of the fund center
                - Cost Center: Cost center identifier
                - Cost Center Name: Name of the cost center
                - Level: Hierarchical level
                - Procurement Officer: Name of the procurement officer

        Notes:
            - Returns empty DataFrame if either fund centers or cost centers data is empty
            - Removes various internal IDs and user-related columns from the final output
            - Sorts the resulting DataFrame by FC Path
            - Sets multi-level index using FC Path, Fund Center, Fund Center Name, Cost Center, and Cost Center Name
        """

        fc = FundCenterManager().fund_center_dataframe(FundCenter.objects.all())
        cc = CostCenterManager().cost_center_dataframe(CostCenter.objects.all())
        if fc.empty or cc.empty:
            return pd.DataFrame()
        merged = pd.merge(
            fc,
            cc,
            how="left",
            left_on=["Fundcenter_ID", "FC Path", "Fund Center", "Fund Center Name"],
            right_on=[
                "Costcenter_parent_ID",
                "FC Path",
                "Fund Center",
                "Fund Center Name",
            ],
        )
        merged = merged.fillna("")
        merged.set_index(
            [
                "FC Path",
                "Fund Center",
                "Fund Center Name",
                "Cost Center",
                "Cost Center Name",
            ],
            inplace=True,
        )
        unwanted_columns = [
            "Fundcenter_ID_x",
            "Fundcenter_ID_y",
            "Fundcenter_parent_ID_x",
            "Fundcenter_parent_ID_y",
            "Costcenter_ID",
            "CC Path",
            "Fund_ID",
            "Source_ID",
            "Costcenter_parent_ID",
            "Level_y",
            "first name",
            "last name",
            "superuser status",
            "Password",
            "active",
            "date joined",
            "active",
            "email address",
            "staff status",
            "Default_fc_ID",
            "Default_cc_ID",
            "Bftuser_ID",
            "last login",
            "procurement officer",
            "Procurement_officer_ID",
        ]
        for col in unwanted_columns:
            try:
                merged.drop(
                    col,
                    axis=1,
                    inplace=True,
                )
            except KeyError:
                pass

        merged.sort_values(by=["FC Path"], inplace=True)
        merged.rename(columns={"Level_x": "Level", "Username": "Procurement Officer"}, inplace=True)
        return merged

    def financial_structure_styler(self, data: pd.DataFrame):
        """Styles a financial structure DataFrame for display.

        This method applies custom styling to a DataFrame containing financial structure data,
        including left alignment, indentation based on the string length, and alternating row colors.

        Parameters
        ----------
        data : pd.DataFrame
            The DataFrame containing financial structure data to be styled.

        Returns
        -------
        Styler
            A pandas Styler object with the applied formatting and styling.

        Notes
        -----
        The styling includes:
        - Left-aligned text
        - Indentation based on string length
        - Alternating row colors (red)
        - Custom CSS class 'fin-structure'
        """
        def indent(s):
            return f"text-align:left;padding-left:{len(str(s))*4}px"

        html = Styler(data, uuid_len=0, cell_ids=False)
        table_style = [
            {"selector": "tbody:nth-child(odd)", "props": "background-color:red"},
        ]
        data = (
            html.applymap_index(indent, level=0)
            .set_table_attributes("class=fin-structure")
            .set_table_styles(table_style)
        )
        return data

    def CostCenters(self, fundcenter: "str|FundCenter"):
        """
        Get all cost centers associated with a fund center.

        Args:
            fundcenter (Union[str, FundCenter]): The fund center string identifier or FundCenter object.

        Returns:
            QuerySet[CostCenter]: QuerySet containing all cost centers that have a sequence
                starting with the fund center's sequence. Returns None if fundcenter is falsy.

        Example:
            >>> CostCenters("FC123")
            <QuerySet [<CostCenter: CC123A>, <CostCenter: CC123B>]>
        """
        if isinstance(fundcenter, str):
            fundcenter = FundCenterManager().fundcenter(fundcenter)
        if fundcenter:
            return CostCenter.objects.filter(sequence__startswith=fundcenter.sequence)
        return None

    def all(self):
        pass
