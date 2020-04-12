"""
Testing Web UI using selenium
"""
import re
import unittest
import threading
from helper import CONSTANTS
from datetime import datetime, timedelta
from selenium import webdriver
from botapp import create_app
from botapp.models import MyBot, Message
from botapp.api_helpers import procedures


class WebUITestCase(unittest.TestCase):
    client = None

    @classmethod
    def setUpClass(cls):
        # Suppress logging to keep unittest output clean
        import logging
        logger = logging.getLogger('werkzeug')
        logger.setLevel(logging.ERROR)

        # start Firefox
        try:
            cls.client = webdriver.Firefox()
        except Exception as e:
            print e
            logging.critical('Could not start Firefox browser for running '
                             'selenium tests. Error{error}'.format(
                                                            error=e.message))

        # skip the tests if browser is not launched
        if cls.client:
            # Create application
            cls.app = create_app('testing')
            cls.app_context = cls.app.app_context()
            cls.app_context.push()

            # Empty any data if present
            MyBot.objects.delete()
            Message.objects.delete()

            MyBot.drop_collection()
            Message.drop_collection()

            # Populate database
            MyBot.generate_fake(5)
            Message.generate_fake(100)

            # start flask server in another thread.
            threading.Thread(target=cls.app.run).start()

    @classmethod
    def tearDownClass(cls):
        if cls.client:
            # Stop the flask server and close the browser
            cls.client.get('http://localhost:5000/web/shutdown')
            cls.client.close()
            # Remove all data
            MyBot.objects.delete()
            Message.objects.delete()

            MyBot.drop_collection()
            Message.drop_collection()
            # Remove application context
            cls.app_context.pop()

    def setUp(self):
        if not self.client:
            self.skipTest('Web browser not available.')

    def tearDown(self):
        pass

    def test_index_page(self):
        base_address = 'http://localhost:5000/web/index'
        # Navigate to home page
        self.client.get(base_address)
        self.assertTrue(re.search('Telegram Bot App', self.client.page_source))
        # Redirect to index page
        self.client.find_element_by_link_text('Home').click()
        self.assertTrue('Telegram Bot App' in self.client.page_source)
        # Check for messages appearing on home page.
        msgs = Message.objects.all().order_by('-date')
        for msg in msgs[1:10]:
            self.assertTrue(msg.text_content in self.client.page_source)

    def test_filtering_method(self):
        bot = MyBot.objects.first()
        # Add partially matching messages.
        Message(date=datetime.now() - timedelta(minutes=30),
                # Un-match time.
                sender_username='tester1',
                sender_firstname='test',
                sender_lastname='bot',
                text_content='testmessage',
                bot_id=bot.bot_id).save()
        Message(date=datetime.now() - timedelta(minutes=10),
                sender_username='tester2',  # Non-matching sender-username.
                sender_firstname='test',
                sender_lastname='bot',
                text_content='testmessage',
                bot_id=bot.bot_id).save()
        Message(date=datetime.now() - timedelta(minutes=10),
                sender_username='tester1',
                sender_firstname='abc',
                # Non-matching first-name, last-name
                sender_lastname='def',
                text_content='testmessage',
                bot_id=bot.bot_id).save()
        Message(date=datetime.now() - timedelta(minutes=10),
                sender_username='tester1',
                sender_firstname='test',
                sender_lastname='bot',
                text_content='message',  # Non-matching text content
                bot_id=bot.bot_id).save()
        Message(date=datetime.now() - timedelta(minutes=10),
                sender_username='Tester1',
                sender_firstname='Test',
                sender_lastname='Bot',
                text_content='testmessage',
                bot_id=11111).save()  # Non-matching botid
        # Add expected message.
        Message(date=datetime.now() - timedelta(minutes=10),
                sender_username='tester1',
                sender_firstname='test',
                sender_lastname='bot',
                text_content='testmessage',
                bot_id=bot.bot_id).save()

        base_address = 'http://127.0.0.1:5000/web/index'
        # navigate to home page
        self.client.get(base_address)

        # Navigate to filering page
        self.client.find_element_by_link_text('Filter').click()
        self.assertTrue(re.search('Decide Filtering Criteria',
                        self.client.page_source, re.IGNORECASE))

        # Add some filtering criteria
        self.client.find_element_by_name('fn_ln_field').send_keys('test')
        self.client.find_element_by_name('time_field').send_keys('30')
        self.client.find_element_by_name('time_int_field').send_keys('30')
        self.client.find_element_by_name('username_field').send_keys('tester1')
        self.client.find_element_by_name('text_field').send_keys('test')
        self.client.find_element_by_name('submit').click()
        # Ensure that we went to right page
        self.assertTrue(re.search('Filtered Messages',
                                  self.client.page_source, re.IGNORECASE))
        self.assertTrue(re.search('Text:\s+test', self.client.page_source,
                                  re.IGNORECASE))
        self.assertTrue(re.search('sender username:\s+tester1',
                                  self.client.page_source,
                                  re.IGNORECASE))
        self.assertTrue(re.search('sender name:\s+test', self.client.page_source,
                                  re.IGNORECASE))
        self.assertTrue(re.search('Time:\s+30', self.client.page_source,
                                  re.IGNORECASE))
        self.assertTrue(re.search('received from:\s+test\s+bot',
                                  self.client.page_source,
                                  re.IGNORECASE))

    def test_add_test_bot(self):
        base_address = 'http://127.0.0.1:5000/web/index'
        # navigate to home page
        self.client.get(base_address)
        # Navigate to filtering page
        self.client.find_element_by_link_text('New-bot').click()
        self.assertTrue(re.search('Add a new Bot',
                                  self.client.page_source, re.IGNORECASE))
        # add a test bot
        self.client.find_element_by_name('token').send_keys('dummy-bot-token')
        self.client.find_element_by_name('is_test_bot').click()
        self.client.find_element_by_name('submit').click()
        bot = MyBot.objects(token='dummy-bot-token').first()
        self.assertIsNotNone(bot)
        self.assertFalse(bot.state)
        # Assertions.
        self.assertTrue(re.search('Bot\s+{uname}'.format(uname=bot.username),
                                  self.client.page_source, re.IGNORECASE))
        self.assertTrue(re.search('Bot\s+name:\s+test\s+bot',
                                  self.client.page_source, re.IGNORECASE))
        self.assertTrue(re.search('ID:\s+{botid}'.format(botid=bot.bot_id),
                                  self.client.page_source, re.IGNORECASE))
        self.assertTrue(re.search('token:\s+{token}'.format(token=bot.token),
                                  self.client.page_source, re.IGNORECASE))
        self.assertTrue('Testbot Bot:{uname} successfully added to '
                        'database'.format(uname=bot.username)
                        in self.client.page_source)

    def test_add_valid_bot(self):
        base_address = 'http://127.0.0.1:5000/web/index'
        # navigate to home page
        self.client.get(base_address)
        # Navigate to filtering page
        self.client.find_element_by_link_text('New-bot').click()
        self.assertTrue(re.search('Add a new Bot',
                                  self.client.page_source, re.IGNORECASE))
        # add a test bot
        self.client.find_element_by_name('token')\
            .send_keys(CONSTANTS.LIVE_BOTS.get(1))
        self.client.find_element_by_name('submit').click()
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1)).first()
        self.assertIsNotNone(bot)
        self.assertTrue(bot.state)
        # Assertions.
        self.assertTrue(re.search('Bot\s+{uname}'.format(uname=bot.username),
                                  self.client.page_source, re.IGNORECASE))
        self.assertTrue(re.search(
            'Bot\s+name:\s+{fname}\s+{lname}'.format(fname=bot.first_name,
                                                     lname=bot.last_name),
            self.client.page_source, re.IGNORECASE))
        self.assertTrue(re.search('ID:\s+{botid}'.format(botid=bot.bot_id),
                                  self.client.page_source, re.IGNORECASE))
        self.assertTrue(re.search('token:\s+{token}'.format(token=bot.token),
                                  self.client.page_source, re.IGNORECASE))
        self.assertTrue('New bot:{uname} successfully added and started '
                        'polling.'.format(uname=bot.username)
                        in self.client.page_source)
        # Force disable live bot from polling.
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), 1)

    def test_edit_valid_bot(self):
        base_address = 'http://127.0.0.1:5000/web/index'
        # navigate to home page
        self.client.get(base_address)
        # Navigate to filering page
        self.client.find_element_by_link_text('Edit-Bot').click()
        self.assertTrue(re.search('Toggle\s+\(Enable/\s+Disable\)\s+Bot',
                                  self.client.page_source, re.IGNORECASE))

        # add a test bot
        self.assertTrue(procedures.add_bot(token=CONSTANTS.LIVE_BOTS.get(1)))
        bot = MyBot.objects(token=CONSTANTS.LIVE_BOTS.get(1),
                            test_bot=False).first()
        self.assertIsNotNone(bot)
        self.assertTrue(bot.state)
        # self.client.find_elements_by_name('status_field').send_keys('tomato')
        self.client.find_element_by_name('choose_bot').send_keys(
            bot.username.lower())
        self.client.find_element_by_name('toggle').click()
        # check for success
        self.assertTrue('Bot:{uname} successfully stopped polling'.format(
            uname=bot.username) in self.client.page_source)
        self.assertTrue('Disabled' in self.client.page_source)

        # Enable the bot
        self.client.find_element_by_name('choose_bot').send_keys(bot.username)
        self.client.find_element_by_name('toggle').click()

        # check for success
        self.assertTrue('Bot:{uname} successfully started polling'.format(
            uname=bot.username) in self.client.page_source)
        self.assertTrue('Enabled' in self.client.page_source)

        # Force disable live bot from polling.
        self.assertEqual(procedures.stop_bot(botid=bot.bot_id), 1)

    def test_get_bot_info(self):
        base_address = 'http://127.0.0.1:5000/web/index'
        # Add a special bot and some expected messages.
        bot = MyBot(bot_id=123456, username='special test bot',
                    token='special-dummy-token', first_name='special',
                    last_name='bot').save()
        for i in range(5):
            Message(bot_id=bot.bot_id, text_content='message'+str(i)).save()

        # navigate to home page
        self.client.get(base_address)
        # Navigate to filtering page
        self.client.find_element_by_link_text('Get-Bot-Info').click()
        self.assertTrue(re.search('Get Bot Information',
                                  self.client.page_source, re.IGNORECASE))

        self.client.find_element_by_name('choose_bot').send_keys(bot.username)
        self.client.find_element_by_name('submit').click()

        # Redirected to bot information page. Make Assertions.
        self.assertTrue(re.search(bot.username, self.client.page_source,
                                  re.IGNORECASE))
        self.assertTrue(re.search('{fname}\s+{lname}'.format(
            fname=bot.first_name, lname=bot.last_name),
            self.client.page_source, re.IGNORECASE))
        self.assertTrue(re.search('Token:\s+{token}'.format(token=bot.token),
                                  self.client.page_source, re.IGNORECASE))
        msgs = Message.objects(bot_id=bot.bot_id).all()
        for msg in msgs:
            self.assertTrue(msg.text_content in self.client.page_source)
