import logging

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    if not logger.handlers:  # prevent duplicate handlers if called multiple times
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)
        console.setFormatter(formatter)

        file = logging.FileHandler("Logs/aman.log")
        file.setLevel(logging.DEBUG)
        file.setFormatter(formatter)

        logger.addHandler(console)
        logger.addHandler(file)

    return logger


if __name__ == "__main__":
    logger = get_logger("test_logger")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")