import pandas as pd
from django.db import models
from django.db.models import Model, QuerySet
from django.forms.models import model_to_dict

from bft.exceptions import BFTDataFrameExceptionError


class BFTDataFrame(pd.DataFrame):
    """This class creates a Pandas DataFrame using either a Django QuerySet, a Django Model instance, or a dictionary.  Column names are renamed according to the django_model passed in the __init__ method.  If field method does not have a verbose name, the column name will be capitalized.

    Typical usage:
    from bft.models import FundCenter
    from utils import dataframe

    fc = FundCenter.objects.all()
    df = dataframe.BFTDataFrame(FundCenter).build(fc)
    print(df)

    Args:
        django_model (django.db.models.Model): The model that the dataframe will be built upon.

    Raises:
        BFTDataFrameExceptionError: Will be raised if not provided with either  <QuerySet | dict | Model> when build method is called.

    Returns:
        _type_: _description_
    """

    dataframe_fields = {}
    dataframe = pd.DataFrame()

    def __init__(self, django_model: models.Model) -> None:
        super().__init__()

        self.django_model = django_model
        self.dataframe_fields = {}
        self.has_data = django_model.objects.all().exists()
        for c in django_model._meta.concrete_fields:
            if c.column.endswith("_id"):
                self.dataframe_fields[c.column] = f"{c.name.capitalize()}_ID"
            elif c.name == "id":
                self.dataframe_fields["id"] = f"{django_model.__name__.capitalize()}_ID"
            elif c.name == c.verbose_name:
                self.dataframe_fields[c.name] = c.name.capitalize()
            else:
                self.dataframe_fields[c.name] = c.verbose_name

    def _rename_columns(self):
        self.dataframe.rename(columns=self.dataframe_fields, inplace=True)

    def _set_dtype(self):
        # TODO Fine tune this, Commitment showing as none.  Maybe do this before colum renaming.
        for c in self.dataframe_fields:
            if self.django_model._meta.get_field(c).get_internal_type() == "DecimalField":
                try:
                    self.dataframe[self.dataframe_fields[c]] = (
                        self.dataframe[self.dataframe_fields[c]].fillna(0).astype(int)
                    )
                except TypeError:
                    print((f"Failed to change type for {c}"))

    def build(
        self,
        model_data: QuerySet | dict | Model,
        rename_columns=True,
        set_dtype=True,
    ) -> pd.DataFrame:
        """Construct a Pandas DataFrame

        Args:
            model_data (QuerySet | dict | Model): Data to use to build the dataframe.
            rename_columns (bool, optional): Whether or not to rename the columns in the dataframe. Defaults to True.
            set_dtype (bool, optional): Whether or not to alter the datatype of the dataframe. Defaults to True in which case, Decimal Type will be casted to int.

        Raises:
            BFTDataFrameExceptionError: Will be raised if the model_data type cannot be handled.

        Returns:
            pd.DataFrame: Returns a Pandas DataFrame.
        """
        if not self.has_data:
            return pd.DataFrame()

        if isinstance(model_data, QuerySet):
            self.dataframe = pd.DataFrame(list(model_data.values()))
        elif isinstance(model_data, dict):
            self.dataframe = pd.DataFrame([model_data])
        elif isinstance(model_data, models.Model):
            self.dataframe = pd.DataFrame([model_to_dict(model_data)])
        else:
            raise BFTDataFrameExceptionError(
                f"Failed to build dataframe, model data type {type(model_data)} not handled"
            )
        if rename_columns:
            self._rename_columns()
        if set_dtype:
            self._set_dtype()
        return self.dataframe
