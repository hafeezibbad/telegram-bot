"""
This module contains the forms used for setting up web UI.
"""

import time
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, IntegerField, SubmitField, \
    BooleanField
from wtforms.validators import NumberRange
from wtforms_components import read_only
from botapp.models import MyBot, Message


class FilteringForm(FlaskForm):
    """
    FlaskForm for setting up form for filtering logged messages.
    :parameter bot_field: Drop-down list containing all bots in the databases.
    :parameter time_field: Drop-down list for choosing time for filtering.
    :parameter time_int_field: Input field for getting time (in minutes) for
    filtering.
    :parameter text_field: Input field for entering text for filtering.
    :parameter username_field: Usernames of all users from which messages
    were recieved.
    :parameter name_field: (Partial) name for sender's firstname, lastname.
    """
    bot_field = SelectField(
        'Choose Bot', coerce=int,
        choices=[(0, 'Select an option')] +
                list(MyBot.objects().all().values_list('bot_id', 'username')))

    time_field = SelectField('Time', coerce=int,
                             choices=[(0, 'Choose'), (10, '10 minutes'),
                                      (30, '30 minutes'), (60, '60 minutes')])

    time_int_field = IntegerField(
        'Enter time (in Minutes)',
        validators=[NumberRange(0, int(time.time())/60,
                                message="Please enter valid time or 0.")])

    text_field = StringField('Text (contains)')

    username_field = SelectField('Sender username', coerce=str,
        choices=[('#', 'Select')] + list(Message.objects(sender_username__nin=[
            'unknown', '']) .values_list('sender_username', 'sender_username')))
    fn_ln_field = StringField('First name/ Last name (contains)')
    submit = SubmitField('Filter')


class AddBotForm(FlaskForm):
    """
    Flask form for adding new Bot.
    :parameter token_field: Token to be used for adding new Bot.
    :parameter is_test_bot: Checked if token is entered for a testbot.
    """
    token = StringField('Enter Bot token')
    is_test_bot = BooleanField('Test bot', default=False)
    submit = SubmitField('Add')


class GetBot(FlaskForm):
    """
    Flask form for getting a bot's information including name, token,
    messages received.
    """
    choose_bot = SelectField('Choose Bot', coerce=str,
                             choices=[('#', 'Select')] + list(
                                 MyBot.objects.values_list(
                                     'username', 'username')))
    submit = SubmitField('Get Info')


class EditBot(FlaskForm):
    """
    Flask form for editing a bot status i.e. enable/disable polling for the bot.
    """
    choose_bot = SelectField('Choose Bot', coerce=str, choices=
                             [('#', 'Select')] +
                               list(MyBot.objects().values_list(
                                   'username', 'username')))
    status_field = StringField('Status')
    toggle = SubmitField()

    def __init__(self, *args, **kwargs):
        super(EditBot, self).__init__(*args, **kwargs)
        read_only(self.status_field)


class FilterCriteria:
    """
    Private class for setting up filtering criteria used in web UI to help
    pagination feature.
    """
    botid = None
    time_off = None
    text = ''
    username = None
    name = None

    def __init__(self, botid, time_off, text, username, name):
        self.botid = botid
        self.time_off = time_off
        self.text = text
        self.username = username
        self.name = name
