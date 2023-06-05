class InvalidAllocationException(Exception):
    """Raised when allocation is less than 0."""

    pass


class InvalidOptionException(Exception):
    """Raised when a given value does not exist in available options."""

    pass


class InvalidFiscalYearException(Exception):
    """Raised when Fiscal Year is not valid."""

    pass
