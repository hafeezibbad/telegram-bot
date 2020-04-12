"""
Module containing tests cases for procedures used in Rest and WebAPI.
"""
import unittest
from mongoengine import Q
from datetime import datetime, timedelta
from telegram.bot import Bot
from botapp import create_app
from botapp.models import MyBot, Message
from botapp.api_helpers import procedures
from helper import CONSTANTS


class ProceduresTest(unittest.TestCase):

    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        # Drop all collections
        MyBot.drop_collection()
        Message.drop_collection()
        self.app_context.pop()

    def test_add_bot_procedure_with_no_inputs(self):
        with self.assertRaises(ValueError) as e:
            procedures.add_bot()
            self.assertEqual(str(e.exception),
                             'No/Bad token(String expected) provided to add new'
                             ' bot.')

    def test_add_bot_with_invalid_token_type(self):
        with self.assertRaises(ValueError) as e:
            procedures.add_bot(token=1)
            self.assertEqual(str(e.exception),
                             'Invalid token:{tokn} used for adding live '
                             'bot.'.format(tokn=1))

    def test_add_testbot_valid_token(self):
        status = procedures.add_bot(token='dummy_token', testing=True)
        self.assertIsNotNone(status[0])
        self.assertFalse(status[1])
        self.assertTrue('testbot-' in status[0])

        bot = MyBot.objects(username=status[0]).first()
        self.assertIsNotNone(bot)
        self.assertTrue(bot.test_bot)
        self.assertEqual(bot.first_name, 'test')
        self.assertEqual(bot.last_name, 'bot')

    def test_add_livebot_with_valid_token(self):
        status = procedures.add_bot(token=CONSTANTS.LIVE_BOTS.get(1))
        # Get bot information from Telegram API.
        bot = Bot(token=CONSTANTS.LIVE_BOTS.get(1)).get_me()
        self.assertIsNotNone(status[0])
        self.assertEqual(status[0], bot.username)
        self.assertTrue(status[1])

        mybot = MyBot.objects(username=status[0]).first()
        self.assertIsNotNone(mybot)
        self.assertFalse(mybot.test_bot)
        self.assertEqual(mybot.first_name, bot.first_name)
        self.assertEqual(mybot.last_name, mybot.last_name)
        self.assertEqual(mybot.username, bot.username)
        # Otherwise unittests doesn't end.
        self.assertEqual(procedures.stop_bot(mybot.bot_id), 1)

    def test_add_livebot_with_invalid_token(self):
        bad_token = 'dummy-token'
        with self.assertRaises(ValueError) as e:
            procedures.add_bot(token=bad_token)
            self.assertEqual(str(e.exception),
                             'Invalid token:{tokn} used for adding live '
                             'bot.'.format(tokn=bad_token))

    def test_add_testbot_with_duplicate_token(self):
        bad_token = 'dummy-token'
        # Add a test bot with bad token.
        MyBot(token=bad_token, test_bot=True).save()
        self.assertIsNotNone(MyBot.objects(token=bad_token).first())
        self.assertEqual(MyBot.objects.count(), 1)
        with self.assertRaises(ValueError) as e:
            procedures.add_bot(token=bad_token, testing=True)
            self.assertEqual(str(e.exception),
                             'Bot with given token{tokn} is already present in '
                             'database.'.format(tokn=bad_token))

    def test_add_livebot_with_duplicate_token(self):
        live_token = CONSTANTS.LIVE_BOTS.get(1)
        # Add a live bot with valid token.
        MyBot(token=live_token).save()
        self.assertIsNotNone(MyBot.objects(token=live_token).first())
        self.assertEqual(MyBot.objects.count(), 1)
        with self.assertRaises(ValueError) as e:
            procedures.add_bot(token=live_token)
            self.assertEqual(str(e.exception),
                             'Bot with given token{tokn} is already present in '
                             'database.'.format(tokn=live_token))

    def test_add_testbot_with_duplicate_live_token(self):
        live_token = CONSTANTS.LIVE_BOTS.get(1)
        # Add a live bot with valid token.
        MyBot(token=live_token).save()
        self.assertIsNotNone(MyBot.objects(token=live_token).first())
        self.assertEqual(MyBot.objects.count(), 1)
        with self.assertRaises(ValueError) as e:
            procedures.add_bot(token=live_token, testing=True)
            self.assertEqual(str(e.exception),
                             'Bot with given token{tokn} is already present in '
                             'database.'.format(tokn=live_token))

    def test_add_livebot_with_duplicate_bad_token(self):
        bad_token = 'dummy-token'
        # Add a live bot with valid token.
        MyBot(token=bad_token, test_bot=True).save()
        self.assertIsNotNone(MyBot.objects(token=bad_token).first())
        self.assertEqual(MyBot.objects.count(), 1)
        with self.assertRaises(ValueError) as e:
            procedures.add_bot(token=bad_token)
            self.assertEqual(str(e.exception),
                             'Bot with given token{tokn} is already present in '
                             'database.'.format(tokn=bad_token))

    def test_start_bot_with_no_inputs(self):
        with self.assertRaises(ValueError) as e:
            procedures.start_bot()
            self.assertEqual(str(e.exception),
                             'No botid/username provided with start bot '
                             'request.')

    def test_start_bot_with_invalid_botid(self):
        with self.assertRaises(ValueError) as e:
            procedures.start_bot(botid='abc')
            self.assertEqual(str(e.exception),
                             'Integer value expected for botid in start bot '
                             'request.')

    def test_start_bot_with_invalid_username(self):
        with self.assertRaises(ValueError) as e:
            procedures.start_bot(username=1234)
            self.assertEqual(str(e.exception),
                             'String value expected for username in start bot '
                             'request.')

    def test_start_bot_for_non_existing_botid(self):
        self.assertEqual(procedures.start_bot(botid=12345), -1)

    def test_start_bot_for_non_existing_username(self):
        self.assertEqual(procedures.start_bot(username='unknown-username'), -1)

    def test_start_bot_for_non_existing_botid_username(self):
        self.assertEqual(procedures.start_bot(botid=1234,
                                              username='unknown-username'), -1)

    def test_start_bot_for_test_bot(self):
        bot = MyBot(token='dummy-token', test_bot=True).save()
        self.assertIsNotNone(bot)
        self.assertEqual(procedures.start_bot(botid=bot.bot_id), -2)

    def test_start_livebot_with_valid_botid(self):
        bot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1)).save()
        self.assertIsNotNone(bot)
        self.assertEqual(procedures.start_bot(botid=bot.bot_id), 1)
        bot = MyBot.objects(bot_id=bot.bot_id).first()
        self.assertTrue(bot.state)

        # Otherwise unittests doesn't end.
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), 1)
        bot = MyBot.objects(bot_id=bot.bot_id).first()
        self.assertFalse(bot.state)

    def test_start_livebot_with_valid_username(self):
        bot = Bot(token=CONSTANTS.LIVE_BOTS.get(1)).get_me()
        mybot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1), bot_id=bot.id,
                      username=bot.username, first_name=bot.first_name,
                      last_name=bot.last_name).save()
        self.assertIsNotNone(mybot)
        self.assertEqual(procedures.start_bot(username=str(mybot.username)), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertTrue(mybot.state)

        # Otherwise unittests doesn't end.
        self.assertEqual(procedures.stop_bot(botid=mybot.bot_id), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertFalse(mybot.state)

    def test_start_livebot_with_valid_botid_username(self):
        bot = Bot(token=CONSTANTS.LIVE_BOTS.get(1)).get_me()
        mybot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1), bot_id=bot.id,
                      username=bot.username, first_name=bot.first_name,
                      last_name=bot.last_name).save()
        self.assertIsNotNone(mybot)
        self.assertEqual(procedures.start_bot(botid=mybot.bot_id,
                                              username=str(mybot.username)), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertTrue(mybot.state)

        # Otherwise unittests doesn't end.
        self.assertEqual(procedures.stop_bot(botid=mybot.bot_id), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertFalse(mybot.state)

    def test_start_livebot_with_invalid_botid_valid_username(self):
        bot = Bot(token=CONSTANTS.LIVE_BOTS.get(1)).get_me()
        mybot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1), bot_id=bot.id,
                      username=bot.username, first_name=bot.first_name,
                      last_name=bot.last_name).save()
        self.assertIsNotNone(mybot)
        self.assertEqual(procedures.start_bot(botid=12345,
                                              username=str(mybot.username)), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertTrue(mybot.state)

        # Otherwise unittests doesn't end.
        self.assertEqual(procedures.stop_bot(botid=mybot.bot_id), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertFalse(mybot.state)

    def test_start_livebot_with_valid_botid_invalid_username(self):
        bot = Bot(token=CONSTANTS.LIVE_BOTS.get(1)).get_me()
        mybot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1), bot_id=bot.id,
                      username=bot.username, first_name=bot.first_name,
                      last_name=bot.last_name).save()
        self.assertIsNotNone(mybot)
        self.assertEqual(procedures.start_bot(botid=mybot.bot_id,
                                              username='abcde'), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertTrue(mybot.state)

        # Otherwise unittests doesn't end.
        self.assertEqual(procedures.stop_bot(botid=mybot.bot_id), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertFalse(mybot.state)

    def test_start_livebot_with_bad_token(self):
        bot = MyBot(token='dummy-token').save()
        self.assertIsNotNone(bot)
        with self.assertRaises(ValueError) as e:
            procedures.start_bot(botid=bot.bot_id)
            self.assertEqual(str(e.exception),
                             'Bot:{username} registered with bad token can not '
                             'be started.'.format(username=bot.username))

    def test_stop_bot_with_no_inputs(self):
        with self.assertRaises(ValueError) as e:
            procedures.stop_bot()
            self.assertEqual(str(e.exception),
                             'No botid/username provided with stop bot '
                             'request.')

    def test_stop_bot_with_invalid_botid(self):
        with self.assertRaises(ValueError) as e:
            procedures.stop_bot(botid='abc')
            self.assertEqual(str(e.exception),
                             'Integer value expected for botid in stop bot '
                             'request.')

    def test_stop_bot_with_invalid_username(self):
        with self.assertRaises(ValueError) as e:
            procedures.stop_bot(username=1234)
            self.assertEqual(str(e.exception),
                             'String value expected for username in stop bot '
                             'request.')

    def test_stop_bot_for_non_existing_botid(self):
        self.assertEqual(procedures.stop_bot(botid=12345), -1)

    def test_stop_bot_for_non_existing_username(self):
        self.assertEqual(procedures.stop_bot(username='unknown-username'), -1)

    def test_stop_bot_for_non_existing_botid_username(self):
        self.assertEqual(procedures.stop_bot(botid=1234,
                                             username='unknown-username'), -1)

    def test_stop_bot_for_test_bot(self):
        bot = MyBot(token='dummy-token', test_bot=True).save()
        self.assertIsNotNone(bot)
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), -2)

    def test_stop_bot_never_running_live_bot(self):
        bot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1)).save()
        self.assertIsNotNone(bot)
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), -2)

    def test_stopbot_previously_running_now_stopped_live_bot(self):
        bot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1)).save()
        self.assertIsNotNone(bot)
        self.assertEqual(procedures.start_bot(botid=bot.bot_id), 1)
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), 1)
        bot = MyBot.objects(token=bot.token).first()
        self.assertFalse(bot.state)
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), -2)

    def test_stopbot_valid_running_bot_using_valid_username(self):
        bot = Bot(token=CONSTANTS.LIVE_BOTS.get(1)).get_me()
        mybot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1), bot_id=bot.id,
                      username=bot.username, first_name=bot.first_name,
                      last_name=bot.last_name).save()
        self.assertIsNotNone(mybot)
        self.assertEqual(procedures.start_bot(botid=mybot.bot_id), 1)

        self.assertEqual(procedures.stop_bot(username=str(mybot.username)), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertFalse(mybot.state)

    def test_stopbot_valid_running_bot_using_valid_botid(self):
        bot = Bot(token=CONSTANTS.LIVE_BOTS.get(1)).get_me()
        mybot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1), bot_id=bot.id,
                      username=bot.username, first_name=bot.first_name,
                      last_name=bot.last_name).save()
        self.assertIsNotNone(mybot)
        self.assertEqual(procedures.start_bot(botid=mybot.bot_id), 1)

        self.assertEqual(procedures.stop_bot(botid=mybot.bot_id), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertFalse(mybot.state)

    def test_stopbot_valid_running_bot_using_valid_username_invalid_botid(self):
        bot = Bot(token=CONSTANTS.LIVE_BOTS.get(1)).get_me()
        mybot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1), bot_id=bot.id,
                      username=bot.username, first_name=bot.first_name,
                      last_name=bot.last_name).save()
        self.assertIsNotNone(mybot)
        self.assertEqual(procedures.start_bot(botid=mybot.bot_id), 1)

        self.assertEqual(procedures.stop_bot(botid=12345,
                                             username=str(mybot.username)), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertFalse(mybot.state)

    def test_stopbot_valid_running_bot_using_invalid_username_valid_botid(self):
        bot = Bot(token=CONSTANTS.LIVE_BOTS.get(1)).get_me()
        mybot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1), bot_id=bot.id,
                      username=bot.username, first_name=bot.first_name,
                      last_name=bot.last_name).save()
        self.assertIsNotNone(mybot)
        self.assertEqual(procedures.start_bot(botid=mybot.bot_id), 1)

        assert isinstance(mybot, MyBot)
        self.assertEqual(procedures.stop_bot(botid=mybot.bot_id,
                                             username='abcde'), 1)
        mybot = MyBot.objects(bot_id=mybot.bot_id).first()
        self.assertFalse(mybot.state)

    def test_start_stop_all_with_valid_bots(self):
        bot = MyBot(token=CONSTANTS.LIVE_BOTS.get(1)).save()
        self.assertIsNotNone(bot)
        started = procedures.start_all()
        self.assertTrue(bot.bot_id in started)
        self.assertEqual(len(started),
                         MyBot.objects(test_bot=False).count())
        stopped = procedures.stop_all()
        self.assertTrue(len(stopped), len(started))
        self.assertTrue(bot.bot_id in stopped)

    def test_start_stop_all_with_test_bots(self):
        bot = MyBot(token='dummy-token', test_bot=True).save()
        self.assertIsNotNone(bot)
        started = procedures.start_all()
        self.assertTrue(bot.bot_id not in started)
        self.assertEqual(len(started),
                         MyBot.objects(test_bot=False).count())
        stopped = procedures.stop_all()
        self.assertTrue(bot.bot_id not in stopped)

    def test_start_stop_all_with_test_and_live_bots(self):
        bot1 = MyBot(token='dummy-token', test_bot=True, username='test').save()
        bot2 = MyBot(token=CONSTANTS.LIVE_BOTS.get(1), username='live').save()
        self.assertIsNotNone(bot1)
        self.assertIsNotNone(bot2)
        started = procedures.start_all()
        self.assertTrue(bot2.bot_id in started)
        self.assertTrue(bot1.bot_id not in started)
        self.assertEqual(len(started),
                         MyBot.objects(test_bot=False).count())
        stopped = procedures.stop_all()
        self.assertTrue(bot2.bot_id in stopped)

    def test_filter_messages_by_time(self):
        # Add dummy messages
        Message.generate_fake(10)
        # Add 2 legit messages
        Message(date=datetime.now()-timedelta(minutes=30)).save()
        Message(date=datetime.now() - timedelta(minutes=60)).save()
        # Get messages
        msgs = procedures.filter_messages(time_min=90)
        self.assertEqual(len(msgs), 2)

    def test_filter_messages_by_botid(self):
        # Add dummy messages
        Message.generate_fake(5)
        # Add 2 legit messages
        Message(bot_id=1234).save()
        Message(bot_id=1234).save()
        # Get messages
        msgs = procedures.filter_messages(botid=1234)
        self.assertEqual(len(msgs), 2)

    def test_filter_messages_by_sender_username(self):
        # Add dummy messages
        Message.generate_fake(5)
        # Add 2 legit messages
        Message(sender_username='tester').save()
        Message(sender_username='Tester').save()
        # Get messages
        msgs = procedures.filter_messages(username='tester')
        self.assertEqual(len(msgs), 2)

    def test_filter_messages_by_sender_text(self):
        # Add dummy messages
        Message.generate_fake(5)
        # Add 2 legit messages
        Message(text_content='text-12345').save()
        Message(text_content='TEXT-abcde').save()
        # Get messages
        msgs = procedures.filter_messages(text='text')
        self.assertEqual(len(msgs), 2)

    def test_filter_messages_by_sender_firstname(self):
        # Add dummy messages
        Message.generate_fake(5)
        # Add 2 legit messages
        Message(sender_firstname='tom-hanks', sender_lastname='john').save()
        Message(sender_firstname='tom-cruise', sender_lastname='doe').save()
        # Get messages
        msgs = procedures.filter_messages(name='tom')
        self.assertEqual(len(msgs), 2)

    def test_filter_messages_by_sender_lastname(self):
        # Add dummy messages
        Message.generate_fake(5)
        # Add 2 legit messages
        Message(sender_firstname='doe', sender_lastname='john').save()
        Message(sender_firstname='angel', sender_lastname='johnny').save()
        # Get messages
        msgs = procedures.filter_messages(name='john')
        self.assertEqual(len(msgs), 2)

    def test_filter_messages_by_sender_firstname_lastname(self):
        # Add dummy messages
        Message.generate_fake(10)
        # Remove any message with (possibly) matching names.
        Message.objects(Q(sender_firstname__icontains='john') |
                        Q(sender_lastname__icontains='john')).delete()
        # Add 2 legit messages
        Message(sender_firstname='doe', sender_lastname='john').save()
        Message(sender_firstname='johnathen', sender_lastname='angel').save()
        # Get messages
        msgs = procedures.filter_messages(name='john')
        self.assertEqual(len(msgs), 2)

    def test_filter_messages_by_all_criteria(self):
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
        # Get messages
        msgs = procedures.filter_messages(botid=12345, time_min=15, text='test',
                                          username='tester1', name='test')
        self.assertEqual(len(msgs), 1)
