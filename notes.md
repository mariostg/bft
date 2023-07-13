# Development

---

## Filling in some data

Some stuff to do when startig from fresh for testing purposes.

Do this the following to populate some fund so uploadcsv does not complain of missing funds.

    python manage.py populate

---

## Coverage

    coverage run --omit='*/venv/*' manage.py test
    coverage report
    coverage html
