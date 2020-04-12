"""
This module contains procedures (i.e. functions) used by RestAPI and Web UI
functions.
"""

import time
from datetime import datetime, timedelta
from mongoengine import Q
from botapp.models import MyBot, Message
from mongoengine import NotUniqueError
from telegram.bot import Bot
from telegram.error import InvalidToken
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from . import running_bots, proc_logger


def start(bot, update):
    """
    Handler function for '/start' command message. Application does not log
    this messsage but notifies the users that all messages will be logged.
    :param bot: telegram.bot object receiving the message.
    :param update: message update received by the bot.
    :return:
    """
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="I 'm a bot. I will be logging all this conversation.")
    proc_logger.info('Chat:{chatid} logging started by bot:{bot_uname}'.format(
        chatid=update.message.chatid, bot_uname=bot.username))


def echo(bot, update):
    """
    Handler message for Incoming text messages. It allows the application to
    echo the same message back to be chat from where it was received.
    :param bot: telegram.bot object receiving the message.
    :param update: message update received by the bot.
    :return:
    """
    bot.sendMessage(chat_id=update.message.chat_id, text=update.message.text)
    proc_logger.info('Message echoed for chat:{chatid} by bot:'
                     '{bot_uname}'.format(chatid=update.message.chatid,
                                          bot_uname=bot.username))


def log_message(bot, update):
    """
    Handler for logging incoming messages to the database. It extracts
    sender's information i.e. username, firstname, lastname from incoming
    message along with message_text, ID of bot which received the message as
    well as message and chat id. The extracted information is logged into the
    database.
    :param bot: telegram.bot object receiving the message.
    :param update: message update received by the bot.
    :return:
    """
    message = update.message
    sender = message.from_user
    try:
        Message(msg_id=message.message_id,
                date=message.date,
                sender_username=sender.username,
                sender_firstname=sender.first_name,
                sender_lastname=sender.last_name,
                chatid=message.chat_id,
                text_content=message.text,
                bot_id=bot.id).save()
        proc_logger.info('New message:{msg_id} logged for chat:{chatid} by bot:'
                         '{bot_uname}'.format(msg_id=message.message_id,
                                              chatid=update.message.chatid,
                                              bot_uname=bot.username))
    except Exception as e:
        raise ValueError('Unable to log message. Reason{reason}'.format(
            reason=e.message))


def add_bot(token=None, testing=False):
    """
    This function takes token for adding a new bot in the database. If
    testing flag is on, token is used to add a text bot. Otherwise,
    the application gets bot information e.g. username, ID, firstname,
    lastname from telegram.bot.api and adds the bot to database. It also
    starts polling for message updates from telegram service.
    :param token: Token for telegram.bot object.
    :param testing: Flag to indicate whether the token is for a test bot or
    live telegram bot.
    :return (bot.username, polling_started): Username for newly added bot in
    the database. Polling_started flag tells if polling has started or not.
    :except ValueError: If the token provided is Invalid for a live bot or if
    bot is already present in the database.
    """
    if token is None or type(str(token)) is not str:
        raise ValueError('No/Bad token(String expected) provided to add new '
                         'bot.')
    try:
        if testing:
            # Add a test bot.
            bot = MyBot(first_name='test',
                        last_name='bot',
                        token=token,
                        test_bot=True)
            bot.username = 'testbot-{bid}'.format(bid=bot.bot_id)
            bot.save()
            proc_logger.info('new test-bot:{bot_uname} added to '
                             'database.'.format(bot_uname=bot.username))
            return bot.username, False

        # Get bot information from telegram API for live bot.
        tg_bot = Bot(token=token).getMe()
        bot = MyBot(bot_id=tg_bot.id, first_name=tg_bot.first_name,
                    last_name=tg_bot.last_name, username=tg_bot.username,
                    test_bot=False, token=token).save()

        if start_bot(botid=bot.bot_id):     # Start polling for newly added bot.
            proc_logger.info('new live-bot:{bot_uname} added to '
                             'database and is polling '.format(
                                    bot_uname=bot.username))
            return bot.username, True       # Successfully started polling.
        else:
            proc_logger.info('new live-bot:{bot_uname} added to '
                             'database and is not polling '.format(
                                    bot_uname=bot.username))
            return bot.username, False      # Unable to start polling.
    except (InvalidToken, TypeError):      # Bad token for a live bot.
        proc_logger.warn('Bad token:{tokn} used for adding live bot.'.format(
            tokn=token))
        raise ValueError('Invalid token:{tokn} used for adding live '
                         'bot.'.format(tokn=token))
    except NotUniqueError:                  # Bot already exists in DB.
        proc_logger.warn('A new bot is attempted to be registered using '
                         'previously used token:{tokn}'.format(
                                    tokn=token))
        raise ValueError('Bot with given token{tokn} is already present in '
                         'database.'.format(tokn=token))


def start_bot(botid=None, username=None):
    """
    This function starts polling for a newly added bot. It gets an updater
    object for a valid (i.e. not test) bot and associated dispatcher. It adds
    handlers for responding to /start command and text messages to the
    dispatcher.
    :param botid:  ID of the bot for which start polling request is made.
    :param username: Username of the bot for which start polling request is
    made.
    :return integer: -1 = Unable to find bot with given username/ID in the DB.
    -2 = The requested bot is a testbot, live polling is not available for a
    test bot.
     1 = Successfully started polling for the requested bot.
     0 = Internal error, unable to start polling for the requested bot.
    :except ValueError: If neither Bot ID nor Username is provided.
    """
    if username is None and botid is None:
        raise ValueError('No botid/username provided with start bot request.')
    elif botid is not None and type(botid) is not int:
        raise ValueError('Integer value expected for botid in start bot '
                         'request.')
    elif username is not None and type(username) is not str:
        raise ValueError('String value expected for username in start bot '
                         'request.')
    # Find the requested Bot in database.
    bot = MyBot.objects(bot_id=botid or 0).first() or \
        MyBot.objects(username__iexact=username or '').first()
    if bot is None:         # Requested bot not found in DB.
        proc_logger.error('No bot found with ID:{id} or Username:{uname} for '
                          'starting the polling.'.format(id=botid,
                                                         uname=username))
        return -1
    if bot.test_bot:        # Requested bot is testbot.
        proc_logger.error('Cannot start polling for test-bot with ID:{id} '
                          'or username:{uname}'.format(id=botid,
                                                       uname=username))
        return -2
    if bot.bot_id in running_bots.keys():   # Bot found and previously ran once.
        updater = running_bots.get(bot.bot_id)  # Retrieve updater from dict.
        updater.start_polling()
        bot.state = True
        bot.save()
        proc_logger.info('Successfully started polling for live bot with id:'
                         '{id} or username:{uname}'.format(
                                        id=botid, uname=username))
        return 1                            # Started running requested bot.
    try:
        updater = Updater(token=bot.token)  # Get bot Updater
        dispatcher = updater.dispatcher

        start_handler = CommandHandler('start', start)  # Add Handlers.
        dispatcher.add_handler(start_handler)

        log_handler = MessageHandler([Filters.text], log_message)
        dispatcher.add_handler(log_handler)

        updater.start_polling()                 # Start polling.
        running_bots[bot.bot_id] = updater      # Add to dictionary.
        bot.state = True                        # Update bot state.
        bot.save()
        proc_logger.info('Successfully added and started polling for live bot '
                         'with id:{id} or username:{uname}'.format(
                                id=botid, uname=username))
        return 1
    except InvalidToken:
        proc_logger.error('Unable to start polling for bot registered with ID:'
                          '{id} or username:{uname}.'.format(
                                id=botid, uname=username))
        raise ValueError('Bot:{uname} registered with bad token can not be '
                         'started.'.format(uname=bot.username))
    

def stop_bot(botid=None, username=None):
    """
    This function stops a bot from polling for new message updates.
    :param botid:  ID of the bot for which start polling request is made.
    :param username: Username of the bot for which start polling request is
    made.
    :return Integer: -1 = Bot with requested username/bot ID not found in DB.
    1 = successfully stopped the bot for polling.
    0 = Unable to stop the bot for polling. Internal Error.
    -2 = The requested bot never started polling in the first place.
    """
    if username is None and botid is None:
        raise ValueError('No botid/username provided with stop bot request.')
    elif botid is not None and type(botid) is not int:
        raise ValueError('Integer value expected for stop in start bot '
                         'request.')
    elif username is not None and type(username) is not str:
        raise ValueError('String value expected for username in stop bot '
                         'request.')
    bot = MyBot.objects(bot_id=botid or 0).first() or \
        MyBot.objects(username__iexact=username or '').first()
    if bot is None:
        proc_logger.error('No bot found with ID:{id} or Username:{uname} for '
                          'starting the polling.'.format(id=botid,
                                                         uname=username))
        return -1
    if bot.state:
        try:
            if bot.bot_id in running_bots.keys():
                updater = running_bots.get(bot.bot_id)     # Find bot from dict.
                updater.stop()             # Stop bot
                bot.state = False          # Update bot state to STOP.
                bot.save()
                proc_logger.info(
                    'Successfully stopped polling for live bot with id:{id} '
                    'or username:{uname}'.format(id=botid, uname=username))
                return 1                   # Bot stopped successfully.
            else:
                updater = Updater(token=bot.token)  # Get bot Updater
                dispatcher = updater.dispatcher

                start_handler = CommandHandler('start', start)  # Add Handlers.
                dispatcher.add_handler(start_handler)

                log_handler = MessageHandler([Filters.text], log_message)
                dispatcher.add_handler(log_handler)

                updater.stop()  # Start polling.
                running_bots[bot.bot_id] = updater  # Add to dictionary.
                bot.state = False  # Update bot state.
                bot.save()
                proc_logger.info(
                    'Successfully added and started polling for live bot '
                    'with id:{id} or username:{uname}'.format(id=botid,
                                                              uname=username))
                return 1
        except (KeyError, Exception):
            proc_logger.critical('Unable to start polling for bot registered '
                                 'with ID:{id} or username:{uname}.'
                                 ''.format(id=botid, uname=username))
            return 0  # Unable to stop bot.
    proc_logger.error('Cannot start/stop polling for test-bot with ID:{id} '
                      'or username:{uname}'.format(id=botid,
                                                   uname=username))
    return -2                           # Bot not polling already.


def start_all():
    """
    This function starts all bots in the database.
    :return started_bots: List of bot IDs for bots which successfully started
    polling.
    """
    # Get all non-test (i.e. live) bots.
    bots = MyBot.objects(test_bot=False).all()
    started_bots = []
    # Start all non test bots registered in the database.
    for bot in bots:
        try:
            if start_bot(botid=bot.bot_id) > 0:
                started_bots.append(bot.bot_id)
        except (ValueError, Exception):
            pass                # Skip if some bot is not started.
    proc_logger.info('Successfully started polling for {count} bots out of '
                     '{total} live bots registered in the database.'.format(
                            count=len(started_bots), total=len(bots)))
    return started_bots


def stop_all():
    """
    This function stops all bots for polling which have ever started polling.
    :return stopped_bots: List of bot IDs for Bots which successfully stopped
    polling.
    """
    stopped_bots = []
    # Stop all bots which have ever been started.
    for key in running_bots.keys():
        try:
            stopped_bots.append(key) if stop_bot(botid=key) > 0 else 0
        except (KeyError, Exception):
            pass            # Do nothing
    proc_logger.info('Successfully stopped polling for {count} previously '
                     'running bots'.format(count=len(stopped_bots)))
    return stopped_bots


def filter_messages(time_min=0, botid=None, text='#', username=None,
                    name='#'):
    """
    This function filters the messages logged by Bots based on the 5 given
    fields.
    :param time_min: Time (in minutes) for filtering messages by date.
    :param botid: ID of bot from which message was received.
    :param text: Message text (partially matched.)
    :param username: Senders username (exactly matched.)
    :param name: Sender's firstname or lastname (partially matched.)
    :return messages: Query Set containing filtered messages.
    """
    time_min = time_min if time_min > 0 else int(time.time())/60
    if botid:
        msgs = Message.objects(bot_id=int(botid),
                               date__gt=datetime.now()-timedelta(
                                   minutes=time_min)).order_by('-date')
    else:
        msgs = Message.objects(date__gt=datetime.now() - timedelta(
            minutes=time_min)).order_by('-date')
    if msgs is None:
        return None
    if text and text != '#':                        # Wildcards
        msgs = msgs.filter(Q(text_content__icontains=text))
    if username is not None and username != '#':    # Wildcards
        msgs = msgs.filter(Q(sender_username__iexact=username))
    if name and name != '#':                        # Wildcards
        msgs = msgs.filter(Q(sender_lastname__icontains=name) |
                           Q(sender_firstname__icontains=name))
    proc_logger.info(
        '{count} messages filtered for criteria.botid:{botid}, time(in minutes)'
        ':{time_min}, text:{text}, username={uname},name:{name}'.format(
            count=len(msgs), botid=botid, time_min=time_min, uname=username,
            text=text, name=name))
    return msgs
