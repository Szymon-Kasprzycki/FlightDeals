# Copyright (c) 2023 Szymon Kasprzycki
# This file is protected by MIT license. See LICENSE for more information.

import requests
from log_module import ProjectLogger
from datetime import datetime, timedelta


class FlightSearch:
    """
    This class is responsible for talking to the Flight Search API.
    """
    _MAIN_ENDPOINT = 'https://tequila-api.kiwi.com'
    CURRENCY = 'EUR'

    def __init__(self, api_key: str):
        self._logger = ProjectLogger().get_module_logger("FlightSearch")
        self._logger.debug('Initializing FlightSearch manager...')
        self.query_endpoint = f'{self._MAIN_ENDPOINT}/locations/query'
        self.search_endpoint = f'{self._MAIN_ENDPOINT}/v2/search'
        self._session = requests.Session()
        self._headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'apikey': api_key
        }
        self._session.headers.update(self._headers)
        self._logger.debug('FlightSearch manager initialized.')

    @staticmethod
    def ask_for_flight_data() -> dict:
        """
        This method asks user for flight data.
        :return: flight data dictionary
        """
        origin_city = input('What is your origin airport? (be specific, e.g. Warsaw Chopin Airport) ')
        destination_city = input('What is your destination city? ')
        from_time = datetime.now()
        to_time = datetime.now() + timedelta(days=7)
        night_in_dst_from = (to_time - from_time).days
        night_in_dst_to = night_in_dst_from + 7
        return {
            'fly_from': origin_city,
            'fly_to': destination_city,
            'date_from': from_time.strftime('%Y-%m-%d'),
            'date_to': to_time.strftime('%Y-%m-%d'),
            'nights_in_dst_from': night_in_dst_from,
            'nights_in_dst_to': night_in_dst_to,
            'flight_type': 'round',
            'curr': FlightSearch.CURRENCY,
            'max_stopovers': 0,
            'limit': 1,
            'sort': 'price',
        }

    def get_iata_code(self, city_name: str) -> str:
        """
        This method returns IATA code for given airport (city).
        :param city_name: name of the city
        :return: IATA code
        """
        self._logger.debug(f'Getting IATA code for {city_name}...')
        query = {'term': city_name, 'location_types': 'airports'}
        response = self._session.get(url=self.query_endpoint, params=query)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            self._logger.error(f'Error while getting IATA code for {city_name}.'
                               f'Error message: {e}')
            raise e
        return response.json()['locations'][0]['code']

    def obtain_flight_data(self, query: dict) -> dict:
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

        data = response.json()['data'][0]

        to_return = {
            'price': data['price'],
            'origin_airport': data['flyFrom'],
            'destination_airport': data['flyTo'],
            'origin_city': data['cityFrom'],
            'destination_city': data['cityTo'],
            'origin_country': data['countryFrom']['name'],
            'destination_country': data['countryTo']['name'],
            'distance': data['distance'],
        }

        return to_return
