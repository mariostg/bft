find . -path "*/bft/migrations/*.py" -not -name "__init__.py" -delete -print
find . -path "*/bft/migrations/*.pyc"  -delete -print

find . -path "*/charges/migrations/*.py" -not -name "__init__.py" -delete -print
find . -path "*/charges/migrations/*.pyc"  -delete -print

find . -path "*/costcenter/migrations/*.py" -not -name "__init__.py" -delete -print
find . -path "*/costcenter/migrations/*.pyc"  -delete -print

find . -path "*/encumbrance/migrations/*.py" -not -name "__init__.py" -delete -print
find . -path "*/encumbrance/migrations/*.pyc"  -delete -print

find . -path "*/lineitems/migrations/*.py" -not -name "__init__.py" -delete -print
find . -path "*/lineitems/migrations/*.pyc"  -delete -print

find . -path "*/reports/migrations/*.py" -not -name "__init__.py" -delete -print
find . -path "*/reports/migrations/*.pyc" -delete -print

find . -path "*/users/migrations/*.py" -not -name "__init__.py" -delete -print
find . -path "*/users/migrations/*.pyc" -delete -print

if [ -f "db.sqlite3" ]; then
    mv "db.sqlite3" "db.sqlite3.bak"
else
    echo "No database file"
fi

