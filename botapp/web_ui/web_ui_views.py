"""
Module containing view functions for WEB interfaces.
"""

import time
from flask import flash, redirect, url_for, abort
from flask import render_template, request, current_app
from botapp.api_helpers import procedures
from botapp.web_ui.forms import FilteringForm, AddBotForm, GetBot, \
    FilterCriteria, EditBot
from botapp.web_ui import web_ui, web_logger
from botapp.models import MyBot, Message


@web_ui.route('/shutdown')
def server_shutdown():
    """
    Shutdown application server.
    :return:
    """
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting down...'


@web_ui.route('/index', methods=['GET', 'POST'])
def index():
    """
    This function renders the Index page for application. It shows list of all
    messages logged by all bots and also provides a form for filtered
    messages. Upon filtering, it redirects to a page showing filtered messages.
    :return: ../index
    """
    # get all messages.
    page = request.args.get('page', 1, type=int)
    pagination = procedures.filter_messages(time_min=int(time.time())/60)\
        .paginate(page, per_page=current_app.config['MESSAGES_PER_PAGE'],
                  error_out=False)
    msgs = pagination.items
    web_logger.info('index page displayed with {count} messages.'.format(
        count=len(msgs)))
    return render_template('index.html', messages=msgs,
                           pagination=pagination)


@web_ui.route('/filter', methods=['GET', 'POST'])
def filtering():
    """
    This function displays the form for getting filtering criteria from the user
     and redirects user  to the page containing filtered messages.
    :return: ../filtered_messages
    """
    form = FilteringForm(time_int_field='',
                         text_field='',
                         fn_ln_field='',
                         bot_field=0,
                         time_field=0,
                         username_field='')
    # Populate form fields initially.
    form.bot_field.choices = [(0, 'Select an option')] + list(
        MyBot.objects().all().values_list('bot_id', 'username'))
    form.username_field.choices = \
        [('#', 'Select')] + \
        list(Message.objects(sender_username__nin=['unknown', ''])
             .values_list('sender_username', 'sender_username'))

    if form.validate_on_submit():
        # Get filtering criteria from the submitted form.
        try:
            if int(form.time_field.data) > 0:
                time_offset = form.time_field.data
            elif int(form.time_int_field.data) > 0:
                time_offset = form.time_int_field.data
            else:
                time_offset = int(time.time()) / 60
            # Redirect to page showing filtered message.
            web_logger.info('User redirected to filtered messages page with '
                            'given criteria: botid:{bid},time_off:{tim},'
                            'text:{txt},username:{uname},name:{name}'.format(
                                                bid=form.bot_field.data,
                                                tim=time_offset,
                                                txt=form.text_field.data,
                                                uname=form.username_field.data,
                                                name=form.fn_ln_field.data))
            return redirect(url_for(
                '.filtered_messages',
                botid=int(form.bot_field.data)
                if form.bot_field.data != '' else '#',
                time_off=time_offset,
                text=form.text_field.data
                if form.text_field.data != '' else '#',
                username=form.username_field.data,
                name=form.fn_ln_field.data
                if form.fn_ln_field.data != '' else '#'
            ))
        except Exception as e:
            web_logger.error('Error:{msg} during redirecting user to filtered'
                             ' messages page.'.format(msg=e.message))
            return render_template('500.html', error_message=e.message)

    return render_template('filtering.html', form=form)


@web_ui.route('/filtered/<int:botid>/<int:time_off>/<text>/<username>/<name>')
def filtered_messages(botid, time_off, text, username, name):
    """
    This function renders the filtered messages page based on the criteria
    chosen in index page.
    :param botid: ID of telegram.bot
    :param time_off: Time offset (in minutes).
    :param text: Message text (partially matched).
    :param username: Sender username (exactly matched).
    :param name: Sender firstname/lastname (partially matched).
    :return: .../filtered/botid/time_off/text/username/name
    """
    # Resolve wildcards
    username_field = username if username != '#' else '#'
    botid = botid if botid != -1 else None
    text = text
    name = name
    # Filter messages
    msgs = procedures.filter_messages(username=username_field, botid=botid,
                                      time_min=time_off, text=text,
                                      name=name)
    fc = FilterCriteria(botid=botid, time_off=time_off, text=text, name=name,
                        username=username_field)

    # get filtered messages.
    page = request.args.get('page', 1, type=int)
    pagination = msgs.paginate(page, error_out=False,
                               per_page=current_app.config['MESSAGES_PER_PAGE'])

    msgs = pagination.items
    return render_template('filtered_msgs.html', criteria=fc, messages=msgs,
                           pagination=pagination)


@web_ui.route('/addbot', methods=['GET', 'POST'])
def add_bot():
    """
    This function renders the add_bot form where user can add a new bot to
    database by providing token for the bot.
    :return: .../addbot
    """
    form = AddBotForm()
    if form.validate_on_submit():
        bot = MyBot.objects(token=form.token.data).first()
        if bot is not None:         # Duplicate token user for adding bot.
            flash('Another bot Bot:{username} is already registered with '
                  'given token.'.format(username=bot.username))
            # Redirect user to Bot's homepage.
            return redirect(url_for('web_ui.bot_info', botid=bot.bot_id))
        if form.is_test_bot.data:
            # if requested token is for a testbot.
            status = procedures.add_bot(token=form.token.data, testing=True)
            web_logger.info('New testbot bot:{uname} added by web api.'.format(
                uname=status[0]))
            flash('Testbot Bot:{username} successfully added to '
                  'database.'.format(username=status[0]))
            return redirect(
                url_for('web_ui.bot_info',
                        botid=MyBot.objects(username__iexact=status[
                            0]).first().bot_id))
        else:
            try:
                # Add the bot.
                status = procedures.add_bot(token=form.token.data,
                                            testing=False)
                # Redirect to bot info page.
                if status[1]:
                    web_logger.info('New live bot:{uname} added by web api and '
                                    'started polling.'.format(uname=status[0]))
                    flash('New bot:{username} successfully added and '
                          'started polling.'.format(username=status[0]))
                    return redirect(
                        url_for('web_ui.bot_info',
                                botid=MyBot.objects(username__iexact=status[
                                    0]).first().bot_id))
                else:
                    # Redirect to Edit bot page to start polling again.
                    web_logger.info('New live bot:{uname} added by web api and '
                                    'did not start polling.'.format(
                                                        uname=status[0]))
                    flash('New bot:{username} successfully added but '
                          'did not start polling.'.format(username=status[0]))
                    return redirect(
                        url_for('web_ui.edit_bot',
                                bot_choice=MyBot.objects(
                                    username__iexact=status[0]).first().bot_id))

            except Exception as e:
                web_logger.error('Error:{msg} during adding new bot.'.format(
                    msg=e.message))
                return render_template('500.html', error_message=e.message)
    return render_template('add_bot.html', form=form)


@web_ui.route('/bot_info/<int:botid>', methods=['GET'])
def bot_info(botid):
    """
    This function renders the page showing bot information including
    username, token, ID and messages logged by the bot.
    :param botid: ID of the bot whose information is requested.
    :return: .../bot_info
    """
    page = request.args.get('page', 1, type=int)
    bot = MyBot.objects(bot_id=botid).first()
    if bot is None:
        # Requested bot not found, redirect to selection page for choosing
        # another bot.
        web_logger.warn('Web request to get bot info with ID:{bid} which does '
                        'not exist in database.'.format(bid=botid))
        flash('Requested bot with ID:{bid} does not exist in the '
              'database.'.format(bid=botid))
        return redirect(url_for('.get_bot_info', bot_choice=0))
    msgs = procedures.filter_messages(botid=botid)
    pagination = msgs.paginate(page, error_out=False,
                               per_page=current_app.config['MESSAGES_PER_PAGE'])
    return render_template('botinfo.html', bot=bot, messages=pagination.items,
                           pagination=pagination)


@web_ui.route('/getbotinfo', methods=['GET', 'POST'])
def get_bot_info(bot_choice=0):
    """
    This function renders the page showing a DropDown field listing all Bots
    in the database. Upon selection the user is redirected to bot's own
    information page.
    :param bot_choice: initial choice for the bot (default=0, no choice)
    :return: .../getbotinfo
    """
    form = GetBot(choose_bot=bot_choice)
    # Populate the initial set of choices for Bot DropDownList.
    form.choose_bot.choices = [('#', 'Select')] + \
                              list(MyBot.objects().values_list(
                                  'username', 'username'))

    if form.validate_on_submit():
        # Redirect to bot_info page.
        bot = MyBot.objects(username__iexact=form.choose_bot.data).first()
        if bot is not None:
            web_logger.info('Successfully redirected user to bot_info page '
                            'for bot:{uname}'.format(uname=bot.username))
            return redirect(url_for('.bot_info', page=1,
                                    botid=bot.bot_id))
        else:
            web_logger.info('Web request to get info for a non existing bot '
                            'with ID:{bid}'.format(bid=form.choose_bot.data))
            return render_template('404.html', message='Invalid bot ID used.')

    return render_template('get_bot_info.html', form=form)


@web_ui.route('/editbot', methods=['GET', 'POST'])
def edit_bot(bot_choice=0):
    """
    This function renders the page for Editing the bot. Editing the bot
    allows to enable/disable polling of the bot.
    :param bot_choice: Initial choice for selected bot.
    :return: .../editbot
    """
    form = EditBot(choose_bot=bot_choice,
                   toggle='Toggle (Enable/Disable)')

    # Populate the initial set of choices for Bot DropDownList.
    form.choose_bot.choices = [(0, 'Select')] + \
                              list(MyBot.objects().values_list(
                                  'username', 'username'))

    if form.validate_on_submit():
        # Get list of bots
        bot = MyBot.objects(username__iexact=form.choose_bot.data).first()
        if bot is None:
            # Redirect to same page because no option selected.
            flash('Please select an option and then press submit.')
            return render_template('edit_bot.html', form=form)
        if bot.test_bot:
            # Redirect to same page because testbot cannot be started.
            web_logger.info('Attempt to start polling for a test bot bot:'
                            '{uname} via web api.'.format(uname=bot.username))
            flash('Testbot Bot:{username} attempt to start polling '
                  'failed.'.format(username=bot.username))
            form.status_field.data = 'Cannot be enabled.'
            return render_template('edit_bot.html', form=form)
        if not bot.state:
            # Bot is not polling currently, start polling.
            status = procedures.start_bot(botid=bot.bot_id,
                                          username=str(bot.username))
            if status == 1:
                web_logger.info('Bot:{uname} successfully started polling via '
                                'web api.'.format(uname=bot.username))
                flash('Bot:{username} successfully started polling.'.format(
                    username=bot.username))
                form.status_field.data = 'Enabled'
            elif status == 0:
                web_logger.info('Bot:{uname} could not start polling via '
                                'web api.'.format(uname=bot.username))
                flash('Failed to enable Bot:{username} for polling'.format(
                    username=bot.username))
                form.status_field.data = 'Failed to enable.'
                form.toggle = 'Enable'
        elif bot.state:
            # Bot is polling currently, stop polling.
            status = procedures.stop_bot(botid=bot.bot_id,
                                         username=str(bot.username))
            if status == 1:
                web_logger.info('Bot:{uname} successfully stopped polling via '
                                'web api.'.format(uname=bot.username))
                flash('Bot:{username} successfully stopped polling.'.format(
                    username=bot.username))
                form.status_field.data = 'Disabled'
            elif status == 0:
                web_logger.info('Bot:{uname} could not stop polling via '
                                'web api.'.format(uname=bot.username))
                flash('Failed to disable Bot:{username} for polling'.format(
                    username=bot.username))
                form.status_field.data = 'Failed to disable.'
        return render_template('edit_bot.html', form=form)
    # Responding to get Request
    return render_template('edit_bot.html', form=form)


@web_ui.route('/')
def root():
    """
    Redirect / to /index page.
    :return: .../index
    """
    return redirect(url_for('web_ui.index'))

