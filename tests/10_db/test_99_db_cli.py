import pytest
from ravvi_poker.db.cli import main

def test_db_cli():
    with pytest.raises(SystemExit):
        main(args=['--help'])


def test_db_schema():
    from ravvi_poker.db.schema import getSQLFiles
    files = getSQLFiles()
    assert files

def test_db_deploy():
    from ravvi_poker.db.deploy import getSQLFiles
    files = getSQLFiles()
    assert files is not None
