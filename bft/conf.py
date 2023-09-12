import datetime

"""
Constants used throughout BFT
"""
YEAR_CHOICES = []
current = datetime.datetime.now().year
first = current - 4
last = current + 4
for r in range(first, last):
    YEAR_CHOICES.append((r, str(r)))

QUARTERKEYS = ("0", "1", "2", "3", "4")
QUARTERVALUES = ("Q0", "Q1", "Q2", "Q3", "Q4")
QUARTERS = list(zip(QUARTERKEYS, QUARTERVALUES))

PERIODS = [
    ("1", "P1"),
    ("2", "P2"),
    ("3", "P3"),
    ("4", "P4"),
    ("5", "P5"),
    ("6", "P6"),
    ("7", "P7"),
    ("8", "P8"),
    ("9", "P9"),
    ("10", "P10"),
    ("11", "P11"),
    ("12", "P12"),
    ("13", "P13"),
    ("14", "P14"),
]
PERIODKEYS, PERIODVALUES = zip(*PERIODS)

STATUS = [("FY", "FY"), ("QUARTER", "QUARTER"), ("PERIOD", "PERIOD")]

P2Q = {
    "1": "1",
    "2": "1",
    "3": "1",
    "4": "2",
    "5": "2",
    "6": "2",
    "7": "3",
    "8": "3",
    "9": "3",
    "10": "4",
    "11": "4",
    "12": "4",
}


def is_period(p: str) -> bool:
    """Utility function to determine if argument is an acceptable period

    Args:
        p (str): Period to verify

    Returns:
        bool: If p in an element of PERIODS, return True, false otherwise.
    """
    return str(p) in PERIODKEYS
