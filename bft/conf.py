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

QUARTERS = [
    ("0", "Q0"),
    ("1", "Q1"),
    ("2", "Q2"),
    ("3", "Q3"),
    ("4", "Q4"),
]

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

STATUS = [("FY", "FY"), ("QUARTER", "QUARTER"), ("PERIOD", "PERIOD")]
