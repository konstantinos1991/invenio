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
from invenio.ext.restful import require_api_auth, require_header,\
    UTCISODateTime
from flask.ext.restful import fields, marshal
from flask.ext.login import current_user
from dateutil import parser
from dateutil.tz import tzlocal
from functools import wraps
#from flask import jsonify
from flask import request
from invenio.modules.messages.config import \
    CFG_WEBMESSAGE_STATUS_CODE
from invenio.modules.messages import api as messagesAPI
from invenio.modules.messages.errors import InvenioWebMessageError, MessageNotFoundError, MessageNotDeletedError, \
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
        except MessageNotFoundError as e:
            abort(404, message=str(e), status=404)
        except MessageNotDeletedError as e:
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
    def __init__(self, givenMessage):
        """ Initialize a message object

        :param message: is a message of type MsgMESSAGE or UserMSgMESSAGE
        """
        #import needed models
        from invenio.modules.messages.models import MsgMESSAGE
        #set the marshaling fields
        self.marshal_message_fields = dict(
            id=fields.Integer,
            id_user_from=fields.Integer,
            nickname_user_from=fields.String,
            sent_to_user_nicks=fields.String,
            sent_to_group_names=fields.String,
            subject=fields.String,
            body=fields.String,
            sent_date=UTCISODateTime,
            received_date=UTCISODateTime,
            status=fields.String
        )
        #parse the attributes of the given message
        # import ipdb;
        # ipdb.set_trace();

        if isinstance(givenMessage, MsgMESSAGE):
            self.id = givenMessage.id
            self.id_user_from = givenMessage.id_user_from
            self.nickname_user_from = givenMessage.user_from.nickname
            self.sent_to_user_nicks = givenMessage._sent_to_user_nicks
            self.sent_to_group_names = givenMessage._sent_to_group_names
            self.subject = givenMessage.subject
            self.body = givenMessage.body
            self.sent_date = givenMessage.sent_date
            self.received_date = givenMessage.received_date
            self.status = CFG_WEBMESSAGE_STATUS_CODE['NEW']
        else:   # givenMessage is of type UserMsgMESSAGE
            self.id = givenMessage.id_msgMESSAGE
            self.id_user_from = givenMessage.message.id_user_from
            self.nickname_user_from = givenMessage.message.user_from.nickname
            self.sent_to_user_nicks = givenMessage.message._sent_to_user_nicks
            self.sent_to_group_names = givenMessage.message._sent_to_group_names
            self.subject = givenMessage.message.subject
            self.body = givenMessage.message.body
            self.sent_date = givenMessage.message.sent_date
            self.received_date = givenMessage.message.received_date
            self.status = givenMessage.status

    def marshal(self):
        """ Packages the object to a dictionary(JSON) """
        return marshal(self, self.marshal_message_fields)


#schema to be validated for POST in MessagesListResource
create_message_post_schema = dict(
    users_nicknames_to=dict(type="string"),
    groups_names_to=dict(type="string"),
    subject=dict(type="string"),
    body=dict(type="string"),
    sent_date=dict(type="string"),
)

#data schema when replying to a message
reply_to_sender_put_schema = dict(
    reply_body=dict(type="string"),
)


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
        message_object = MessageObject(requested_message)
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

    @require_header('Content-Type', 'application/json')
    def put(self, oauth, message_id):
        """Replies to a message

        First it accepts the body that will be added to the body
        of the old message
        :param message_id: the id of the message to reply to
        Returns:
                the new message that was created
        """
        # initialize a Validator
        replyToMessageValidator = Validator(reply_to_sender_put_schema)
        #get the uploaded JSON data
        json_data = request.get_json()
        #validate JSON data
        if replyToMessageValidator.validate(json_data) is False:
            abort(400,
                  message="Validation failed",
                  status=400,
                  errors=replyToMessageValidator.errors)
        #get the user id
        uid = int(current_user.get_id())
        #get the message id to reply to
        msg_id = int(message_id)
        #the body of the niew message
        reply_body = json_data['reply_body']
        #sends the reply
        new_message_id = messagesAPI.reply_to_sender(msg_id=msg_id,
                                                     reply_body=reply_body, uid=uid)
        #get the newly created message
        new_message = messagesAPI.get_message(new_message_id)
        #create a MessageObject to return
        message_object = MessageObject(new_message)
        return message_object.marshal(), 201

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
        user_messages_list = []     # a list that will hold the representations of the messages, i.e a list of MessageObject
        user_messages = messagesAPI.get_all_messages_for_user(uid)
        for m in user_messages:
            message_object = MessageObject(m)
            user_messages_list.append(message_object)
        return map(lambda o: o.marshal(), user_messages_list)

    def delete(self, oauth):
        """Deletes all messages of a user(except the reminders)

        Returns:
            a dictionary containing the number of the deleted messages
        """
        uid = current_user.get_id()
        messagesAPI.delete_all_messages(uid)
        return "", 204

    @require_header('Content-Type', 'application/json')
    def post(self, oauth):
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

        uid = int(uid)
        users_nicknames_to_str = json_data['users_nicknames_to']
        groups_names_to_str = json_data['groups_names_to']
        subject_str = json_data['subject']
        body_str = json_data['body']
        given_datetime_utc_iso_str = json_data['sent_date']
        #convert the given date-time utc-iso string to a datetime object
        dt = parser.parse(given_datetime_utc_iso_str)
        if dt.tzinfo:
            dt = dt.astimezone(tzlocal())
        dt = dt.replace(tzinfo=None)

        created_message_id = \
            messagesAPI.create_message(uid_from=uid,
                                       users_to_str=users_nicknames_to_str,
                                       groups_to_str=groups_names_to_str,
                                       msg_subject=subject_str,
                                       msg_body=body_str,
                                       msg_send_on_date=dt)

        created_message = messagesAPI.get_message(created_message_id)
        message_object = MessageObject(created_message)
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


def setup_app(app, api):
    api.add_resource(
        MessageResource,
        '/api/messages/<int:message_id>',
    )
    api.add_resource(
        MessagesListResource,
        '/api/messages/'
    )
