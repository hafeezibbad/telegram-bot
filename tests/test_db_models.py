"""
Module containing tests cases for database models i.e. MyBot, Message.
"""
import random
import unittest
import mongoengine
from datetime import datetime
from botapp import create_app
from botapp.models import MyBot, Message
from helper import CONSTANTS


class DocumentModelTestCase(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        # Drop all collections
        MyBot.drop_collection()
        Message.drop_collection()
        self.app_context.pop()

    def test_testbot_creation(self):
        # Add a dummy bot
        MyBot(username='testbot', first_name='test', last_name='bot',
              token='dummy-token', test_bot=True).save()
        # Retrieve the bot
        bot = MyBot.objects(token='dummy-token').first()
        self.assertIsNotNone(bot)
        self.assertEqual(bot.username, 'testbot')
        self.assertEqual(bot.first_name, 'test')
        self.assertEqual(bot.last_name, 'bot')
        self.assertEqual(bot.token, 'dummy-token')
        self.assertFalse(bot.state)
        self.assertTrue(bot.test_bot)

    def test_live_bot_creation(self):
        MyBot(token=CONSTANTS.LIVE_BOTS.get(1)).save()
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertIsNotNone(bot)
        self.assertFalse(bot.test_bot)
        self.assertFalse(bot.state)

    def test_valid_bot_creation(self):
        with self.assertRaises(mongoengine.ValidationError):
            # Invalid token
            MyBot(token=2, username='testbot1', first_name='test1',
                  last_name='bot1', test_bot=True).save()
        with self.assertRaises(mongoengine.ValidationError):
            # Invalid username
            MyBot(token='dummy-token', username=1, first_name='test1',
                  last_name='bot1', test_bot=True).save()
        with self.assertRaises(mongoengine.ValidationError):
            # Invalid first name
            MyBot(token='dummy-token', username='testbot1', first_name=1,
                  last_name='bot1', test_bot=True).save()
        with self.assertRaises(mongoengine.ValidationError):
            # Invalid last name
            MyBot(token='dummy-token', username='testbot1', first_name='test1',
                  last_name=2, test_bot=True).save()
        self.assertEqual(MyBot.objects.count(), 0)

    def test_bot_creation_duplicate_token(self):
        # Add first bot
        MyBot(token='dummy-token', username='testbot1', first_name='test1',
              last_name='bot1', test_bot=True).save()
        with self.assertRaises(mongoengine.NotUniqueError):
            # Add bot with duplicate token
            MyBot(token='dummy-token', username='testbot2', first_name='test2',
                  last_name='bot2', test_bot=True).save()
        self.assertEqual(MyBot.objects.count(), 1)

    def test_bot_creation_duplicate_username(self):
        # Add first bot
        MyBot(token='dummy-token1', username='testbot1', first_name='test1',
              last_name='bot1', test_bot=True).save()
        with self.assertRaises(mongoengine.NotUniqueError):
            # Add bot with duplicate token
            MyBot(token='dummy-token2', username='testbot1', first_name='test2',
                  last_name='bot2', test_bot=True).save()
        self.assertEqual(MyBot.objects.count(), 1)

    def test_bot_creation_require_token(self):
        with self.assertRaises(mongoengine.ValidationError):
            # Token is required for creating MyBot.
            MyBot(username='testbot1', first_name='test2', last_name='bot2',
                  test_bot=True).save()
        self.assertEqual(MyBot.objects.count(), 0)

    def test_fake_bot_generation(self):
        # Generate fake bots
        MyBot.generate_fake(5)
        self.assertEqual(MyBot.objects.count(), 5)
        bot = MyBot.objects.first()
        self.assertTrue(bot.test_bot)
        self.assertEqual(len(bot.token), 64)

    def test_message_creation(self):
        m_id = random.randint(1, 100000)
        Message(msg_id=m_id, date=datetime.now(), sender_username='test_sender',
                sender_firstname='test', sender_lastname='sender',
                chatid=random.randint(1, 1000), text_content='text message',
                bot_id=random.randint(1, 25)).save()
        msg = Message.objects(msg_id=m_id).first()
        self.assertIsNotNone(msg)
        self.assertEqual(msg.sender_username, 'test_sender')
        self.assertEqual(msg.sender_firstname, 'test')
        self.assertEqual(msg.sender_lastname, 'sender')
        self.assertEqual(msg.text_content, 'text message')
        self.assertEqual(Message.objects.count(), 1)

    def test_invalid_message_creation(self):
        with self.assertRaises(mongoengine.ValidationError):
            # Invalid datetime
            Message(msg_id=1, date='a', sender_lastname='sender',
                    sender_username='test_sender', sender_firstname='test',
                    chatid=1, text_content='text message',
                    bot_id=1).save()
        with self.assertRaises(mongoengine.ValidationError):
            # Invalid sender_lastname
            Message(msg_id=1, date=datetime.now(), sender_lastname=1,
                    sender_username='test_sender', sender_firstname='test',
                    chatid=1, text_content='text message',
                    bot_id=1).save()
        with self.assertRaises(mongoengine.ValidationError):
            # Invalid sender_username
            Message(msg_id=1, date=datetime.now(), sender_lastname='test',
                    sender_username=1, sender_firstname='test',
                    chatid=1, text_content='text message',
                    bot_id=1).save()
        with self.assertRaises(mongoengine.ValidationError):
            # Invalid sender_firstname
            Message(msg_id=1, date=datetime.now(), sender_lastname='test',
                    sender_username='test_sender', sender_firstname=1,
                    chatid=1, text_content='text message',
                    bot_id=1).save()
        with self.assertRaises(mongoengine.ValidationError):
            # Invalid chatid
            Message(msg_id=1, date=datetime.now(), sender_lastname='test',
                    sender_username='test_sender', sender_firstname='test',
                    chatid='a', text_content='text message',
                    bot_id=1).save()
        with self.assertRaises(mongoengine.ValidationError):
            # Invalid text_content
            Message(msg_id=1, date=datetime.now(), sender_lastname='test',
                    sender_username='test_sender', sender_firstname='test',
                    chatid=1, text_content=2,
                    bot_id=1).save()
        with self.assertRaises(mongoengine.ValidationError):
            # Invalid bot_id
            Message(msg_id=1, date=datetime.now(), sender_lastname='test',
                    sender_username='test_sender', sender_firstname='test',
                    chatid=1, text_content='text-content',
                    bot_id='id').save()

    def test_generate_fake_message(self):
        MyBot.generate_fake(1)  # Generate a fake bot to associate messages.
        Message.generate_fake(10)
        msgs = Message.objects.all()
        self.assertEqual(len(msgs), 10)

    def test_generate_fake_bot_in_fake_message(self):
        Message.generate_fake(20)
        bots = MyBot.objects.all()
        msgs = Message.objects.all()
        self.assertEqual(len(bots), 4)
        self.assertEqual(len(msgs), 20)
