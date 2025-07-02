
from django.db import models


class SourceManager(models.Manager):
    """A Django model manager for handling Source objects.

    This manager provides methods for retrieving Source objects by their source name
    or primary key.

    Methods:
        source(source: str) -> Optional[Source]:
            Retrieves a Source object by its source name (case-insensitive).
            Returns None if the source does not exist.

        pk(pk: int) -> Optional[Source]:
            Retrieves a Source object by its primary key.
            Returns None if the source does not exist.
    """
    def source(self, source: str):
        """
        Retrieve a Source object based on the source string.

        Args:
            source (str): The source string to search for (case-insensitive).

        Returns:
            Source: The matched Source object if found.
            None: If no matching Source object is found.

        Example:
            >>> source_obj = source('example_source')
            >>> print(source_obj)  # Returns Source object or None
        """
        try:
            obj = Source.objects.get(source__iexact=source)
        except Source.DoesNotExist:
            return None
        return obj

    def pk(self, pk: int):
        """
        Retrieve a Source object by its primary key.

        Args:
            pk (int): Primary key of the Source object to retrieve.

        Returns:
            Source or None: The Source object if found, None if not found.
        """
        try:
            obj = Source.objects.get(pk=pk)
        except Source.DoesNotExist:
            return None
        return obj


class Source(models.Model):
    """A model representing a data source.  The source is used to better describe the characteristics of the cost centers.

    This model stores information about different data sources in the system.
    Each source must have a unique name that is automatically capitalized when saved.

    Attributes:
        source (CharField): The name of the source, limited to 24 characters and must be unique.

    Meta:
        verbose_name_plural (str): Specifies the plural name as "Sources" in the admin interface.

    Methods:
        __str__(): Returns a string representation of the source.
        save(*args, **kwargs): Overrides the default save method to capitalize the source name.

    Manager:
        objects (SourceManager): Custom manager for Source model operations.
    """
    source = models.CharField(max_length=24, unique=True)

    def __str__(self):
        return f"{self.source}"

    class Meta:
        verbose_name_plural = "Sources"

    def save(self, *args, **kwargs):
        self.source = self.source.capitalize()
        super(Source, self).save(*args, **kwargs)

    objects = SourceManager()
