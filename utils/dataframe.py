import pandas as pd

from django.db.models import QuerySet
from django.db import models
from bft.exceptions import BFTDataFrameExceptionError


class BFTDataFrame(pd.DataFrame):
    dataframe_fields = {}
    dataframe = pd.DataFrame()

    def __init__(self, django_model: models.Model) -> None:
        super().__init__()

        self.django_model = django_model
        self.dataframe_fields = {}
        self.concrete_fields = django_model._meta.concrete_fields
        self.has_data = django_model.objects.all().exists()
        for c in self.concrete_fields:
            if c.name == c.verbose_name:
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
                    self.dataframe[self.dataframe_fields[c]] = self.dataframe[self.dataframe_fields[c]].astype(int)
                except TypeError:
                    print((f"Failed to change type for {c}"))

    def build(self, model_data: QuerySet = None, rename_columns=True, set_dtype=True) -> pd.DataFrame:
        if model_data and not isinstance(model_data, QuerySet):
            raise BFTDataFrameExceptionError("Exception raised in build method")
        if not self.has_data:
            return pd.DataFrame()
        if not model_data:
            model_data = self.django_model.objects.all()
        self.dataframe = pd.DataFrame(list(model_data.values()))
        if rename_columns:
            self._rename_columns()
        if set_dtype:
            self._set_dtype()
        return self.dataframe
