# Copyright (c) 2023 Szymon Kasprzycki
# This file is protected by MIT license. See LICENSE for more information.

from dataclasses import dataclass


@dataclass
class FlightData:
    """
    This class is responsible for structuring the flight data.
    """
    origin_airport: str
    destination_airport: str
    price: float
    origin_city: str = None
    destination_city: str = None
    distance: float = None

    @staticmethod
    def from_dict(flight_data: dict) -> 'FlightData':
        """
        This method creates FlightData object from dictionary.
        :param flight_data: dict - flight data
        :return: FlightData object
        """
        return FlightData(
            origin_airport=flight_data['fly_from'],
            destination_airport=flight_data['fly_to'],
            price=-1,
        )

    def __str__(self) -> str:
        """
        This method returns string representation of FlightData object.
        :return: str - string representation of FlightData object
        """
        return f'Flight from {self.origin_city} ({self.origin_airport}) to {self.destination_city} ' \
               f'({self.destination_airport}) for {self.price} EUR.'
