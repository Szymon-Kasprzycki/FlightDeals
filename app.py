import time
import os
from data_manager import DataManager
from flight_search import FlightSearch
from notification_manager import NotificationManager
from log_module import ProjectLogger
from flight_data import FlightData


class App:
    """
    This class is responsible for running the application.
    """
    _AUTO_UPDATE_INTERVAL = 120

    def __init__(self):
        self._logger = ProjectLogger().setup_main_logger()
        self._logger.debug('Initializing main app...')
        self._data_manager = DataManager()
        self._config = self._data_manager.get_config()
        self._flight_search = FlightSearch(self._config['tequila_api_key'], self._config['CURRENCY'])
        self._notification_manager = NotificationManager()
        self._update_all_loop = False
        self._logger.debug('App initialized.')

    @staticmethod
    def _clear_screen() -> None:
        """
        This method clears the screen.
        :return: None
        """
        command = 'cls' if os.name in ('nt', 'dos') else 'clear'
        os.system(command)

    @staticmethod
    def _press_enter() -> None:
        """
        This method waits for user to press enter.
        :return: None
        """
        input('Press ENTER to continue...')

    def run(self) -> None:
        """
        This method runs the application.
        :return: None
        """
        self._logger.debug('Running main loop...')
        try:
            while True:
                self._clear_screen()
                operation = self._ask_for_operation()
                self._logger.debug(f'Operation {operation} chosen.')
                print('\n')
                match operation:
                    case 1:
                        self._add_new_flight()
                    case 2:
                        self._search_for_existing_flight_data()
                    case 3:
                        self._update()
                    case 4:
                        self._print_origin_locations()
                    case 5:
                        origin_airport = input('What is your origin airport? (IATA code) -> ')
                        origin_airport_code = self._flight_search.get_iata_code(origin_airport)
                        self._print_destination_locations(origin_airport_code)
                    case 6:
                        self._change_update_all_loop()
                    case 7:
                        self._logger.debug('Exiting...')
                        exit(0)
                print('\n')
                self._press_enter()
        except KeyboardInterrupt:
            self._logger.debug('Exiting...')
            del(self._data_manager)
            del(self._flight_search)
            del(self._notification_manager)
            exit(0)

    def _add_new_flight(self) -> None:
        """
        This method adds new flight from user input.
        :return: None
        """
        self._logger.debug('Asking for flight data...')
        user_input = self._flight_search.ask_for_flight_data()
        self._logger.debug('Searching for flights...')
        flight = self._flight_search.obtain_flight_data(user_input)
        if flight:
            self._data_manager.update_flight(flight)

    def _search_for_existing_flight_data(self) -> None:
        """
        This method searches for existing flight data in database.
        :return: None
        """
        self._logger.debug('Asking for flight data...')
        flight_data = self._flight_search.ask_for_flight_data()
        data = FlightData.from_dict(flight_data)
        self._logger.debug('Flight data received.')
        flight = self._data_manager.get_flight_data(data)
        if flight:
            print(
                f'Flight from {data.origin_airport} to {data.destination_airport} for {flight} {self._config["CURRENCY"]}.')
        else:
            print('Flight not found.')

    def _update(self, send_notifications: bool = False) -> None:
        """
        This method updates all flights in database.
        :param send_notifications: bool - True if sms notifications should be sent, False otherwise
        :return: None
        """
        self._logger.debug('Updating flights...')
        origin_airports = self._data_manager.get_start_locations()
        for o_airport in origin_airports:
            destination_airports = self._data_manager.get_destination_airports(o_airport)
            for d_airport in destination_airports:
                status_code = -1
                self._logger.debug(f'Updating flight from {o_airport} to {d_airport}...')
                search_data = self._flight_search.get_data_dict(o_airport, d_airport)
                flight = self._flight_search.obtain_flight_data(search_data)
                if flight:
                    status_code = self._data_manager.update_flight(flight)
                if status_code == 0 and send_notifications:
                    self._notification_manager.send_message(str(flight))
                time.sleep(1)
        self._logger.debug('Flights updated.')

    def _print_origin_locations(self):
        """
        This method prints available origin locations.
        :return: None
        """
        self._logger.debug('Printing origin locations...')
        origin_airports = self._data_manager.get_start_locations()
        print('Available origin airports:')
        print(", ".join(origin_airports))

    def _print_destination_locations(self, origin_airport: str):
        """
        This method prints available destination locations for given origin airport.
        :param origin_airport: str - origin airport (IATA code)
        :return: None
        """
        self._logger.debug(f'Printing destination locations for {origin_airport}...')
        destination_airports = self._data_manager.get_destination_airports(origin_airport)
        print('Available destination airports:')
        print(", ".join(destination_airports))

    def _change_update_all_loop(self) -> None:
        """
        This method changes update all loop status.
        :return: None
        """
        self._update_all_loop = not self._update_all_loop
        self._logger.info(f'Automatic data updates {"enabled" if self._update_all_loop else "disabled"}.')

    def run_automatic_update(self) -> None:
        while True:
            self._logger.debug('Automatic update tick.')
            if self._update_all_loop:
                self._logger.debug('Automatic update loop on tick.')
                self._update(send_notifications=True)
            time.sleep(self._AUTO_UPDATE_INTERVAL)

    def _ask_for_operation(self) -> int:
        """
        This method asks user for operation.
        1. Add new flight.
        2. Search for existing flight data.
        3. Update existing flight data.
        4. Get available origin airports.
        5. Get available destination airports for given start point.
        6. Set up automatic data updates.
        7. Exit.
        :return: int - operation
        """
        self._clear_screen()
        self._logger.debug('Asking for operation...')
        print('Welcome to Flight Club!')
        print('What do you want to do?')
        print('1. Add new flight.')
        print('2. Search for existing flight data.')
        print('3. Update existing flight data.')
        print('4. Get available origin airports.')
        print('5. Get available destination airports for given start point.')
        print(f'6. Set up automatic data updates. (STATUS: {"ON" if self._update_all_loop else "OFF"})')
        print('7. Exit.')
        operation = input('What do you want to do? -> ')
        self._logger.debug(f'Operation chosen: {operation}')
        if not operation or not operation.isdigit() or int(operation) not in range(1, 8):
            print('You have to choose a number between 1 and 7.')
            self._logger.warning('User did not choose a proper number.')
            return self._ask_for_operation()

        return int(operation)
