from django.db import models


class Fund(models.Model):
    fund = models.CharField(max_length=4, unique=True)
    name = models.CharField(max_length=30)
    vote = models.CharField(max_length=1)
    download = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.fund} - {self.name}"

    class Meta:
        ordering = ["-download", "fund"]
