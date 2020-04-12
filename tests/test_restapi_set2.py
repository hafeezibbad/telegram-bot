"""
Module containing tests cases for Restapi calls for stopbot, start_all_bots,
stop_all_bots
"""
import json
import unittest
from flask import url_for
from botapp import create_app
from botapp.models import MyBot, Message
from helper import CONSTANTS
from botapp.api_helpers import procedures


class ProceduresTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()

    def tearDown(self):
        # Drop all collections
        MyBot.drop_collection()
        Message.drop_collection()
        self.app_context.pop()

    def get_api_headers(self):
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_stop_bot_api_with_post_method(self):
        response = self.client.post(
            url_for('botapi.stop_bot', botid=1234, username='1234'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_stop_bot_api_with_delete_method(self):
        response = self.client.post(
            url_for('botapi.stop_bot', botid=1234, username='1234'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_stop_bot_api_with_get_method(self):
        response = self.client.post(
            url_for('botapi.stop_bot', botid=1234, username='1234'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_stop_bot_api_with_valid_botid_invalid_username(self):
        response = self.client.put(
            url_for('botapi.stop_bot', botid=1234, username=1234),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Please provide valid username (string expected) in "
                         "query string.")

    def test_stop_bot_for_test_bot_wildcard_botid_wildcard_username(self):
        response = self.client.put(
            url_for('botapi.stop_bot', botid=0, username='#'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Please provide valid Bot id (positive integer "
                         "expected) or valid bot username (string expected) in "
                         "request.")

    def test_stop_bot_for_test_bot_valid_botid_wildcard_username(self):
        bot = MyBot(token='dummy-token', test_bot=True,
                    username='testbot1234').save()
        self.assertIsNotNone(bot)
        response = self.client.put(
            url_for('botapi.start_bot', botid=bot.bot_id, username='#'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Testbot bot:{name} can not start polling".format(
                         name=bot.bot_id))

    def test_stop_bot_for_test_bot_valid_botid_valid_username(self):
        bot = MyBot(token='dummy-token', test_bot=True,
                    username='testbot1234').save()
        self.assertIsNotNone(bot)
        response = self.client.put(
            url_for('botapi.stop_bot', botid=bot.bot_id,
                    username=bot.username or '#'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Bot {name} has never started for polling.".format(
                         name=bot.username))

    def test_stop_bot_for_live_bot_valid_botid_valid_username(self):
        self.assertTrue(procedures.add_bot(token=CONSTANTS.LIVE_BOTS.get(1),
                                           testing=False)[1])
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertIsNotNone(bot)
        self.assertTrue(bot.state)      # Bot is polling.
        response = self.client.put(
            url_for('botapi.stop_bot', botid=bot.bot_id,
                    username=bot.username),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_response['message'],
                         "Successfully stopped bot {name} from polling".format(
                             name=bot.username))
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertFalse(bot.state)

    def test_stop_bot_for_live_bot_wildcard_botid_valid_username(self):
        self.assertTrue(procedures.add_bot(token=CONSTANTS.LIVE_BOTS.get(1),
                                           testing=False)[1])
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertIsNotNone(bot)
        self.assertTrue(bot.state)  # Bot is polling.

        response = self.client.put(
            url_for('botapi.stop_bot', botid=0, username=bot.username),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_response['message'],
                         "Successfully stopped bot {name} from polling".format(
                             name=bot.username))
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertFalse(bot.state)

    def test_stop_bot_for_live_bot_valid_botid_wildcard_username(self):
        self.assertTrue(procedures.add_bot(token=CONSTANTS.LIVE_BOTS.get(1),
                                           testing=False)[1])
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertIsNotNone(bot)
        self.assertTrue(bot.state)  # Bot is polling.

        response = self.client.put(
            url_for('botapi.stop_bot', botid=bot.bot_id, username='#'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertEqual(json_response['message'],
                         "Successfully stopped bot {name} from polling".format(
                             name=bot.bot_id))
        self.assertFalse(bot.state)

    def test_stop_bot_for_unregistered_bot_valid_botid_valid_username(self):
        response = self.client.put(
            url_for('botapi.stop_bot', botid=1234,
                    username='non-existing-bot'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Unable to find bot {name} in database.".format(
                             name='non-existing-bot'))

    def test_stop_bot_for_unregistered_bot_wildcard_botid_valid_username(self):
        response = self.client.put(
            url_for('botapi.stop_bot', botid=0, username='non-existing-bot'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Unable to find bot {name} in database.".format(
                             name='non-existing-bot'))

    def test_stop_bot_for_unregistered_bot_valid_botid_wildcard_username(self):
        response = self.client.put(
            url_for('botapi.stop_bot', botid=1234, username='#'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Unable to find bot {name} in database.".format(
                             name=1234))

    # Test case for Start all, stop all bots API calls.
    def test_start_all_bot_api_with_post_method(self):
        response = self.client.post(
            url_for('botapi.start_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_start_all_bot_api_with_delete_method(self):
        response = self.client.post(
            url_for('botapi.start_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_start_all_bot_api_with_get_method(self):
        response = self.client.post(
            url_for('botapi.start_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_stop_all_bot_api_with_post_method(self):
        response = self.client.post(
            url_for('botapi.stop_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_stop_all_bot_api_with_delete_method(self):
        response = self.client.post(
            url_for('botapi.stop_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_stop_all_bot_api_with_get_method(self):
        response = self.client.post(
            url_for('botapi.stop_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_start_stop_all_bots_with_test_bots(self):
        bot = MyBot(token='dummy-token', test_bot=True).save()
        self.assertIsNotNone(bot)
        # Start bots
        response = self.client.put(
            url_for('botapi.start_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'ok')
        self.assertEqual(len(json_response['ids']), 0)

        # Stop bots
        response = self.client.put(
            url_for('botapi.stop_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['ids']), 0)

    def test_start_stop_all_bots_with_test_and_live_bots(self):
        bot1 = MyBot(token='dummy-token', test_bot=True, username='test').save()
        bot2 = MyBot(token=CONSTANTS.LIVE_BOTS.get(1), username='live').save()
        self.assertIsNotNone(bot1)
        self.assertIsNotNone(bot2)
        # Start bots
        response = self.client.put(
            url_for('botapi.start_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'ok')
        self.assertEqual(len(json_response['ids']),
                         MyBot.objects(test_bot=False).count())

        # Stop bots
        response = self.client.put(
            url_for('botapi.stop_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['ids']),
                         MyBot.objects(test_bot=False).count())

    def test_start_stop_all_bots_with_live_bots(self):
        bot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1), username='live').save()
        self.assertIsNotNone(bot)
        # Start bots
        response = self.client.put(
            url_for('botapi.start_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'ok')
        self.assertEqual(len(json_response['ids']),
                         MyBot.objects(test_bot=False).count())

        # Stop bots
        response = self.client.put(
            url_for('botapi.stop_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['ids']),
                         MyBot.objects(test_bot=False).count())
