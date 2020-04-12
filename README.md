# README #

Please read setup-guidelines for more info.

### What is this repository for? ###

* Quick summary
An application for logging messages via Telegram Bots and allowing user to filter through these messages via RestAPI or Web interface.
* Version
0.1


### How do I get set up? ###

* Summary of set up
* Configuration
* Dependencies

pip install -r requirements.txt

* Database configuration

MongoDB @ 127.0.0.1:27017 required. The configuration can be updated in config.json.

* How to run tests
python manage.py test

Run individual Tests using
python manage.py test -t test_module_name

Note: Web UI test cases use selenium==2.53.6 which is compatible with FireFox 46.0. Therefore the test case for Web UI are disabled. Please rename tests/atest_web_ui to tests/test_web_ui

* Deployment instructions
HTTP server: python manage.py runserver
HTTPS server: python manager.py secureserver

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact
