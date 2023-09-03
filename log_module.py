# Copyright (c) 2023 Szymon Kasprzycki
# This file is protected by MIT license. See LICENSE for more information.

import logging


class ProjectLogger:
    """
    This class is responsible for logging.
    It uses static methods to create a logger for the main file and for each module.
    """
    PROJECT_NAME = 'FlightsDeal'
    FORMATTER = logging.Formatter("%(asctime)s %(name)-30s %(levelname)-8s %(message)s")
    FILE_HANDLER_LEVEL = logging.DEBUG
    CONSOLE_HANDLER_LEVEL = logging.INFO
    FILE_NAME = 'flights_deal.log'

    @staticmethod
    def prepare_handlers() -> tuple:
        """
        This method prepares handlers for the logger.
        """
        console_handler = logging.StreamHandler()
        console_handler.setLevel(ProjectLogger.CONSOLE_HANDLER_LEVEL)
        console_handler.setFormatter(ProjectLogger.FORMATTER)
        file_handler = logging.FileHandler(ProjectLogger.FILE_NAME, mode='a+')
        file_handler.setLevel(ProjectLogger.FILE_HANDLER_LEVEL)
        file_handler.setFormatter(ProjectLogger.FORMATTER)
        return console_handler, file_handler

    @staticmethod
    def setup_main_logger() -> logging.Logger:
        """
        This method sets up a logger for the main file. It also clears the log file.
        :return: logger object for the main file
        """
        with open(ProjectLogger.FILE_NAME, mode='w+') as file:
            file.write('')
        logger = logging.getLogger(ProjectLogger.PROJECT_NAME)
        logger.setLevel(logging.DEBUG)
        handlers = ProjectLogger.prepare_handlers()
        logger.addHandler(handlers[0])
        logger.addHandler(handlers[1])
        return logger

    @staticmethod
    def get_module_logger(module_name: str = None) -> logging.Logger:
        """
        This method sets up a logger for a module.
        :param module_name: name of the module
        :return: logger object for the module
        """
        logger = logging.getLogger(ProjectLogger.PROJECT_NAME + '.' + module_name)
        logger.setLevel(logging.DEBUG)
        if not logger.hasHandlers():
            handlers = ProjectLogger.prepare_handlers()
            logger.addHandler(handlers[0])
            logger.addHandler(handlers[1])
        return logger
