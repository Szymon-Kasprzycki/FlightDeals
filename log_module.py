# Copyright (c) 2023 Szymon Kasprzycki
# This file is protected by MIT license. See LICENSE for more information.

import logging

FILE_NAME = 'flights_deal.log'
FILE_HANDLER_LEVEL = logging.DEBUG
CONSOLE_HANDLER_LEVEL = logging.INFO


class ProjectLogger:
    """
    This class is responsible for logging.
    It uses static methods to create a logger for the main file and for each module.
    """
    project_name = 'FlightsDeal'
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch = logging.StreamHandler()
    ch.setLevel(CONSOLE_HANDLER_LEVEL)
    ch.setFormatter(formatter)
    fh = logging.FileHandler(FILE_NAME, mode='w+')
    fh.setLevel(FILE_HANDLER_LEVEL)
    fh.setFormatter(formatter)

    @staticmethod
    def setup_main_logger() -> logging.Logger:
        logger = logging.getLogger(ProjectLogger.project_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(ProjectLogger.ch)
        logger.addHandler(ProjectLogger.fh)
        return logger

    @staticmethod
    def get_module_logger(module_name: str = None) -> logging.Logger:
        logger = logging.getLogger(ProjectLogger.project_name + '.' + module_name)
        logger.setLevel(logging.DEBUG)
        logger.addHandler(ProjectLogger.ch)
        logger.addHandler(ProjectLogger.fh)
        return logger
