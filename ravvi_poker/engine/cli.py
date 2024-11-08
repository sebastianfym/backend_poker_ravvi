import os
import logging
import argparse

from ..logging import logging_add_parser_args, logging_configure
from .main import run_async_loop

logger = logging.getLogger(__name__)


def cmd_run(args):
    run_async_loop()


def main():
    parser = argparse.ArgumentParser(usage="ravvi_poker_engine [-h] OPTIONS COMMAND ...")
    parser.set_defaults(func=None)

    # add logging options
    logging_add_parser_args(parser)

    # commands
    commands = parser.add_subparsers(title="commands", dest="command")

    # RUN
    cmd = commands.add_parser("run", help="Run service")
    cmd.set_defaults(func=cmd_run)

    # parse arguments
    args = parser.parse_args()
    if not args.func:
        parser.print_help()
        exit(os.EX_USAGE)

    # use parser args to configre logging
    logging_configure(args)

    # execute command
    try:
        args.func(args)
    except Exception as ex:
        logger.exception("'%s' command failed: %s", args.command, ex)
        exit(os.EX_SOFTWARE)


if __name__ == "__main__":
    main()
