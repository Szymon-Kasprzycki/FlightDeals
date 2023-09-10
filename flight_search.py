# Copyright (c) 2023 Szymon Kasprzycki
# This file is protected by MIT license. See LICENSE for more information.

import requests
from log_module import ProjectLogger
from datetime import datetime, timedelta
from flight_data import FlightData


class FlightSearch:
    """
    This class is responsible for talking to the Flight Search API.
    """
    _MAIN_ENDPOINT = 'https://tequila-api.kiwi.com'

    def __init__(self, api_key: str, currency: str):
        self._logger = ProjectLogger().get_module_logger("FlightSearch")
        self._logger.debug('Initializing FlightSearch manager...')
        self.query_endpoint = f'{self._MAIN_ENDPOINT}/locations/query'
        self.search_endpoint = f'{self._MAIN_ENDPOINT}/v2/search'
        self._CURRENCY = currency
        self._session = self._setup_session(api_key)
        self._logger.debug('FlightSearch manager initialized.')

    def get_data_dict(self, origin_airport: str, destination_airport: str):
        """
        This method returns data dictionary for given airports.
        :param origin_airport: origin airport (IATA code)
        :param destination_airport: destination airport (IATA code)
        :return: data dictionary
        """
        from_time = datetime.now()
        to_time = datetime.now() + timedelta(days=7)
        night_in_dst_from = (to_time - from_time).days
        night_in_dst_to = night_in_dst_from + 7
        return {
            'fly_from': origin_airport,
            'fly_to': destination_airport,
            'date_from': from_time.strftime('%d/%m/%Y'),
            'date_to': to_time.strftime('%d/%m/%Y'),
            'nights_in_dst_from': night_in_dst_from,
            'nights_in_dst_to': night_in_dst_to,
            'flight_type': 'round',
            'curr': self._CURRENCY,
            'max_stopovers': 0,
            'limit': 1,
            'sort': 'price',
        }

    def ask_for_flight_data(self) -> dict:
        """
        This method asks user for flight data.
        :return: flight data dictionary
        """
        origin_city = input('What is your origin airport? (eg. Warsaw or WAW or LHR) ')
        destination_city = input('What is your destination city? ')
        origin_city = self.get_iata_code(origin_city)
        destination_city = self.get_iata_code(destination_city)
        return self.get_data_dict(origin_city, destination_city)

    def _setup_session(self, api_key: str) -> requests.Session:
        """
        This method sets up session for FlightSearch class.
        :return: None
        """
        self._logger.debug('Setting up session...')
        session = requests.Session()
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'apikey': api_key
        }
        session.headers.update(headers)
        return session

    def get_iata_code(self, city_name: str) -> str:
        """
        This method returns IATA code for given airport (city).
        :param city_name: name of the city
        :return: IATA code
        """
        self._logger.debug(f'Getting IATA code for {city_name}...')
        query = {'term': city_name, 'location_types': 'airport', 'limit': 1, 'active_only': 'true', 'locale': 'en-US'}
        response = self._session.get(url=self.query_endpoint, params=query)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self._logger.error(f'Error while getting IATA code for {city_name}.'
                               f'Error message: {e}')
            raise e
        data = response.json()
        return data['locations'][0]['code']

    def obtain_flight_data(self, query: dict) -> FlightData:
        """
        This method returns flight data for given parameters.
        :param query: flight parameters (see ask_for_flight_data() method)
        :return: flight data - price, origin airport, destination airport, origin city, destination city,
        origin country, destination country, flight link, distance
        """
        self._logger.debug(f'Obtaining flight data for {query["fly_from"]}->{query["fly_to"]}...')

        response = self._session.get(url=self.search_endpoint, params=query)

        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self._logger.error(f'Error while obtaining flight data for {query["fly_from"]}->{query["fly_to"]}.'
                               f'Error message: {e}')
            raise e

        resp_dict = response.json()
        data = resp_dict['data']

        if len(data) == 0:
            self._logger.warning(f'No flights found for {query["fly_from"]}->{query["fly_to"]}.')
            return None

        return FlightData(
            price=data[0]['price'],
            origin_airport=data[0]['flyFrom'],
            destination_airport=data[0]['flyTo'],
            origin_city=data[0]['cityFrom'],
            destination_city=data[0]['cityTo'],
            distance=data[0]['distance']
        )
