# Copyright (c) 2023 Szymon Kasprzycki
# This file is protected by MIT license. See LICENSE for more information.

from data_manager import DataManager
from flight_search import FlightSearch
from notification_manager import NotificationManager
from log_module import ProjectLogger


if __name__ == '__main__':
    logger = ProjectLogger().setup_main_logger()
    data_manager = DataManager()
    config = data_manager.get_config()
    flight_search = FlightSearch(config['tequila_api_key'])
    config = data_manager.get_config()