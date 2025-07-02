
from django.db import models
from django.db.models import QuerySet


class BookmarkQuerySet(models.QuerySet):
    """A custom QuerySet manager for Bookmark objects.

    This QuerySet manager extends the default Django QuerySet to provide
    additional methods for filtering and retrieving bookmarks based on ownership.

    Methods:
        owner(owner: BftUser | str) -> QuerySet | None:
            Filters bookmarks by owner, accepting either a BftUser instance or username string.
            Returns None if the specified user doesn't exist.

        user_bookmark(request) -> QuerySet | None:
            Retrieves bookmarks for the currently authenticated user from the request.
            Returns None if the user doesn't exist.
    """

    def owner(self, owner: BftUser | str) -> QuerySet | None:
        """Filter queryset by owner.
        This method filters the queryset to only include objects owned by the specified owner.
        Args:
            owner (Union[BftUser, str]): The owner to filter by. Can be either a BftUser instance
                or a username string.
        Returns:
            Union[QuerySet, None]: Returns filtered queryset if owner exists, None if string owner
                not found, or original queryset if no owner specified.
        Raises:
            None
        """

        if not owner:
            return self
        if isinstance(owner, str):
            try:
                owner = BftUser.objects.get(username=owner)
            except owner.DoesNotExist:
                return None
        return self.filter(owner=owner)

    def user_bookmark(self, request):
        """
        Retrieve bookmarks for the authenticated user.

        This method fetches all bookmarks associated with the currently logged-in user.
        If the user doesn't exist, returns None.

        Args:
            request: HttpRequest object containing user authentication details

        Returns:
            QuerySet: Collection of Bookmark objects owned by the user if found
            None: If the user does not exist

        Raises:
            None: Exceptions are handled internally
        """
        try:
            owner = BftUser.objects.get(username=request.user)
            bm = Bookmark.objects.filter(owner=owner)
        except BftUser.DoesNotExist:
            bm = None
        return bm


class Bookmark(models.Model):
    """
    A Django model representing a bookmark in the BFT application.

    The Bookmark model allows users to save and manage their favorite links/URLs along with
    associated query strings. Each bookmark is owned by a BftUser and must be unique for
    that user based on the combination of link, query string and owner.

    Attributes:
        owner (ForeignKey): Reference to the BftUser who owns this bookmark
        bookmark_name (str): Name/title of the bookmark (max 30 characters)
        bookmark_link (str): URL/link of the bookmark (max 125 characters)
        bookmark_query_string (str): Optional query string parameters (max 255 characters)
        objects (Manager): Default model manager
        search (BookmarkQuerySet): Custom queryset manager for advanced search capabilities

    Note:
        The combination of bookmark_link, bookmark_query_string and owner must be unique
        within the application.
    """
    owner = models.ForeignKey(BftUser, on_delete=models.CASCADE, default="", verbose_name="Owner's Favorite")
    bookmark_name = models.CharField(max_length=30)
    bookmark_link = models.CharField(max_length=125)
    bookmark_query_string = models.CharField(max_length=255, null=True)
    objects = models.Manager()
    search = BookmarkQuerySet.as_manager()

    def __str__(self):
        return f"{self.owner} - {self.bookmark_name} - {self.bookmark_link}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "bookmark_link",
                    "bookmark_query_string",
                    "owner",
                ),
                name="%(app_label)s_%(class)s_is_unique",
            )
        ]
