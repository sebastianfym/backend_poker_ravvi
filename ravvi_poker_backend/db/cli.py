import logging
import argparse

from .dbi import DBI
from . import schema
from . import deploy


def cmd_create_database(args):
    """Create and init database from schema files = production state"""
    DBI.create_database(args.database)

    with DBI(db_name=args.database) as db:
        for name, sql in schema.getSQLFiles():
            sql = sql.replace("%", "%%")
            print("===", name, "===")
            db.execute(sql)
        db.commit()


def cmd_drop_database(args):
    """Drops database (expected to be used during tests)"""
    DBI.drop_database(args.database)


def cmd_deploy_changes(args):
    """Apply schema changes and data manipulation during version upgrade"""
    with DBI(db_name=args.database) as db:
        for name, sql in deploy.getSQLFiles():
            sql = sql.replace("%", "%%")
            print("===", name, "===")
            db.execute(sql)
        db.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=None)
    parser.add_argument("--debug", action="store_true", help="Debug logging")
    commands = parser.add_subparsers()

    # CREATE
    cmd = commands.add_parser("create", help="Creates database")
    cmd.set_defaults(func=cmd_create_database)
    cmd.add_argument("database", help="Name of database")

    # DROP
    cmd = commands.add_parser("drop", help="Dropes database")
    cmd.set_defaults(func=cmd_drop_database)
    cmd.add_argument("database", help="Name of database")

    # DEPLOY (UPGRADE)
    cmd = commands.add_parser("deploy", help="Deploy schema changes")
    cmd.set_defaults(func=cmd_deploy_changes)
    cmd.add_argument("database", nargs="?", help="Name of database")

    args = parser.parse_args()
    if not args.func:
        parser.print_help()
        return
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)
    args.func(args)


if __name__ == "__main__":
    main()
