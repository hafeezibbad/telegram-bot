"""
Module containing tests cases for testing Restapi calls for filtering and
adding, removing dummy date.
"""
import json
import string
import random
import unittest
from datetime import datetime, timedelta
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

    def test_filter_messages_by_bot(self):
        for _ in range(3):
            Message(bot_id=1234).save()
            Message(bot_id=random.randint(1, 10)).save()
        # Get messages
        response = self.client.get(
            url_for('botapi.filter_messages_by_bot', bot_id=1234),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['messages']), 3)

    def test_filter_messages_by_username(self):
        for _ in range(3):
            Message(sender_username='TestUser1').save()
            Message(sender_username='TestUser' +
                                    str(random.randint(2, 10))).save()
        # Get messages
        response = self.client.get(
            url_for('botapi.filter_messages_by_username',
                    username='TestUser1'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['messages']), 3)

    def test_filter_messages_by_chatid(self):
        for _ in range(3):
            Message(chatid=123).save()
            Message(chatid=random.randint(200, 300)).save()
        # Get messages
        response = self.client.get(
            url_for('botapi.filter_messages_by_chatid',
                    chatid=123),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['messages']), 3)

    def test_filter_messages_using_botid(self):
        # Add some dummy messages
        MyBot.generate_fake(1)
        Message.generate_fake(5)
        bot = MyBot(bot_id=11111, token='dummy-token', test_bot=True).save()
        self.assertIsNotNone(bot)
        for _ in range(3):
            Message(bot_id=bot.bot_id).save()
        self.assertEqual(Message.objects.count(), 5+3)

        # Get filtered messages
        response = self.client.get(
            url_for('botapi.filter_messages', botid=bot.bot_id, time_off=0,
                    text='#', username='#', name='#'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['messages']), 3)

    def test_filter_messages_using_time_off(self):
        # Add some dummy messages
        Message.generate_fake(5)
        for _ in range(5):
            Message(date=datetime.now()-timedelta(minutes=20)).save()
        self.assertEqual(Message.objects.count(), 5+5)

        # Get filtered messages
        response = self.client.get(
            url_for('botapi.filter_messages', botid=0, time_off=40,
                    text='#', username='#', name='#'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['messages']), 5)

    def test_filter_messages_using_text(self):
        # Add some dummy messages
        Message.generate_fake(5)
        for _ in range(5):
            Message(text_content='message:' +
                                 random.choice(string.ascii_letters)).save()
        self.assertEqual(Message.objects.count(), 5+5)

        # Get filtered messages
        response = self.client.get(
            url_for('botapi.filter_messages', botid=0, time_off=0,
                    text='message', username='#', name='#'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['messages']), 5)

    def test_filter_messages_using_username(self):
        # Add some dummy messages
        Message.generate_fake(5)
        for _ in range(5):
            Message(sender_username='testuser').save()
        self.assertEqual(Message.objects.count(), 5 + 5)

        # Get filtered messages
        response = self.client.get(
            url_for('botapi.filter_messages', botid=0, time_off=0,
                    text='#', username='testuser', name='#'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['messages']), 5)

    def test_filter_messages_using_user_firstname_lastname(self):
        # Add some dummy messages
        Message.generate_fake(5)
        Message(sender_firstname='testuser').save()
        Message(sender_lastname='usertest').save()
        Message(sender_firstname='test', sender_lastname='user').save()
        Message(sender_firstname='user', sender_lastname='test').save()
        self.assertEqual(Message.objects.count(), 5 + 4)

        # Get filtered messages
        response = self.client.get(
            url_for('botapi.filter_messages', botid=0, time_off=0,
                    text='#', username='#', name='test'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['messages']), 4)

    def test_filter_messages_using_no_criteria(self):
        # Add some dummy messages
        Message.generate_fake(5)
        Message(bot_id=1234).save()
        Message(date=datetime.now()-timedelta(hours=1.5)).save()
        Message(text_content='message1234').save()
        Message(sender_username='testuser').save()
        Message(sender_firstname='test', sender_lastname='user').save()
        self.assertEqual(Message.objects.count(), 5 + 5)

        # Get filtered messages
        response = self.client.get(
            url_for('botapi.filter_messages', botid=0, time_off=0,
                    text='#', username='#', name='#'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['messages']), 10)

    def test_filter_messages_using_all_criteria(self):
        # Add dummy messages
        Message.generate_fake(5)
        # Add partially matching messages.
        Message(date=datetime.now() - timedelta(minutes=30),    # Un-match time.
                sender_username='tester1',
                sender_firstname='test',
                sender_lastname='bot',
                text_content='testmessage',
                bot_id=12345).save()
        Message(date=datetime.now() - timedelta(minutes=10),
                sender_username='tester2',  # Non-matching sender-username.
                sender_firstname='test',
                sender_lastname='bot',
                text_content='testmessage',
                bot_id=12345).save()
        Message(date=datetime.now() - timedelta(minutes=10),
                sender_username='tester1',
                sender_firstname='abc',   # Non-matching first-name, last-name
                sender_lastname='def',
                text_content='testmessage',
                bot_id=12345).save()
        Message(date=datetime.now() - timedelta(minutes=10),
                sender_username='tester1',
                sender_firstname='test',
                sender_lastname='bot',
                text_content='message',     # Non-matching text content
                bot_id=12345).save()
        Message(date=datetime.now() - timedelta(minutes=10),
                sender_username='Tester1',
                sender_firstname='Test',
                sender_lastname='Bot',
                text_content='testmessage',
                bot_id=11111).save()         # Non-matching botid
        # Add expected message.
        Message(date=datetime.now()-timedelta(minutes=10),
                sender_username='tester1',
                sender_firstname='test',
                sender_lastname='bot',
                text_content='testmessage',
                bot_id=12345).save()

        # Get filtered messages
        response = self.client.get(
            url_for('botapi.filter_messages', botid=12345, time_off=15,
                    text='test', username='tester1', name='test'),
            headers=self.get_api_headers()
        )
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertEqual(json_response['result'], 'success')
        self.assertEqual(len(json_response['messages']), 1)
