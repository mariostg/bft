# Development

---

## Filling in some data

Some stuff to do when startig from fresh for testing purposes.

Do this the following to populate some fund so uploadcsv does not complain of missing funds.

    from costcenter.models import Fund

    Fund.objects.create(fund="c113", name="NP", vote=1)
    Fund.objects.create(fund="L101", name="Fund L101", vote=1)
    Fund.objects.create(fund="c523", name="Fund C523", vote=1)

---

## Coverage

    coverage run --omit='*/venv/*' manage.py test
    coverage report
    coverage html
