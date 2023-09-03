# Copyright (c) 2023 Szymon Kasprzycki
# This file is protected by MIT license. See LICENSE for more information.

# EXAMPLE USAGE
# from data_manager import DataManager
# manager = DataManager(SPREADSHEET_ID)
# manager.update_flight('GDA', 'WAW', 21650) --> updates the lowest price for flight from GDA to WAW to 21650
# manager.update_flight('GDA', 'BER', 46522) --> updates the lowest price for flight from GDA to BER to 46522
# manager.get_flight_data('GDA', 'WAW') --> returns the actual lowest price for flight from GDA to WAW
# manager.get_flight_data('GDA', 'BER') --> returns the actual lowest price for flight from GDA to BER

import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from log_module import ProjectLogger


class DataManager:
    """
        This class is responsible for talking to the Google Spreadsheet.
    """
    API_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
    API_SERVICE_NAME = "sheets"
    API_VERSION = "v4"
    AVAILABLE_RANGE = 'A:B'

    def __init__(self):
        # create new logger for DataManager
        self._logger = ProjectLogger().get_module_logger('DataManager')

        self._config = self._check_if_config_folder_exists()

        self._logger.debug('Initializing DataManager...')
        self._spreadsheet_id = self._config['google_sheet_id']

        # Check if token file exists, if it does, load credentials from file
        if os.path.exists(self._config['google_token_file']):
            self._creds = Credentials.from_authorized_user_file(self._config['google_token_file'], DataManager.API_SCOPES)
            self._logger.debug('Google credentials loaded from file')

        # If there are no (valid) credentials available, let the user log in using OAuth.
        if not self._creds or not self._creds.valid:
            if self._creds and self._creds.expired and self._creds.refresh_token:
                # If credentials are expired, but refresh token is available, refresh credentials
                self._logger.debug('Credentials expired, refreshing...')
                self._creds.refresh(Request())
                self._logger.debug('Credentials refreshed')
            else:
                # If credentials are not available, create new credentials
                self._logger.debug('Credentials not available, creating new...')
                flow = InstalledAppFlow.from_client_secrets_file(self._config['google_credentials_file'],
                                                                 DataManager.API_SCOPES)
                self._creds = flow.run_local_server(port=0)
                self._logger.debug('Credentials created')
            # Save the credentials for the next run
            with open(self._config['google_token_file'], 'w+') as token:
                token.write(self._creds.to_json())
                self._logger.debug('Credentials saved to file')

        try:
            # Build the Google service
            service = build(DataManager.API_SERVICE_NAME, DataManager.API_VERSION, credentials=self._creds)
            # Call the Sheets API
            self._sheet = service.spreadsheets()
            self._logger.debug('Google Sheet service created')
        except HttpError as err:
            self._logger.error(err)

        self._logger.debug('DataManager initialized')

    @staticmethod
    def _prepare_range(sheet_id: str, cells: str) -> str:
        """
        This method prepares the range for the Google Sheet API
        :param sheet_id: Sheet id to be updated e.g. 'Sheet1'
        :param cells: Cells to be updated e.g. 'A1:B2'
        :return: Range e.g. 'Sheet1!A1:B2'
        """
        return f'\'{sheet_id}\'!{cells}'

    @staticmethod
    def _prepare_sheet_id(start_location: str) -> str:
        """
        This method prepares the sheet id for the Google Sheet API
        :param start_location: start location IATA code
        :return: Ready to use sheet id for application e.g. 'FROM_GDA'
        """
        return f'FROM_{start_location}'

    @staticmethod
    def get_flight_dict(start_location: str, destination: str, price: int) -> dict:
        """
        This method creates the flight data dictionary
        :param start_location: start location IATA code
        :param destination: destination IATA code
        :param price: price of the flight
        :return: proper data dictionary
        """
        return {'origin_airport': start_location, 'destination_airport': destination, 'price': price}

    def _check_if_config_folder_exists(self) -> dict:
        """
        This function checks if config folder exists. If not, it creates it.
        :return: config dictionary
        """
        config = {
            'tequila_api_key': '',
            'google_token_file': '.config/token.json',
            'google_credentials_file': '.config/client_secret.json',
            'google_sheet_id': ''
        }

        if not os.path.exists('.config/'):
            self._logger.warning('Config folder does not exist, creating...')
            os.mkdir('.config')

        if not os.path.exists('.config/config.json'):
            self._logger.warning('Config file does not exist, creating...')

            with open('.config/config.json', 'w+') as f:
                f.write(json.dumps(config))

        else:
            with open('.config/config.json', 'r') as f:
                config = json.load(f)

        if not os.path.exists(config['google_token_file']):
            self._logger.warning('Google token file does not exist, creating...')

            with open(config['google_token_file'], 'w+') as f:
                f.write('')

        if not os.path.exists(config['google_credentials_file']):
            print("XD")
            self._logger.error(
                'Google credentials file does not exist! Please download it from Google Cloud Platform and put it in .config folder. Name it `client_secret.json` and try again.')

            raise FileNotFoundError('Google credentials file not found! More info in log file.')

        return config

    def get_config(self) -> dict:
        """
        This method returns the config dictionary
        :return: config dictionary with `tequila_api_key`, `google_token_file`, `google_credentials_file` and `google_sheet_id`
        """
        return self._config

    def _create_sheet(self, sheet_id: str) -> bool:
        """
        This method creates the sheet in the connected Google spreadsheet
        :param sheet_id: Sheet id to be created e.g. 'Sheet1'
        :return: True if sheet was created, False otherwise
        """
        status = False

        self._logger.debug(f'Creating sheet {sheet_id}')

        try:
            # Call the Sheets API to create the sheet
            self._logger.debug(f'Calling Sheets API to create sheet {sheet_id}')
            self._sheet.batchUpdate(spreadsheetId=self._spreadsheet_id, body={
                'requests': [
                    {
                        'addSheet': {
                            'properties': {
                                'title': sheet_id
                            }
                        }
                    }
                ]
            }).execute()
            status = True
        except HttpError as err:
            self._logger.error(err)

        return status

    def _check_if_sheet_exists(self, sheet_id: str) -> bool:
        """
        This method checks if the sheet exists in the connected Google spreadsheet
        :param sheet_id: Sheet id to be checked e.g. 'Sheet1'
        :return: True if sheet exists, False otherwise
        """
        status = False

        self._logger.debug(f'Checking if sheet {sheet_id} exists')

        # Call the Sheets API to get the list of sheets
        try:
            self._logger.debug(f'Calling Sheets API to get the list of sheets')
            result = self._sheet.get(spreadsheetId=self._spreadsheet_id).execute()
            sheets = result.get('sheets', [])
            self._logger.debug(f'{len(sheets)} sheets found')
        except HttpError as err:
            self._logger.error(err)
            sheets = []

        # Check if sheet exists
        for sheet in sheets:
            if sheet['properties']['title'] == sheet_id:
                status = True
                break

        return status

    def _append_data(self, sheet_id: str, new_values: list) -> bool:
        """
        This method appends the data to the connected Google spreadsheet
        :param sheet_id: Sheet id to be updated e.g. 'Sheet1'
        :param new_values: 2D list of values to append e.g. [['New Value A', 'New Value B'], ['New Value C', 'New Value D']]
        :return: True if append was successful, False otherwise
        """
        status = False

        self._logger.debug(f'Appending values {new_values} to sheet {sheet_id}')

        # Add sheet id to the range, so it looks like 'Sheet1!A1:B2'
        data_range = self._prepare_range(sheet_id, DataManager.AVAILABLE_RANGE)

        self._logger.debug(f'Calling Sheets API to append data to {data_range}')

        try:
            # Call the Sheets API to append the data
            self._sheet.values().append(spreadsheetId=self._spreadsheet_id, range=data_range,
                                        valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS',
                                        body={'values': new_values}).execute()
            status = True
        except HttpError as err:
            self._logger.error(err)

        return status

    def _update_data(self, new_values: list, cells_range: str) -> bool:
        """
        This method updates the data in the connected Google spreadsheet
        :param new_values: 2D list of values to update [['New Value A', 'New Value B'], ['New Value C', 'New Value D']]
        :param cells_range: Range to update in Sheet!A1:B2 format --> 'My Custom Sheet!A1:B2'
        :return: True if update was successful, False otherwise
        """
        status = False
        self._logger.debug(f'Updating range `{cells_range}` with values {new_values}')
        try:
            # Call the Sheets API to update the data
            result = self._sheet.values().update(spreadsheetId=self._spreadsheet_id, range=cells_range,
                                                 valueInputOption='RAW',
                                                 body={'values': new_values}).execute()
            # Check if any cells were updated
            status = result.get('updatedCells') > 0
            if status:
                self._logger.debug(f'{result.get("updatedCells")} cells updated')
            else:
                self._logger.debug(f'No cells updated')
        except HttpError as err:
            self._logger.error(err)

        return status

    def _read_data(self, cells_range: str = None) -> list:
        """
        This method reads the data from the connected Google spreadsheet
        :param cells_range: Range to read in Sheet!A1:B2 format e.g. 'My Custom Sheet!A1:B2'
        :return: 2D list of values [['Value A', 'Value B'], ['Value C', 'Value D']]
        """
        # Check if range is specified
        if cells_range is None:
            self._logger.error('No range specified, using default')
            cells_range = DataManager.AVAILABLE_RANGE

        try:
            # Call the Sheets API to read the data
            self._logger.debug('Calling Sheets API to access data')

            # Check if sheet exists
            sheet_id = cells_range.split("!")[0].replace('\'', '')
            if not self._check_if_sheet_exists(sheet_id):
                self._logger.error(f'Sheet `{sheet_id}` does not exist')
                return []

            result = self._sheet.values().get(spreadsheetId=self._spreadsheet_id, range=cells_range).execute()
            values = result.get('values', [])
        except HttpError as err:
            self._logger.error(err)
            values = []
        return values

    def _get_flights_amount(self, start_location: str) -> int:
        """
        This method reads the amount of flights from the connected Google spreadsheet
        :param start_location: start location IATA code
        :return: amount of flights
        """
        self._logger.debug(f'Reading flights amount for {start_location}...')
        # Call the Sheets API to read the data
        sheet_id = self._prepare_sheet_id(start_location)
        read_range = self._prepare_range(sheet_id, DataManager.AVAILABLE_RANGE)
        flights = self._read_flights(read_range)

        # Return amount of flights
        self._logger.debug(f'Amount of flights for {start_location}: {len(flights)}')

        return len(flights)

    def _read_flights(self, start_location: str) -> dict:
        """
        This method reads all flights data from the connected Google spreadsheet
        :param start_location: start location IATA code
        :return: dictionary of flights data {'iataCode1': 'lowestPrice1', 'iataCode2': 'lowestPrice2'}
        """
        self._logger.debug(f'Reading flights data...')
        # Call the Sheets API to read the data
        sheet_id = self._prepare_sheet_id(start_location)
        read_range = self._prepare_range(sheet_id, DataManager.AVAILABLE_RANGE)
        values = self._read_data(read_range)

        self._logger.debug(f'Collected all flights data')

        self._logger.debug(values)

        # Return dictionary of flight data {'iataCode1': 'lowestPrice1', 'iataCode2': 'lowestPrice2'}
        flights = {f'{row[0]}': int(row[1]) for row in values if len(row) == 2}

        return flights

    def _add_flight(self, flight: dict) -> None:
        """
        This method adds the new flight data to the connected Google spreadsheet
        :param flight: Flight data to add e.g. {'start_iata_code': 'ABC', dest_iata_code': 'ABC', 'lowestPrice': 123}
        :return: True if data added, False otherwise
        """
        self._logger.debug(
            f'Adding flight data: {flight["origin_airport"]}->{flight["destination_airport"]} with price {flight["price"]}$'
        )

        # Check if there is data to add
        if flight is None:
            self._logger.error('add_flight: No data to add')
            return

        # Check if sheet exists
        sheet_id = self._prepare_sheet_id(flight["origin_airport"])
        if not self._check_if_sheet_exists(sheet_id):
            self._create_sheet(sheet_id)

        # Call the Sheets API to add the data
        status = self._append_data(sheet_id, [[flight['destination_airport'], flight['price']]])

        if status:
            self._logger.debug(f'Flight data added')
        else:
            self._logger.error(f'Flight data not added')

    def get_flight_data(self, start_location: str, destination: str) -> dict:
        """
        This method reads the flight data (by iata code) from the connected Google sheet
        :param start_location: start location IATA code
        :param destination: destination IATA code
        :return: dictionary of certain flight data {'iataCode': 'lowestPrice'}
        :raises ValueError: if there is no flight data for given start and destination
        """
        flights = self._read_flights(start_location=start_location)

        if destination not in flights.keys():
            self._logger.error(f'No flight data found for {start_location}->{destination}')
            raise ValueError(f'No flight data found for {start_location}->{destination}')

        return flights.get(destination)

    def update_flight(self, start: str, dest: str, price: int) -> None:
        """
        This method updates the flight data in the connected Google sheet
        :param price:
        :param dest:
        :param start: Flight data to update e.g. {'start_iata_code': 'ABC', 'dest_iata_code': 'ABC', 'lowestPrice': 123}
        :return: None
        :raises ValueError: if error occurred during update process
        """
        self._logger.info(
            f'Updating flight data: {start}->{dest} with price {price}'
        )

        flight = self.get_flight_dict(start, dest, price)

        # Check if start location exists in the sheet
        if not self._check_if_sheet_exists(self._prepare_sheet_id(flight["origin_airport"])):
            self._logger.debug(
                f'update_flight: There is no sheet for iata code `{flight["origin_airport"]}`, creating new')
            self._add_flight(flight)
            return

        # Get range to update
        row_number = -1
        existing_values = self._read_flights(flight['origin_airport'])
        for nr, row in enumerate(existing_values.keys()):
            if row == flight['destination_airport']:
                self._logger.debug(f'Found existing entry for `{flight["destination_airport"]}`')
                row_number = nr + 1
                break

        # Add new data if there is no data for this destination
        if row_number == -1:
            self._logger.debug(f'update_flight: No data for iata code `{flight["destination_airport"]}`')
            self._add_flight(flight)
            return

        # Call the Sheets API to update the data
        sheet_id = self._prepare_sheet_id(flight["origin_airport"])
        update_range = self._prepare_range(sheet_id, f'B{row_number}')
        status = self._update_data([[flight['price']]], update_range)

        if status:
            self._logger.info(f'Flight data updated')
        else:
            self._logger.error(f'Flight data not updated')
            raise ValueError(f'Flight data not updated')
