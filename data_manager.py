# Copyright (c) 2023 Szymon Kasprzycki
# This file is protected by MIT license. See LICENSE for more information.

import os.path
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
    CLIENT_SECRET_FILE = "client_secret.json"
    TOKEN_FILE = "token.json"
    AVAILABE_RANGE = 'A:B'

    def __init__(self, spreadsheet_id: str):
        # create new logger for DataManager
        self.logger = ProjectLogger().get_module_logger('DataManager')
        self.spreadsheet_id = spreadsheet_id

        # Check if token file exists, if does, load credentials from file
        if os.path.exists(DataManager.TOKEN_FILE):
            self.creds = Credentials.from_authorized_user_file(DataManager.TOKEN_FILE, DataManager.API_SCOPES)
            self.logger.debug('Google credentials loaded from file')

        # If there are no (valid) credentials available, let the user log in using OAuth.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # If credentials are expired, but refresh token is available, refresh credentials
                self.logger.debug('Credentials expired, refreshing...')
                self.creds.refresh(Request())
                self.logger.debug('Credentials refreshed')
            else:
                # If credentials are not available, create new credentials
                self.logger.debug('Credentials not available, creating new...')
                flow = InstalledAppFlow.from_client_secrets_file(DataManager.CLIENT_SECRET_FILE, DataManager.API_SCOPES)
                self.creds = flow.run_local_server(port=0)
                self.logger.debug('Credentials created')
            # Save the credentials for the next run
            with open(DataManager.TOKEN_FILE, 'w+') as token:
                token.write(self.creds.to_json())
                self.logger.debug('Credentials saved to file')

        try:
            # Build the Google service
            service = build(DataManager.API_SERVICE_NAME, DataManager.API_VERSION, credentials=self.creds)
            # Call the Sheets API
            self.sheet = service.spreadsheets()
            self.logger.debug('Google Sheet service created')
        except HttpError as err:
            self.logger.error(err)

    def _prepare_range(self, sheet_id: str, cells: str) -> str:
        """
        This method prepares the range for the Google Sheet API
        :param sheet_id: Sheet id to be updated e.g. 'Sheet1'
        :param cells: Cells to be updated e.g. 'A1:B2'
        :return: Range e.g. 'Sheet1!A1:B2'
        """
        # Check if sheet id is specified
        if sheet_id is None:
            self.logger.error('No sheet id specified')
            raise ValueError('No sheet id specified')

        # Check if cells are specified
        if cells is None:
            self.logger.error('No cells specified')
            raise ValueError('No cells specified')

        # Add sheet id to the range, so it looks like 'Sheet1!A1:B2'
        return f'\'{sheet_id}\'!{cells}'

    @staticmethod
    def _prepare_sheet_id(start_location: str) -> str:
        """
        This method prepares the sheet id for the Google Sheet API
        :param start_location: start location IATA code
        :return: Ready to use sheet id for application e.g. 'FROM_GDA'
        """
        return f'FROM_{start_location}'

    def _create_sheet(self, sheet_id: str) -> bool:
        """
        This method creates the sheet in the connected Google spreadsheet
        :param sheet_id: Sheet id to be created e.g. 'Sheet1'
        :return: True if sheet was created, False otherwise
        """
        status = False

        self.logger.debug(f'Creating sheet {sheet_id}')

        try:
            # Call the Sheets API to create the sheet
            self.logger.debug(f'Calling Sheets API to create sheet {sheet_id}')
            self.sheet.batchUpdate(spreadsheetId=self.spreadsheet_id, body={
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
            self.logger.error(err)

        return status

    def _check_if_sheet_exists(self, sheet_id: str) -> bool:
        """
        This method checks if the sheet exists in the connected Google spreadsheet
        :param sheet_id: Sheet id to be checked e.g. 'Sheet1'
        :return: True if sheet exists, False otherwise
        """
        status = False

        self.logger.debug(f'Checking if sheet {sheet_id} exists')

        # Call the Sheets API to get the list of sheets
        try:
            self.logger.debug(f'Calling Sheets API to get the list of sheets')
            result = self.sheet.get(spreadsheetId=self.spreadsheet_id).execute()
            sheets = result.get('sheets', [])
            self.logger.debug(f'{len(sheets)} sheets found')
        except HttpError as err:
            self.logger.error(err)
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

        self.logger.debug(f'Appending values {new_values} to sheet {sheet_id}')

        # Add sheet id to the range, so it looks like 'Sheet1!A1:B2'
        data_range = self._prepare_range(sheet_id, DataManager.AVAILABE_RANGE)

        self.logger.debug(f'Calling Sheets API to append data to {data_range}')

        try:
            # Call the Sheets API to append the data
            self.sheet.values().append(spreadsheetId=self.spreadsheet_id, range=data_range,
                                       valueInputOption='USER_ENTERED', insertDataOption='INSERT_ROWS',
                                       body={'values': new_values}).execute()
            status = True
        except HttpError as err:
            self.logger.error(err)

        return status

    def _update_data(self, new_values: list, cells_range: str) -> bool:
        """
        This method updates the data in the connected Google spreadsheet
        :param new_values: 2D list of values to update [['New Value A', 'New Value B'], ['New Value C', 'New Value D']]
        :param cells_range: Range to update in Sheet!A1:B2 format --> 'My Custom Sheet!A1:B2'
        :return: True if update was successful, False otherwise
        """
        status = False
        self.logger.debug(f'Updating range `{cells_range}` with values {new_values}')
        try:
            # Call the Sheets API to update the data
            result = self.sheet.values().update(spreadsheetId=self.spreadsheet_id, range=cells_range,
                                                valueInputOption='RAW',
                                                body={'values': new_values}).execute()
            # Check if any cells were updated
            status = result.get('updatedCells') > 0
            if status:
                self.logger.debug(f'{result.get("updatedCells")} cells updated')
            else:
                self.logger.debug(f'No cells updated')
        except HttpError as err:
            self.logger.error(err)

        return status

    def _read_data(self, cells_range: str = None) -> list:
        """
        This method reads the data from the connected Google spreadsheet
        :param cells_range: Range to read in Sheet!A1:B2 format e.g. 'My Custom Sheet!A1:B2'
        :return: 2D list of values [['Value A', 'Value B'], ['Value C', 'Value D']]
        """
        # Check if range is specified
        if cells_range is None:
            self.logger.error('No range specified, using default')
            cells_range = DataManager.AVAILABE_RANGE

        try:
            # Call the Sheets API to read the data
            self.logger.debug('Calling Sheets API to access data')

            # Check if sheet exists
            sheet_id = cells_range.split("!")[0].replace('\'', '')
            if not self._check_if_sheet_exists(sheet_id):
                self.logger.error(f'Sheet `{sheet_id}` does not exist')
                return []

            result = self.sheet.values().get(spreadsheetId=self.spreadsheet_id, range=cells_range).execute()
            values = result.get('values', [])
        except HttpError as err:
            self.logger.error(err)
            values = []
        return values

    def _get_flights_amount(self, start_location: str) -> int:
        """
        This method reads the amount of flights from the connected Google spreadsheet
        :param start_location: start location IATA code
        :return: amount of flights
        """
        self.logger.debug(f'Reading flights amount for {start_location}...')
        # Call the Sheets API to read the data
        sheet_id = self._prepare_sheet_id(start_location)
        read_range = self._prepare_range(sheet_id, DataManager.AVAILABE_RANGE)
        flights = self._read_flights(read_range)

        # Return amount of flights
        self.logger.debug(f'Amount of flights for {start_location}: {len(flights)}')

        return len(flights)

    def _read_flights(self, start_location: str) -> dict:
        """
        This method reads all flights data from the connected Google spreadsheet
        :param start_location: start location IATA code
        :return: dictionary of flights data {'iataCode1': 'lowestPrice1', 'iataCode2': 'lowestPrice2'}
        """
        self.logger.debug(f'Reading flights data...')
        # Call the Sheets API to read the data
        sheet_id = self._prepare_sheet_id(start_location)
        read_range = self._prepare_range(sheet_id, DataManager.AVAILABE_RANGE)
        values = self._read_data(read_range)

        self.logger.debug(f'Collected all flights data')

        self.logger.debug(values)

        # Return dictionary of flight data {'iataCode1': 'lowestPrice1', 'iataCode2': 'lowestPrice2'}
        flights = {f'{row[0]}': int(row[1]) for row in values if len(row) == 2}

        return flights

    def _add_flight(self, flight: dict) -> None:
        """
        This method adds the new flight data to the connected Google spreadsheet
        :param flight: Flight data to add e.g. {'start_iataCode': 'ABC', dest_iataCode': 'ABC', 'lowestPrice': 123}
        :return: True if data added, False otherwise
        """
        self.logger.debug(
            f'Adding flight data: {flight["start_iataCode"]}->{flight["dest_iataCode"]} with price {flight["lowestPrice"]}$'
        )

        # Check if there is data to add
        if flight is None:
            self.logger.error('add_flight: No data to add')
            return

        # Check if sheet exists
        sheet_id = self._prepare_sheet_id(flight["start_iataCode"])
        if not self._check_if_sheet_exists(sheet_id):
            self._create_sheet(sheet_id)

        # Call the Sheets API to add the data
        status = self._append_data(sheet_id,[[flight['dest_iataCode'], flight['lowestPrice']]])

        if status:
            self.logger.debug(f'Flight data added')
        else:
            self.logger.error(f'Flight data not added')

    def get_flight_data(self, start_location: str, destination: str) -> dict:
        """
        This method reads the flight data (by iata code) from the connected Google sheet
        :param start_location: start location IATA code
        :param destination: destination IATA code
        :return: dictionary of certain flight data {'iataCode': 'lowestPrice'} or None if not found
        """
        flights = self._read_flights(start_location=start_location)

        if destination not in flights.keys():
            self.logger.error(f'No flight data found for {start_location}->{destination}')
            raise ValueError(f'No flight data found for {start_location}->{destination}')

        return flights.get(destination)

    def update_flight(self, flight: dict) -> None:
        """
        This method updates the flight data in the connected Google sheet
        :param flight: Flight data to update e.g. {'start_iataCode': 'ABC', 'dest_iataCode': 'ABC', 'lowestPrice': 123}
        :return: None
        """
        self.logger.info(
            f'Updating flight data: {flight["start_iataCode"]}->{flight["dest_iataCode"]} with price {flight["lowestPrice"]}'
        )

        # Check if start location exists in the sheet
        if not self._check_if_sheet_exists(self._prepare_sheet_id(flight["start_iataCode"])):
            self.logger.debug(f'update_flight: There is no sheet for iata code `{flight["start_iataCode"]}`, creating new')
            self._add_flight(flight)
            return

        # Get range to update
        row_number = -1
        existing_values = self._read_flights(flight['start_iataCode'])
        for nr, row in enumerate(existing_values.keys()):
            if row == flight['dest_iataCode']:
                self.logger.debug(f'Found existing entry for `{flight["dest_iataCode"]}`')
                row_number = nr + 1
                break

        # Add new data if there is no data for this destination
        if row_number == -1:
            self.logger.debug(f'update_flight: No data for iata code `{flight["dest_iataCode"]}`')
            self._add_flight(flight)
            return

        # Call the Sheets API to update the data
        sheet_id = self._prepare_sheet_id(flight["start_iataCode"])
        update_range = self._prepare_range(sheet_id, f'B{row_number}')
        status = self._update_data([[flight['lowestPrice']]], update_range)

        if status:
            self.logger.info(f'Flight data updated')
        else:
            self.logger.error(f'Flight data not updated')

    @staticmethod
    def get_flight_dict(start_location: str, destination: str, price: int) -> dict:
        """
        This method creates the flight data dictionary
        :param start_location: start location IATA code
        :param destination: destination IATA code
        :param price: price of the flight
        :return: proper data dictionary
        """
        return {'start_iataCode': start_location, 'dest_iataCode': destination, 'lowestPrice': price}


# TEST CODE
if __name__ == '__main__':
    SPREADSHEET_ID = '1QfA56f4agDyDdPsrTYYbEF0uDOwgIyJJgHS8jwWteDs'
    x = DataManager(SPREADSHEET_ID)

    par_ber_update = DataManager.get_flight_dict('PAR', 'BER', 150)
    x.update_flight(par_ber_update)

    kyi_ber_update = DataManager.get_flight_dict('KYI', 'BER', 1234)
    x.update_flight(kyi_ber_update)

    x.get_flight_data('KYI', 'BER')

    gda_waw_update = DataManager.get_flight_dict('GDA', 'WAW', 21550)
    x.update_flight(gda_waw_update)

    print(f"The least cost for flight to Berlin is: {x.get_flight_data('GDA', 'BER')}$")

    gda_ber_update = DataManager.get_flight_dict('GDA', 'BER', 36522)
    x.update_flight(gda_ber_update)

    gda_ny_update = DataManager.get_flight_dict('GDA', 'NY', 1236522)
    x.update_flight(gda_ny_update)

    print(f"The least cost for flight to Warsaw is: {x.get_flight_data('GDA', 'WAW')}$")
    print(f"The least cost for flight to New York is: {x.get_flight_data('GDA', 'NY')}$")
    print(f"The least cost for flight to Paris is: {x.get_flight_data('GDA', 'PAR')}$")
