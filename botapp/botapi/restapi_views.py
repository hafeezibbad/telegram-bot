"""
Function calls for RestAPIs.
"""
from flask import jsonify
from botapp.api_helpers import procedures
from botapp.botapi import botapi, botapi_logger
from botapp.models import Message, MyBot
from .errors import bad_request, internal_server_error


@botapi.route('/addbot/<token>/<int:test>', methods=['POST'])
def add_bot(token=None, test=None):
    """
    This function addresses the rest API request for adding a new bot.
    :param token: Token for the new bot.
    :param test: (Integer) <=0 shows that token is for a live bot, > 0 shows
    it is a test bot.
    :return:
    """
    if token is None or test is None:
        # Invalid token provided.
        botapi_logger.warn('add_bot api call invoked without any token.')
        return bad_request(message="No token/test provided to add new bot.")
    try:
        if token.isdigit():
            botapi_logger.critical('Integer string provided as token:{tokn} '
                                   'for with add_bot api call.'.format(
                                                            tokn=token))
            raise AttributeError
        else:
            bot_token = token.encode('utf-8')
        testing = True if test is not None and test > 0 else False
        # Add new bot.
        status = procedures.add_bot(token=bot_token, testing=testing)
        if status[1]:
            # New bot successfully started.
            botapi_logger.info('Successfully added new bot:{uname} and '
                               'started polling in add_bot api call.'.format(
                                                            uname=status[0]))
            return jsonify({
                "status": "success",
                "message": "Bot:{name} successfully added to database "
                           "and started polling.".format(name=status[0])
            }), 201
        else:
            # New bot added but did not start polling.
            botapi_logger.info('Successfully added new bot:{uname} and did not'
                               'start polling in add_bot api call.'.format(
                                                            uname=status[0]))
            return jsonify({
                "status": "ok",
                "message": "Bot:{name} successfully added to database "
                           "but could not start polling.".format(name=status[0])
            }), 201
    except ValueError as e:
        botapi_logger.error('Unable to entertain add_bot api for token:{'
                            'tokn}. Reason:{reason}'.format(tokn=token,
                                                            reason=e.message))
        return bad_request(message="Unable to add Bot. Reason:{reason}".format(
                reason=e.message))
    except AttributeError:
        botapi_logger.error('Bad token:{tokn} provided with add_bot api call.'
                            ''.format(tokn=token))
        return bad_request(message="String expected for token in URL. Integer "
                                   "provided.")


@botapi.route('/startbot/<int:botid>/<username>', methods=['PUT'])
def start_bot(botid=0, username='#'):
    """
    This function addresses the Rest API call to start polling for an already
    present bot in the database.
    :param botid: ID (positive integer) for the bot which should start polling.
    :param username: Username of bot which should start polling. #: wildcard
    :return:
    """
    try:
        bot_id = botid if int(botid) > 0 else None
        bot_username = username.encode('utf-8')     # Both wildcard inputs.
        if bot_id is None and bot_username == '#':
            botapi_logger.warn('start_bot api call invoked without any botid,'
                               'username.')
            raise ValueError
        elif bot_username.isdigit():
            botapi_logger.error('Integer only username:{uname} provided with '
                                'start_bot api call.'.format(uname=username))
            return bad_request(
                message="Please provide valid username (string expected) in "
                        "query string.")

        # Start the bot.
        status = procedures.start_bot(botid=bot_id, username=bot_username)
        if status == -1:
            # Bot not found in DB.
            botapi_logger.error('Unable to find a bot to start_bot with given '
                                'id:{bid} or username={uname}'.format(
                                bid=botid, uname=username))
            return bad_request(
                message="Unable to find bot {name} in database.".format(
                    name=bot_username if bot_username != '#' else bot_id))
        elif status == 1:
            # Bot started polling successfully.
            botapi_logger.info('Successfully started polling for bot with '
                               'id:{bid} or username={uname} with start_bot '
                               'api call.'.format(bid=bot_id, uname=username))
            return jsonify({
                "result": "success",
                "message": "Polling started for bot {name}".format(
                    name=bot_username if bot_username != '#' else bot_id)
            }), 200
        elif status == 0:
            # Bot could not start polling successfully.
            botapi_logger.error('Failed to start polling for bot with '
                                'id:{bid} or username={uname} with start_bot '
                                'api call.'.format(bid=bot_id, uname=username))
            return jsonify({
                "result": "failure",
                "message": "Unable to start bot{name}".format(
                    name=bot_username if bot_username != '#' else bot_id)
            }), 304             # HTTP Response code: 304 (Un modified)
        elif status == -2:
            botapi_logger.info('Cannot start polling for test-bot with '
                               'id:{bid} or username={uname} with start_bot '
                               'api call.'.format(bid=bot_id, uname=username))
            return bad_request(
                message="Testbot bot:{name} can not start polling".format(
                    name=bot_username if bot_username != '#' else bot_id))
    except ValueError:
        botapi_logger.info('id:{bid} or username={uname} provided with start_'
                           'bot api call.'.format(bid=bot_id, uname=username))
        return bad_request(
            message="Please provide valid Bot id (positive integer expected) or"
                    " valid bot username (string expected) in request.")


@botapi.route('/stopbot/<int:botid>/<username>', methods=['PUT'])
def stop_bot(botid=0, username=None):
    """
    This function addresses RestAPI call to stop polling for a bot already
    registered in database.
    :param botid: Token for the bot which should start polling.
    :param username: Username of bot which should start polling. #: wildcard
    :return:
    """
    try:
        bot_id = botid if int(botid) > 0 else None
        bot_username = username.encode('utf-8')  # Both wildcard inputs.
        if bot_id is None and bot_username == '#':
            botapi_logger.warn('stop_bot api call invoked without any botid,'
                               'username.')
            raise ValueError
        elif bot_username.isdigit():
            botapi_logger.error('Integer only username:{uname} provided with '
                                'stop_bot api call.'.format(uname=username))
            return bad_request(
                message="Please provide valid username (string expected) in "
                        "query string.")
        # Stop the bot
        status = procedures.stop_bot(botid=bot_id, username=bot_username)
        if status == -1:
            # Bot not found
            botapi_logger.error('Unable to find a bot to stop_bot with given '
                                'id:{bid} or username={uname}'.format(
                                                bid=botid, uname=username))
            return bad_request(
                message="Unable to find bot {name} in database.".format(
                    name=bot_username if bot_username != '#' else bot_id))
        elif status == 1:
            # Bot stopped polling successfully.
            botapi_logger.info('Successfully stopped polling for bot with '
                               'id:{bid} or username={uname} with start_bot '
                               'api call.'.format(bid=bot_id, uname=username))
            return jsonify({
                "result": "success",
                "message": "Successfully stopped bot {name} from polling"
                .format(name=bot_username if bot_username != '#' else bot_id)
            }), 200
        elif status == 0:
            # Bot could not stop polling.
            botapi_logger.error('Failed to stop polling for bot with '
                                'id:{bid} or username={uname} with start_bot '
                                'api call.'.format(bid=bot_id, uname=username))
            return jsonify({
                "result": "failure",
                "message": "Unable to stop bot{name} from polling".format(
                    name=bot_username if bot_username != '#' else bot_id)
            }), 304
        elif status == -2:
            botapi_logger.info('Cannot stop polling for test-bot with '
                               'id:{bid} or username={uname} with start_bot '
                               'api call.'.format(bid=bot_id,
                                                  uname=username))
            return bad_request(
                message="Bot {name} has never started for polling.".format(
                    name=bot_username if bot_username != '#' else bot_id))
    except ValueError:
        botapi_logger.info('id:{bid} or username={uname} provided with stop_'
                           'bot api call.'.format(bid=bot_id, uname=username))
        return bad_request(
            message="Please provide valid Bot id (positive integer expected) or"
                    " valid bot username (string expected) in request.")


@botapi.route('/startall', methods=['PUT'])
def start_all_bots():
    bots_started = procedures.start_all()       # Start all bots
    botapi_logger.info('Successfully started {count} bots for polling in '
                       'start_all api call.'.format(count=len(bots_started)))
    return jsonify({
        "result": "ok",
        "message": "Successfully started {count} bots.".format(
            count=len(bots_started)),
        "ids": [bot_id for bot_id in bots_started]
    }), 200


@botapi.route('/stopall', methods=['PUT'])
def stop_all_bots():
    """
    This function address RestAPI call to stop polling for all bots which
    have ever started polling.
    :return:
    """
    bots_stopped = procedures.stop_all()        # Stop all bots.
    botapi_logger.info('Successfully stopped {count} bots for polling in '
                       'start_all api call.'.format(count=len(bots_stopped)))
    if bots_stopped > 0:
        return jsonify({
            "result": "success",
            "message": "Successfully stopped {count} previously running "
                       "bots.".format(count=len(bots_stopped)),
            "ids": [bot_id for bot_id in bots_stopped]
        }), 200
    else:
        return internal_server_error(
            message="No to stop previously running bots.")


@botapi.route('/<bot_id>/getBotMessages', methods=['GET'])
def filter_messages_by_bot(bot_id=0):
    """
    This call addresses RestAPI call to return all messages logged by given bot.
    :param bot_id: Bot ID for Bot whose logged messages are requested.
    :return:
    """
    # Get messages
    msgs = Message.objects(bot_id=bot_id).all().order_by('-date')
    botapi_logger.info('Successfully returned {count} messages logged by {bid}'
                       'filter_messages_by_botid api call.'.format(
                        count=len(msgs), bid=bot_id))
    if msgs is not None:
        return jsonify({
            "result": "success",
            "messages": [msg.to_json() for msg in msgs] if len(msgs) > 0 else []
        }), 200


@botapi.route('/<username>/getUserMessages', methods=['GET'])
def filter_messages_by_username(username):
    """
    This call addresses RestAPI call to return all messages logged from by
    requested username.
    :param username: Sender's username.
    :return:
    """
    # Get messages
    msgs = Message.objects(sender_username__iexact=username)\
                  .all().order_by('-date')
    botapi_logger.info('Successfully returned {count} messages sent by {uname}'
                       'filter_messages_by_username api call.'.format(
                        count=len(msgs), uname=username))
    if msgs is not None:
        return jsonify({
            "result": "success",
            "messages": [msg.to_json() for msg in msgs] if len(msgs) > 0 else []
        }), 200


@botapi.route('/<chatid>/getMessages', methods=['GET'])
def filter_messages_by_chatid(chatid):
    """
    This call addresses RestAPI call to return all messages logged for a
    given chat.
    :param chatid: Telegram chat id for the chat in question.
    :return:
    """
    # Get messages
    msgs = Message.objects(chatid=chatid).all().order_by('-date')
    botapi_logger.info('Successfully returned {count} messages logged in chat:'
                       '{chatid} filter_messages_by_chatid api call.'.format(
                        count=len(msgs), chatid=chatid))
    if msgs is not None:
        return jsonify({
            "result": "success",
            "messages": [msg.to_json() for msg in msgs] if len(msgs) > 0 else []
        }), 200


@botapi.route(
    '/filterMessages/<int:botid>/<int:time_off>/<text>/<username>/<name>',
    methods=['GET'])
def filter_messages(botid, time_off, text, username, name):
    """
    This function filters the logged messages based on given criteria.
    :param time_off: Time (in minutes) for filtering messages by date.
    :param botid: ID of bot from which message was received.
    :param text: Message text (partially matched.)
    :param username: Senders username (exactly matched.)
    :param name: Sender's firstname or lastname (partially matched.)
    :return:
    """
    # Resolve wildcards
    username = username
    botid = botid if botid > 0 else None
    text = text
    name = name
    # Get filtered messages.
    msgs = procedures.filter_messages(time_min=time_off, botid=botid,
                                      text=text, username=username, name=name)
    return jsonify({
        "result": "success",
        "messages": [msg.to_json() for msg in msgs] if len(msgs) > 0 else []
    }), 200


@botapi.route('/do_not_use/delete_all_bots', methods=['DELETE'])
def delete_all_bots():
    """
    This function deletes all (test+non-test) bots from the database.
    :return:
    """
    deleted = MyBot.objects.delete()
    botapi_logger.info('Successfully deleted {count} bots for delete_all_bots '
                       'api call'.format(count=deleted))
    return jsonify({
        "status": "success",
        "message": "{count} bots deleted successfully from database.".format(
            count=deleted)
    }), 200


@botapi.route('/do_not_use/delete_all_messages', methods=['DELETE'])
def delete_all_messages():
    """
    This function generates all the messages logged in the database.
    :return:
    """
    deleted = Message.objects.delete()
    botapi_logger.info('Successfully deleted {count} messages for '
                       'delete_all_messages api call'.format(count=deleted))
    return jsonify({
        "status": "success",
        "message": "{count} logged messages removed successfully from "
                   "database.".format(count=deleted)
    }), 200


@botapi.route('/private/gen_dummy_bots/<int:count>', methods=['POST'])
def gen_dummy_bots(count):
    """
    This function generates test dummy bots. To be used for testing purpose.
    :param count: Number of bots to be generated.
    :return:
    """
    MyBot.generate_fake(entries=count)      # Generate dummy bots.
    botapi_logger.info('Successfully generated {count} dummy bots for '
                       'gen_dummy_bots api call'.format(count=count))
    return jsonify({
        "status": "success",
        "message": "{count} dummy bots generated successfully".format(
            count=count)
    }), 200


@botapi.route('/private/gen_dummy_messages/<int:count>', methods=['POST'])
def gen_dummy_msgs(count=100):
    """
    This function generates dummy messages for the bots registered in the
    database. To be used for testing only.
    :param count: number of dummy messages to be generated.
    :return:
    """
    Message.generate_fake(entries=count)            # Generate dummy messages.
    botapi_logger.info('Successfully generated {count} dummy messages for '
                       'gen_dummy_msgs api call'.format(count=count))
    return jsonify({
        "status": "success",
        "message": "{count} dummy logged messages generated "
                   "successfully".format(count=count)
    }), 200


@botapi.route('/remove_bot_id_cascade/<int:botid>', methods=['DELETE'])
def delete_bot_and_message_by_id(botid):
    """
    This function deletes the bot registered with given ID and removes all
    messages logged by that bot.
    :param botid: ID of the bot which needs to be removed.
    :return:
    """
    bot = MyBot.objects(bot_id=botid).first()
    if bot:
        bot.delete()
        messages = Message.objects(bot_id=botid).delete()
        botapi_logger.info('Successfully deleted bot:{uname} and {count} '
                           'messages logged by it, via delete_bot_and_message'
                           '_by_id api call'.format(uname=bot.username,
                                                    count=messages))
        return jsonify({
            'status': 'success',
            'message': 'Bot:{uname} and {msgs} logged messages removed'.format(
                uname=bot.username, msgs=messages)
        }), 200
    else:
        botapi_logger.warn('delete_bot_and_message_by_id api call to delete '
                           'non existing bot with id:{bid}'.format(bid=botid))
        return bad_request(message='No bot registered for ID:{botid}'.format(
            botid=botid))


@botapi.route('/remove_bot_id/<int:botid>', methods=['DELETE'])
def delete_only_bot_by_id(botid):
    """
    This function deletes the bot registered with given ID .
    :param botid: ID of the bot which needs to be removed.
    :return:
    """
    bot = MyBot.objects(bot_id=botid).first()
    if bot:
        bot.delete()
        botapi_logger.info('Successfully deleted bot:{uname} by '
                           'delete_only_bot_by_id api call'.format(
                                                uname=bot.username))
        return jsonify({
            'status': 'success',
            'message': 'Bot:{uname} registered with ID: {botid} removed'.format(
                uname=bot.username, botid=botid)
        }), 200
    else:
        botapi_logger.warn('delete_only_bot_by_id api call to delete '
                           'non existing bot with id:{bid}'.format(bid=botid))
        return bad_request(message='No bot registered for ID:{botid}'.format(
            botid=botid))


@botapi.route('/remove_bot_uname_cascade/<username>', methods=['DELETE'])
def delete_bot_and_message_by_uname(username):
    """
    This function deletes the bot registered with given username and removes all
    messages logged by that bot.
    :param username: Username of the bot which needs to be removed.
    :return:
    """
    bot = MyBot.objects(username=username).first()
    if bot:
        bot.delete()
        messages = Message.objects(bot_id=bot.bot_id).delete()
        botapi_logger.info('Successfully deleted bot:{uname} and {count} '
                           'messages logged by it, via delete_bot_and_message_'
                           '_by_uname api call'.format(uname=bot.username,
                                                       count=messages))
        return jsonify({
            'status': 'success',
            'message': 'Bot:{username} and {msgs} logged messages '
                       'removed'.format(username=bot.username, msgs=messages)
        }), 200
    else:
        botapi_logger.warn('delete_bot_and_message_by_uname api call to delete '
                           'non existing bot with id:{uname}'.format(
                                                            uname=username))
        return bad_request(message='No bot registered with username:'
                                   '{uname}'.format(uname=username))


@botapi.route('/remove_bot_id/<username>', methods=['DELETE'])
def delete_only_bot_by_uname(username):
    """
    This function deletes the bot registered with given ID .
    :param username: Username of the bot which needs to be removed.
    :return:
    """
    bot = MyBot.objects(username=username).first()
    if bot:
        bot.delete()
        botapi_logger.info('Successfully deleted bot:{uname} by '
                           'delete_only_bot_by_uname api call'.format(
                                                    uname=bot.username))
        return jsonify({
            'status': 'success',
            'message': 'Bot:{uname} successfully removed'.format(uname=username)
        }), 200
    else:
        botapi_logger.warn('delete_only_bot_by_uname api call to delete '
                           'non existing bot with id:{uname}'.format(
                                                            uname=username))
        return bad_request(message='No bot registered for username:'
                                   '{uname}'.format(uname=username))
