import logging
import argparse

from .dbi import DBI
from .schema import getSQLFiles as getSchemaFiles

def cmdCreate(args):
    db = DBI()
    db.db_name = None
    db.connect(autocommit=True)
    try:
        db.execute(f"CREATE DATABASE {args.database} TEMPLATE template0")
    finally:
        db.close()

    db.db_name = args.database
    db.connect()
    try:
        for name, sql in getSchemaFiles():
            sql = sql.replace('%','%%')
            print("===", name, "===")
            db.execute(sql)
        db.commit()
    finally:
        db.close()

def cmdDrop(args):
    db = DBI()
    db.db_name = None
    db.connect(autocommit=True)
    try:
        db.execute(f"DROP DATABASE IF EXISTS {args.database}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=None)
    parser.add_argument("--debug", action="store_true", help="Debug logging")
    commands = parser.add_subparsers()
    # CREATE
    cmd = commands.add_parser("create", help="Creates database")
    cmd.set_defaults(func=cmdCreate)
    cmd.add_argument("database", help="Name of database")
    # DROP
    cmd = commands.add_parser("drop", help="Dropes database")
    cmd.set_defaults(func=cmdDrop)
    cmd.add_argument("database", help="Name of database")

    args = parser.parse_args()
    if not args.func:
        parser.print_help()
        return
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    args.func(args)


if __name__ == "__main__":
    main()
