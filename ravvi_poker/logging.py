import os
import sys
import yaml
import logging
from logging import getLogger
from logging.handlers import TimedRotatingFileHandler


def logging_add_parser_args(parser):
    """Добавление необходимых параметров в argsparser для поддержки логирования
    * --log-config LOG_CONFIG_PATH
    * --log-file LOG_FILE_PATH
    * --log-debug
    """

    parser.add_argument(
        "--log-config", type=str, default="", help="Path to log config file"
    )
    parser.add_argument("--log-file", type=str, default="", help="Path to log file")
    parser.add_argument(
        "--log-debug", action="store_true", default=False, help="Log DEBUG level"
    )


def logging_configure(args):
    """Настройка логирования в соответствии с параметрами указаными в командной строке

    см logging_add_parser_args
    """
    if args.log_config and (args.log_file or args.log_debug):
        print(
            "ERROR: --log-config and --log-file|debug are mutually exclusive",
            file=sys.stderr,
        )
        exit(os.EX_CONFIG)
    if args.log_config:
        try:
            path = os.path.expanduser(args.log_config)
            with open(path, "r") as f:
                log_config = yaml.safe_load(f)
            logging.config.dictConfig(log_config)
        except Exception as ex:
            print("Failed lo load config: %s", ex, file=sys.stderr)
            exit(os.EX_CONFIG)
    else:
        handlers = [logging.StreamHandler(sys.stderr)]
        if args.log_file:
            path = os.path.expanduser(args.log_file)
            handler = TimedRotatingFileHandler(filename=path, when="D")
            handlers.append(handler)
        logging.basicConfig(
            level=logging.DEBUG if args.log_debug else logging.INFO,
            handlers=handlers,
            format="%(asctime)s.%(msecs)03d: %(process)d: %(levelname)s: %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

class ObjectLoggerAdapter(logging.LoggerAdapter):
    def __init__(self, logger, func) -> None:
        super().__init__(logger, None)
        self.func = func

    def process(self, msg, kwargs):
        value = self.func()
        if value is not None:
            msg = f"{value}: "+msg
        return super().process(msg, kwargs)

