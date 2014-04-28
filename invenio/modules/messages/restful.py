# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
##
## Invenio is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## Invenio is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with Invenio; if not, write to the Free Software

"""
Restful api for the messages module.
"""

from flask.ext.restful import abort
from flask.ext.restful import Resource
from invenio.ext.restful import require_api_auth, require_header, UTCISODateTimeString
from flask.ext.restful import fields, marshal
from flask.ext.login import current_user
from functools import wraps
from flask import jsonify
from flask import request
from invenio.modules.messages.config import \
    CFG_WEBMESSAGE_STATUS_CODE
from invenio.modules.messages import api as messagesAPI
from invenio.modules.messages.errors import InvenioWebMessageError, MessageNotFound, MessageNotDeleted, \
    MessagesNotFetchedError, MessageNotCreatedError
#for marshaling the MessageObject
from cerberus import Validator


#Define the error handler
def error_handler(f):
    """
    Decorator to handle message exceptions
    """
    @wraps(f)
    def inner(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except MessageNotFound as e:
            abort(404, message=str(e), status=404)
        except MessageNotDeleted as e:
            abort(400, message=str(e), status=400)
        except MessagesNotFetchedError as e:
            abort(400, message=str(e), status=400)
        except MessageNotCreatedError as e:
            abort(400, message=str(e), status=400)
        except InvenioWebMessageError as e:
            if len(e.args) >= 1:
                abort(400, message=e.args[0], status=400)
            else:
                abort(500, message="Internal server error", status=500)
    return inner


class MessageObject(object):
    """A class that contains several informations about a message

    It will be used only to return informations back to the client and
    it has no interaction with the database
    """

    def __init__(self, id, id_user_from, nickname_user_from, sent_to_user_nicks, sent_to_group_names,
                 subject, body, sent_date, received_date, status):
        """Initialize a message object"""
        self.id = id
        self.id_user_from = id_user_from
        self.nickname_user_from = nickname_user_from
        self.sent_to_user_nicks = sent_to_user_nicks
        self.sent_to_group_names = sent_to_group_names
        self.subject = subject
        self.body = body
        self.send_date = sent_date
        self.received_date = received_date
        self.status = status
        #set the marshaling fields
        self.marshal_message_fields = dict(
            id=fields.Integer,
            id_user_from=fields.Integer,
            nickname_user_from=fields.String,
            sent_to_user_nicks=fields.String,
            sent_to_group_names=fields.String,
            subject=fields.String,
            body=fields.String,
            sent_date=fields.String,
            received_date=fields.String,
            status=fields.String
        )

    def marshal(self):
        """ Packages the object to a dictionary(JSON) """
        return marshal(self, self.marshaling_fields)


#schema to be validated for POST in MessagesListResource
create_message_post_schema = {
    'users_nicknames_to': {'type': 'string'},
    'groups_names_to': {'type': 'string'},
    'subject': {'type': 'string'},
    'body': {'type': 'string'},
    'sent_date': {'type': 'string'}
}


#The Resources
class MessageResource(Resource):

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    def get(self, oauth, message_id):
        """Returns a message in json format

        :param message_id: the id of the message to return
        Returns:
            a dictionary as JSON that contains all the information of a message
            a message is marshaled with the attributes id,id_user_from,nickname_user_from,
            sent_to_user_nicks,sent_to_group_names,subject,body,sent_date,received_date,
            status
        """
        uid = current_user.get_id()
        requested_message = messagesAPI.get_message_from_user_inbox(uid, message_id)
        #convert attributes to marshal the object correctly
        m_id = int(requested_message.message.id)
        id_user_from = int(requested_message.message.id_user_from)
        nickname_user_from = str(requested_message.message.user_from.nickname)
        sent_to_user_nicks = str(requested_message.message._sent_to_user_nicks)
        sent_to_group_names = str(requested_message.message._sent_to_group_names)
        subject = str(requested_message.message.subject)
        body = str(requested_message.message.body)
        status = str(requested_message.status)
        #convert the date-times to strings
        utc_iso_datetime_string = UTCISODateTimeString()
        sent_date = str(utc_iso_datetime_string.format(requested_message.message.sent_date))
        received_date = str(utc_iso_datetime_string.format(requested_message.message.received_date))
        #now create an instance of class MessageObject
        message_object = MessageObject(id=m_id, id_user_from=id_user_from,
                                       nickname_user_from=nickname_user_from,
                                       sent_to_user_nicks=sent_to_user_nicks,
                                       sent_to_group_names=sent_to_group_names,
                                       subject=subject, body=body,
                                       sent_date=sent_date, received_date=received_date,
                                       status=status)
        return message_object.marshal()

    def delete(self, oauth, message_id):
        """Deletes a message

        :param message_id: the id of the message to delete
        Returns:
            "" , 204 if the deletion of the message was successful
        """
        uid = current_user.get_id()
        messagesAPI.delete_message_from_user_inbox(uid, message_id)
        return "", 204

    def put(self, oauth, message_id):
        """Replies to a message

        First it accepts the body that will be added to the body
        of the old message
        :param message_id: the id of the message to reply to
        """
        pass

    def head(self, message_id):
        abort(405)

    def options(self, message_id):
        abort(405)

    def patch(self, message_id):
        abort(405)


class MessagesListResource(Resource):

    method_decorators = [
        require_api_auth(),
        error_handler
    ]

    def get(self, oauth):
        """Gets information about all messages of a user

        Returns:
            A dictionary is returned as JSON in format
            key:id_of_message as string , value:marshaled_message.
        """
        uid = current_user.get_id()
        return_dictionary = {}    # the dictionary that will contain the messages as dictionaries. the keys will be the message ids
        utc_iso_datetime_string = UTCISODateTimeString()
        user_messages = messagesAPI.get_all_messages_for_user(uid)
        for m in user_messages:
            message_object = MessageObject(id=int(m.id_msgMESSAGE),
                                           id_user_from=int(m.message.id_user_from),
                                           nickname_user_from=str(m.message.user_from.nickname),
                                           sent_to_user_nicks=str(m.message._sent_to_user_nicks),
                                           sent_to_group_names=str(m.message._sent_to_group_names),
                                           subject=str(m.message.subject),
                                           body=str(m.message.body),
                                           sent_date=str(utc_iso_datetime_string.format(m.message.sent_date)),
                                           received_date=str(utc_iso_datetime_string.format(m.message.received_date)),
                                           status=str(m.status))
            return_dictionary[str(m.id_msgMESSAGE)] = message_object.marshal()
            return jsonify(return_dictionary)

    def delete(self, oauth):
        """Deletes all messages of a user(except the reminders)

        Returns:
            a dictionary containing the number of the deleted messages
        """
        uid = current_user.get_id()
        messagesAPI.delete_all_messages(uid)
        # return_dictionary = {}
        # return_dictionary['number_of_deleted_messages'] = number_of_deleted_messages
        # return jsonify(return_dictionary)
        return "", 204

    @require_header('Content-Type', 'application/json')
    def post(self, oauth):
        ###IMPLEMENT ON MONDAY
        """Creates and sends a new message

        The request must have the following parameters
        users_nicknames_to
        groups_names_to
        subject
        body
        sent_date
        All the above arguments must be string values
        Returns:
            a dictionary as json in the same format when
            retrieving a message
        """
        uid = current_user.get_id()
        createMessageValidator = Validator(create_message_post_schema)
        json_data = request.get_json()

        if createMessageValidator.validate(json_data) is False:
            abort(400,
                  message="validation failed",
                  status=400,
                  errors=createMessageValidator.errors)

        created_message_id = \
            messagesAPI.create_message(uid_from=uid,
                                       users_to_str=json_data['users_nicknames_to'],
                                       groups_to_str=json_data['groups_names_to'],
                                       msg_subject=json_data['subject'],
                                       msg_body=json_data['body'],
                                       msg_send_on_date=json_data['sent_date'])
        created_message = messagesAPI.get_message(created_message_id)
        utc_iso_datetime_string = UTCISODateTimeString()
        message_object = MessageObject(id=int(created_message.id),
                                       id_user_from=int(created_message.id_user_from),
                                       nickname_user_from=str(created_message.user_from.nickname),
                                       sent_to_user_nicks=str(created_message._sent_to_user_nicks),
                                       sent_to_group_names=str(created_message._sent_to_group_names),
                                       subject=str(created_message.subject),
                                       body=str(created_message.body),
                                       sent_date=str(utc_iso_datetime_string.format(created_message.sent_date)),
                                       received_date=str(utc_iso_datetime_string.format(created_message.received_date)),
                                       status=str(CFG_WEBMESSAGE_STATUS_CODE['NEW']))
        return message_object.marshal(), 201

    def head(self, oauth):
        abort(405)

    def options(self, oauth):
        abort(405)

    def patch(self, oauth):
        abort(405)


# maybe set up here the API resource routing???

#
# Register API resources
#

#api = restful.Api(app=app)


def setup_app(app, api):
    api.add_resource(
        MessageResource,
        '/api/message/<int:message_id>',
    )
    api.add_resource(
        MessagesListResource,
        '/api/messages/'
    )