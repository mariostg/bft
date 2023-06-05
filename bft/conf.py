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
    ("Q0", "Q0"),
    ("Q1", "Q1"),
    ("Q2", "Q2"),
    ("Q3", "Q3"),
    ("Q4", "Q4"),
]
