"""
Main module for managing Telegram application.
"""
import sys
import logging
from botapp import create_app, db
from botapp.models import MyBot, Message
from flask_script import Manager, Shell
from telegram.error import NetworkError

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - '
                           '%(levelname)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.INFO)

try:
    app = create_app('default')
except NetworkError:
    logger.error('Network error while communicating with Telegram API, please '
                 'try again.')
    sys.exit(-1)
manager = Manager(app)


def make_shell_context():
    """
    Make context for Shell.
    :return: Application models, database and application object.
    """
    return dict(app=app, MyBot=MyBot, Message=Message, db=db)

manager.add_command("shell", Shell(make_context=make_shell_context))


@manager.command
def test(coverage=False, test_name=None):
    """
    Run unit tests
    :param coverage: Enable coverage
    :return test_name: Name of the tests to be run.
    """
    import unittest
    if test_name is None:
        logger.info('Running all testcases.')
        tests = unittest.TestLoader().discover('tests')
    else:
        logger.info('Running test cases for module:{module}'.format(
            module=test_name))
        tests = unittest.TestLoader().loadTestsFromName('tests.'+test_name)

    # Run test
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def secureserver():
    """
    Start secure server with self-signed Certificates. It will give a
    untrusted connection warning on web browsers. To avoid the warning,
    please use CA signed certificates.
    :return:
    """
    context = ('server.crt', 'server.key')
    app.run(ssl_context=context, threaded=True, debug=True)


if __name__ == '__main__':
    manager.run()
