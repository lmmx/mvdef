import logging

__all__ = ["set_up_logging"]


def set_up_logging(name: str, *, verbose: bool = False):
    """
    Initialise the log

    Args:
      name   : To be set as ``__name__`` from the calling module
      verbose: Change this flag to True/False to turn on/off console logging
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    if verbose:
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(console)
    return logger
