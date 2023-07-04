class InvalidAllocationException(Exception):
    """Raised when allocation is less than 0."""

    pass


class InvalidOptionException(Exception):
    """Raised when a given value does not exist in available options."""

    pass


class InvalidFiscalYearException(Exception):
    """Raised when Fiscal Year is not valid."""

    pass


class LineItemsDoNotExistError(Exception):
    def __init__(self, parent=None):
        self.message = "No Line items were found in the system."

    def __str__(self):
        return self.message
