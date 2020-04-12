"""
Module containing tests cases for testing Restapi call adding, removing dummy
data and deleting bots and messages.
"""
import json
import unittest
from flask import url_for
from botapp import create_app
from botapp.models import MyBot, Message


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

    def test_gen_dummy_bot(self):
        response = self.client.post(
            url_for('botapi.gen_dummy_bots', count=10),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        count = MyBot.objects.count()
        self.assertEqual(count, 10)
        self.assertTrue(str(count) in json_response['message'])

    def test_gen_dummy_message(self):
        response = self.client.post(
            url_for('botapi.gen_dummy_msgs', count=100),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        count = Message.objects.count()
        self.assertEqual(count, 100)
        self.assertTrue(str(count) in json_response['message'])

    def test_delete_all_bots(self):
        MyBot.generate_fake(10)
        response = self.client.delete(
            url_for('botapi.delete_all_bots'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        count = MyBot.objects.count()
        self.assertEqual(count, 0)
        self.assertTrue(str(10) in json_response['message'])

    def test_delete_all_message(self):
        Message.generate_fake(100)
        response = self.client.delete(
            url_for('botapi.delete_all_messages'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        count = Message.objects.count()
        self.assertEqual(count, 0)
        self.assertTrue(str(100) in json_response['message'])

    def test_cascade_delete_bot_and_message_by_id_with_valid_botid_and_msgs(
            self):
        bot = MyBot(token='dummy-token', username='testbot').save()
        self.assertIsNotNone(bot)
        Message.generate_fake(10)
        response = self.client.delete(
            url_for('botapi.delete_bot_and_message_by_id', botid=bot.bot_id),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        self.assertEqual(json_response['message'],
                         'Bot:{uname} and {msgs} logged messages '
                         'removed'.format(uname=bot.username, msgs=10))
        self.assertEqual(Message.objects.count(), 0)
        self.assertEqual(MyBot.objects.count(), 0)

    def test_cascade_delete_bot_and_message_by_id_with_valid_botid_and_no_msgs(
            self):
        bot = MyBot(token='dummy-token', username='testbot').save()
        self.assertIsNotNone(bot)
        response = self.client.delete(
            url_for('botapi.delete_bot_and_message_by_id', botid=bot.bot_id),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        self.assertTrue(bot.username in json_response['message'])
        self.assertEqual(json_response['message'],
                         'Bot:{uname} and {msgs} logged messages '
                         'removed'.format(uname=bot.username, msgs=0))

    def test_cascade_delete_bot_and_message_by_id_with_multiple_valid_botid(self):
        bot1 = MyBot(token='dummy-token1', username='testbot1').save()
        bot2 = MyBot(token='dummy-token2', username='testbot2').save()
        self.assertEqual(MyBot.objects.count(), 2)
        response = self.client.delete(
            url_for('botapi.delete_bot_and_message_by_id', botid=bot1.bot_id),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        self.assertEqual(json_response['message'],
                         'Bot:{uname} and {msgs} logged messages '
                         'removed'.format(uname=bot1.username, msgs=0))
        self.assertEqual(MyBot.objects.count(), 1)
        self.assertIsNone(MyBot.objects(token='dummy-token1').first())
        self.assertIsNotNone(MyBot.objects(bot_id=bot2.bot_id).first())

    def test_cascade_delete_bot_with_non_existing_id(self):
        response = self.client.delete(
            url_for('botapi.delete_bot_and_message_by_id', botid=12345),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['error'], 'bad request')
        self.assertEqual(json_response['message'],
                         'No bot registered for ID:{botid}'.format(botid=12345))

    def test_cascade_delete_bot_and_msgs_by_uname_with_messages(self):
        bot = MyBot(token='dummy-token', username='testbot').save()
        self.assertIsNotNone(bot)
        Message.generate_fake(10)
        response = self.client.delete(
            url_for('botapi.delete_bot_and_message_by_uname',
                    username=bot.username),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        self.assertEqual(json_response['message'],
                         'Bot:{uname} and {msgs} logged messages '
                         'removed'.format(uname=bot.username, msgs=10))
        self.assertEqual(Message.objects.count(), 0)
        self.assertEqual(MyBot.objects.count(), 0)

    def test_cascade_delete_bot_and_message_by_uname_with_valid_botid_no_msgs(
            self):
        bot = MyBot(token='dummy-token', username='testbot').save()
        self.assertIsNotNone(bot)
        response = self.client.delete(
            url_for('botapi.delete_bot_and_message_by_uname',
                    username=bot.username),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        self.assertTrue(bot.username in json_response['message'])
        self.assertEqual(json_response['message'],
                         'Bot:{uname} and {msgs} logged messages '
                         'removed'.format(uname=bot.username, msgs=0))

    def test_cascade_delete_bot_and_message_by_uname_with_multiple_valid_botid(
            self):
        bot1 = MyBot(token='dummy-token1', username='testbot1').save()
        bot2 = MyBot(token='dummy-token2', username='testbot2').save()
        self.assertEqual(MyBot.objects.count(), 2)
        response = self.client.delete(
            url_for('botapi.delete_bot_and_message_by_uname',
                    username=bot1.username),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        self.assertEqual(json_response['message'],
                         'Bot:{uname} and {msgs} logged messages '
                         'removed'.format(uname=bot1.username, msgs=0))
        self.assertEqual(MyBot.objects.count(), 1)
        self.assertIsNone(MyBot.objects(username=bot1.username).first())
        self.assertIsNotNone(MyBot.objects(username=bot2.username).first())

    def test_cascade_delete_bot_with_non_existing_uname(self):
        response = self.client.delete(
            url_for('botapi.delete_bot_and_message_by_uname',
                    username='dummy-uname'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['error'], 'bad request')
        self.assertEqual(json_response['message'],
                         'No bot registered with username:'
                         '{uname}'.format(uname='dummy-uname'))

    def test_delete_bot_using_valid_id(self):
        bot = MyBot(token='dummy_token', username='testbot').save()
        self.assertIsNotNone(bot)
        response = self.client.delete(
            url_for('botapi.delete_only_bot_by_id', botid=bot.bot_id),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        self.assertEqual(json_response['message'],
                         'Bot:{uname} registered with ID: {botid} '
                         'removed'.format(uname=bot.username, botid=bot.bot_id))
        self.assertEqual(MyBot.objects.count(), 0)
        self.assertIsNone(MyBot.objects(bot_id=bot.bot_id).first())

    def test_delete_bot_using_invalid_id(self):
        response = self.client.delete(
            url_for('botapi.delete_only_bot_by_id', botid=12345),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['error'], 'bad request')
        self.assertEqual(json_response['message'],
                         'No bot registered for ID:{botid}'.format(botid=12345))

    def test_delete_bot_using_valid_uname(self):
        bot = MyBot(token='dummy_token', username='testbot').save()
        self.assertIsNotNone(bot)
        response = self.client.delete(
            url_for('botapi.delete_only_bot_by_uname', username=bot.username),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['status'], 'success')
        self.assertEqual(json_response['message'],
                         'Bot:{uname} successfully removed'.format(
                             uname=bot.username))
        self.assertEqual(MyBot.objects.count(), 0)
        self.assertIsNone(MyBot.objects(username=bot.username).first())

    def test_delete_bot_using_invalid_uname(self):
        response = self.client.delete(
            url_for('botapi.delete_only_bot_by_uname', username='dummy_uname'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 400)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['error'], 'bad request')
        self.assertEqual(json_response['message'],
                         'No bot registered for username:{uname}'.format(
                             uname='dummy_uname'))
