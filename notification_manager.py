# Copyright (c) 2023 Szymon Kasprzycki
# This file is protected by MIT license. See LICENSE for more information.

import os
import json
from log_module import ProjectLogger
from twilio.rest import Client as TwilioClient
from twilio.rest.api.v2010.account.message import MessageInstance


class NotificationManager:
    """ This class is responsible for sending notifications with the deal flight details. """

    def __init__(self):
        self._logger = ProjectLogger().get_module_logger('NotificationManager')
        self._config = self._read_config()
        self._logger.debug('Initializing NotificationManager...')
        self._client = TwilioClient(self._config['twilio_account_sid'], self._config['twilio_auth_token'])

    def _read_config(self) -> dict:
        """
        Reads config file.
        :return: dict - config file
        """
        if not os.path.exists('.config/twilio_config.json'):
            self._logger.error('Config file not found.')
            raise FileNotFoundError('Twilio config file not found.')
        else:
            self._logger.info('Config file found, reading...')
            with open('.config/twilio_config.json', 'r') as file:
                config = json.load(file)
                return config

    def send_message(self, message: str) -> None:
        """
        Sends SMS message with flight details.
        :param message: str - body of the message
        :return:
        """
        if self._check_message(message):
            self._logger.debug('Sending SMS message...')
            self._send_sms(message)

    def _send_sms(self, msg_body: str) -> None:
        """
        Sends SMS message.
        :param msg_body: str - body of the message
        :return: None
        """
        message = self._client.messages.create(
            body=msg_body,
            from_=self._config['twilio_phone_number'],
            to=self._config['my_phone_number']
        )

        if self._check_message_status(message):
            self._logger.info(f'Message sent: {message.sid}')
        else:
            self._logger.warning(f'Message not sent: {message.sid}')

    def _check_message(self, message: str) -> bool:
        """
        Checks if message is valid.
        :param message: str - body of the message
        :return: bool - True if message is valid, False otherwise
        """
        self._logger.debug(f'Checking message: {message}')
        if len(message) > 1600:
            self._logger.error('Message too long. Max 1600 characters.')
            raise ValueError('Message too long. Max 1600 characters.')
        elif len(message) == 0:
            self._logger.error('Message empty.')
            raise ValueError('Message empty.')
        else:
            self._logger.debug('Message OK.')
            return True

    def _check_message_status(self, message: MessageInstance) -> bool:
        """
        Checks if message was sent.
        :param message: dict - message object returned by Twilio API
        :return: bool - True if message was sent, False otherwise
        """
        return_status = False
        self._logger.debug(f'Checking message status: {message.sid}')
        if message.status in ('sent', 'delivered', 'sending', 'queued', 'accepted', ):
            self._logger.info('Message delivered.')
            return_status = True
        elif message.status in ('failed', 'undelivered'):
            self._logger.warning('Message not delivered.')

        return return_status
