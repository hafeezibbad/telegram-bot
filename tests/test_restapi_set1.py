"""
Module containing tests cases for Restapi calls for add_bot, start_bot.
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

    def test_404(self):
        response = self.client.get(
            '/api/wrong/url',
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 404)
        json_response = json.loads(response.data.encode('utf-8'))
        self.assertEqual(json_response['error'], 'not found')
        self.assertEqual(json_response['message'], 'resource not found')

    def test_add_testbot_using_dummy_token_and_test_flag(self):
        response = self.client.post(
            url_for('botapi.add_bot', token='dummy-token', test=1),
            headers=self.get_api_headers()
        )

        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(json_response['status'], 'ok')
        bot = MyBot.objects(token='dummy-token', test_bot=True).first()
        self.assertIsNotNone(bot)
        self.assertEqual(
            json_response['message'],
            "Bot:{name} successfully added to database but could not start "
            "polling.".format(name=bot.username)
        )

    def test_add_testbot_using_invlid_token_type_and_test_flag(self):
        response = self.client.post(
            url_for('botapi.add_bot', token=1234, test=1),
            headers=self.get_api_headers()
        )

        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        bot = MyBot.objects(token='1', test_bot=True).first()
        self.assertIsNone(bot)
        self.assertEqual(json_response['message'],
                         "String expected for token in URL. Integer provided."
        )

    def test_add_testbot_with_dummy_token_no_test_flag(self):
        response = self.client.post(
            url_for('botapi.add_bot', token='dummy-token', test=0),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(MyBot.objects(token='dummy-token').first())
        self.assertEqual(
            json_response['message'],
            "Unable to add Bot. Reason:{reason}".format(
                reason='Invalid token:{tokn} used for adding live bot.'.format(
                    tokn='dummy-token'))
        )

    def test_add_livebot_with_dummy_token(self):
        response = self.client.post(
            url_for('botapi.add_bot', token='dummy-token', test=0),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertIsNone(MyBot.objects(token='dummy-token').first())
        self.assertEqual(
            json_response['message'],
            "Unable to add Bot. Reason:{reason}".format(
                reason='Invalid token:{tokn} used for adding live bot.'.format(
                    tokn='dummy-token'))
        )

    def test_add_livebot_with_valid_token(self):
        response = self.client.post(
            url_for('botapi.add_bot', token=CONSTANTS.LIVE_BOTS.get(1), test=0),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 201)
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertIsNotNone(bot)
        # Live bot is polling, stop it from polling.
        self.assertTrue(bot.state)
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), 1)
        self.assertEqual(
            json_response['message'],
            "Bot:{name} successfully added to database and started "
            "polling.".format(name=bot.username)
        )

    def test_start_bot_api_with_invalid_botid_no_username(self):
        response = self.client.put(
            url_for('botapi.start_bot', botid='-1234', username=''),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(json_response['message'], "resource not found")

    def test_add_bot_api_with_put_method(self):
        response = self.client.put(
            url_for('botapi.add_bot', token='dummy_token', test=1),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_add_bot_api_with_get_method(self):
        response = self.client.get(
            url_for('botapi.add_bot', token='dummy_token', test=1),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_add_bot_api_with_delete_method(self):
        response = self.client.delete(
            url_for('botapi.add_bot', token='dummy_token', test=1),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_start_bot_api_with_post_method(self):
        response = self.client.post(
            url_for('botapi.start_bot', botid=1234, username='1234'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_start_bot_api_with_delete_method(self):
        response = self.client.post(
            url_for('botapi.start_bot', botid=1234, username='1234'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_start_bot_api_with_get_method(self):
        response = self.client.post(
            url_for('botapi.start_bot', botid=1234, username='1234'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 405)

    def test_start_bot_api_with_valid_botid_invalid_username(self):
        response = self.client.put(
            url_for('botapi.start_bot', botid=1234, username=1234),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Please provide valid username (string expected) in "
                         "query string.")

    def test_start_bot_for_test_bot_wildcard_botid_wildcard_username(self):
        response = self.client.put(
            url_for('botapi.start_bot', botid=0, username='#'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Please provide valid Bot id (positive integer "
                         "expected) or valid bot username (string expected) in "
                         "request.")

    def test_start_bot_for_test_bot_valid_botid_wildcard_username(self):
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

    def test_start_bot_for_test_bot_valid_botid_valid_username(self):
        bot = MyBot(token='dummy-token', test_bot=True,
                    username='testbot1234').save()
        self.assertIsNotNone(bot)
        response = self.client.put(
            url_for('botapi.start_bot', botid=bot.bot_id,
                    username=bot.username or '#'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Testbot bot:{name} can not start polling".format(
                         name=bot.username)
                         )

    def test_start_bot_for_live_bot_valid_botid_valid_username(self):
        self.assertTrue(procedures.add_bot(token=CONSTANTS.LIVE_BOTS.get(1),
                                           testing=False)[1])
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertIsNotNone(bot)
        # Stop bot from polling.
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), 1)

        response = self.client.put(
            url_for('botapi.start_bot', botid=bot.bot_id,
                    username=bot.username),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_response['message'],
                         "Polling started for bot {name}".format(
                            name=bot.username)
                         )
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertTrue(bot.state)
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), 1)

    def test_start_bot_for_live_bot_wildcard_botid_valid_username(self):
        self.assertTrue(procedures.add_bot(token=CONSTANTS.LIVE_BOTS.get(1),
                                           testing=False)[1])
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertIsNotNone(bot)
        # Stop bot from polling.
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), 1)

        response = self.client.put(
            url_for('botapi.start_bot', botid=0, username=bot.username),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_response['message'],
                         "Polling started for bot {name}".format(
                            name=bot.username)
                         )
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertTrue(bot.state)
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), 1)

    def test_start_bot_for_live_bot_valid_botid_wildcard_username(self):
        self.assertTrue(procedures.add_bot(token=CONSTANTS.LIVE_BOTS.get(1),
                                           testing=False)[1])
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertIsNotNone(bot)
        # Stop bot from polling.
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), 1)

        response = self.client.put(
            url_for('botapi.start_bot', botid=bot.bot_id, username='#'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json_response['message'],
                         "Polling started for bot {name}".format(
                             name=bot.bot_id)
                         )
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertTrue(bot.state)
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), 1)

    def test_start_bot_for_unregistered_bot_valid_botid_valid_username(self):
        response = self.client.put(
            url_for('botapi.start_bot', botid=1234,
                    username='non-existing-bot'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Unable to find bot {name} in database.".format(
                             name='non-existing-bot'))

    def test_start_bot_for_unregistered_bot_wildcard_botid_valid_username(self):
        response = self.client.put(
            url_for('botapi.start_bot', botid=0, username='non-existing-bot'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Unable to find bot {name} in database.".format(
                             name='non-existing-bot'))

    def test_start_bot_for_unregistered_bot_valid_botid_wildcard_username(self):
        response = self.client.put(
            url_for('botapi.start_bot', botid=1234, username='#'),
            headers=self.get_api_headers()
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(json_response['message'],
                         "Unable to find bot {name} in database.".format(
                             name=1234))
