"""
Modules containing database models for MyBot and Message objects
"""
import random
import logging
from datetime import datetime, timedelta
from botapp import db
from helper.helper_functions import generate_secret_key

# Setup logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - '
                           '%(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class MyBot(db.Document):
    """
    Document blueprint for storing Telegram.Bot information in MongoDB
    collection.
    """
    first_name = db.StringField(max_length=64)
    last_name = db.StringField(max_length=64)
    """
    There is a mongoengine bug that unique=True, primary_key=True for same
    document does not invoke NotUniqueError in case of duplication therefore
    token cannot be made primary key. Therefore bot_id (inherently unique) is
    made primary key.
    """
    token = db.StringField(max_length=64, unique=True, required=True)
    username = db.StringField(max_length=64, unique=True)
    bot_id = db.SequenceField(primary_key=True)
    test_bot = db.BooleanField(default=False)
    state = db.BooleanField(default=False)

    meta = {
        'indexes': ['#token'],
        'index_background': True
    }

    @staticmethod
    def generate_fake(entries=10):
        import forgery_py
        from mongoengine import ValidationError, NotUniqueError
        fakes = 0
        while fakes < entries:
            try:
                MyBot(first_name=forgery_py.name.first_name(),
                      last_name=forgery_py.name.last_name(),
                      token=generate_secret_key(length=64),
                      username=forgery_py.internet.user_name(with_num=True),
                      test_bot=True).save()
                fakes += 1
            except (ValidationError, NotUniqueError, Exception):
                pass                  # Do nothing in case of any exception.


class Message(db.Document):
    """
    Document blueprint for storing Telegram.Message (text message)
    information in MongoDB collection.
    """
    msg_id = db.SequenceField(primary_key=True)
    date = db.DateTimeField(default=datetime.now())
    sender_username = db.StringField()
    sender_firstname = db.StringField()
    sender_lastname = db.StringField()
    chatid = db.IntField(default=0)
    text_content = db.StringField()
    bot_id = db.IntField(default=0)

    def to_json(self):
        return {
            'message_id': self.msg_id,
            'date': self.date,
            'chat_id': self.chatid,
            'sender_username': self.sender_username or 'unknown',
            'sender_firstname': self.sender_firstname or 'na',
            'sender_lastname': self.sender_lastname or 'na',
            'text': self.text_content,
            'bot_id': self.bot_id
        }

    @staticmethod
    def generate_fake(entries=1000):
        """
        This function generates fake messages for time between last 48 hours.
        This function is only advised to be used to generate dummy data during
        testing.
        :param entries: Number of fake messages to be generated.
        :return:
        """
        import forgery_py
        from mongoengine import ValidationError, NotUniqueError
        fakes = 0
        if MyBot.objects.count() == 0:
            MyBot.generate_fake(entries/5)
        while fakes < entries:
            try:
                Message(msg_id=random.randint(1, 100000),
                        date=(datetime.now()-timedelta(hours=2)) -
                        timedelta(hours=48),        # Between last 2-48hours.
                        sender_username=forgery_py.internet
                                                  .user_name(with_num=True),
                        sender_firstname=forgery_py.name.first_name(),
                        sender_lastname=forgery_py.name.last_name(),
                        chatid=random.randint(1, 100000),
                        text_content=forgery_py.lorem_ipsum.sentence(),
                        bot_id=random.choice(
                            MyBot.objects().all().values_list('bot_id'))).save()
                fakes += 1
            except (ValidationError, NotUniqueError, Exception):
                pass                    # Do nothing in case of any exception.
