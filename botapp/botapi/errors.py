"""
This module lists the blueprints for returning errors in JSON format.
"""
from flask import jsonify, request
from botapp.exceptions import ValidationError
from . import botapi


@botapi.app_errorhandler(404)           # API level handler.
def resource_not_found(message=None):
    response = jsonify({
            'error': 'not found',
            'message': 'resource not found',
    })
    response.status_code = 404
    return response


def not_found(message="Requested resource not found"):
    """
    Generates json response for requests for a resource not found.
    :param message: error message sent to the user.
    :return: json response, HTTP status code: 404
    """
    response = jsonify({'error': 'not_found',
                        'message': message})
    response.status_code = 404
    return response


def bad_request(message):
    """
    Return bad request JSON response to user.
    :param message: Message provided in response.
    :return:
    """
    response = jsonify({
        'error': 'bad request',
        'message': message
    })
    response.status_code = 400
    return response


@botapi.app_errorhandler(500)
def internal_server_error(message):
    """
    Return internal server error JSON response to user.
    :param message: Message provided in response.
    :return:
    """
    response = jsonify({
        'error': 'interal server error',
        'message': message
    })
    response.status_code = 500
    return response


@botapi.errorhandler(ValidationError)
def validation_error(e):
    return bad_request(e.args[0])
