# Copyright (c) 2023 Szymon Kasprzycki
# This file is protected by MIT license. See LICENSE for more information.

from data_manager import DataManager
from flight_search import FlightSearch
from notification_manager import NotificationManager
from log_module import ProjectLogger


logger = ProjectLogger().setup_main_logger()
SPREADSHEET_ID = '1QfA56f4agDyDdPsrTYYbEF0uDOwgIyJJgHS8jwWteDs'