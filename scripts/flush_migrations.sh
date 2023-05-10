BASEDIR=`pwd`
cd "$BASEDIR/.."
BASEDIR=`pwd`

#  cd '.allocations'
#  find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
#  find . -path "*/migrations/*.pyc"  -delete
#  cd ../bft
#  find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
#  find . -path "*/migrations/*.pyc"  -delete
#  cd ../dashboard
#  find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
#  find . -path "*/migrations/*.pyc"  -delete
#  cd ../reports
#  find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
#  find . -path "*/migrations/*.pyc"  -delete

cd "${BASEDIR}/lineitems"
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete -print
find . -path "*/migrations/*.pyc"  -delete -print

cd "${BASEDIR}/encumbrance"
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete -print
find . -path "*/migrations/*.pyc"  -delete -print

cd "${BASEDIR}/costcenter"
find . -path "*/migrations/*.py" -not -name "__init__.py" -delete -print
find . -path "*/migrations/*.pyc" -delete -print

cd "$BASEDIR"
echo `pwd`
if [ -f "db.sqlite3" ]; then
    rm -v "db.sqlite3"
else
    echo "No database file deletes"
fi

