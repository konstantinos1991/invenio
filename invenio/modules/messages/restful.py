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
from invenio.ext.restful import require_api_auth, require_header
from flask.ext.restful import fields, marshal
from flask.ext.login import current_user
from datetime import datetime
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
        #convert attributes to marshal the object correctly
        m_id = int(requested_message.message.id)
        id_user_from = int(requested_message.message.id_user_from)
        nickname_user_from = str(requested_message.message.user_from.nickname.encode("utf-8"))
        sent_to_user_nicks = str(requested_message.message._sent_to_user_nicks.encode("utf-8"))
        sent_to_group_names = str(requested_message.message._sent_to_group_names.encode("utf-8"))
        subject = str(requested_message.message.subject.encode("utf-8"))
        body = str(requested_message.message.body.encode("utf-8"))
        status = str(requested_message.status)
        #convert the date-times to strings
        sent_date = str(requested_message.message.sent_date.strftime("%Y-%m-%d %H:%M:%S"))
        received_date = str(requested_message.message.received_date.strftime("%Y-%m-%d %H:%M:%S"))
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
        reply_body = str(json_data['reply_body'].encode("utf-8"))
        #sends the reply
        new_message_id = messagesAPI.reply_to_sender(msg_id=msg_id,
                                                     reply_body=reply_body, uid=uid)
        #get the newly created message
        new_message = messagesAPI.get_message(new_message_id)
        #create a MessageObject to return
        send_date_to_str = str(new_message.sent_date.strftime("%Y-%m-%d %H:%M:%S"))
        received_date_to_str = str(new_message.received_date.strftime("%Y-%m-%d %H:%M:%S"))
        message_object = MessageObject(id=int(new_message.id),
                                       id_user_from=int(new_message.id_user_from),
                                       nickname_user_from=str(new_message.user_from.nickname.encode("utf-8")),
                                       sent_to_user_nicks=str(new_message._sent_to_user_nicks.encode("utf-8")),
                                       sent_to_group_names=str(new_message._sent_to_group_names.encode("utf-8")),
                                       subject=str(new_message.subject.encode("utf-8")),
                                       body=str(new_message.body.encode("utf-8")),
                                       sent_date=send_date_to_str,
                                       received_date=received_date_to_str,
                                       status=str(CFG_WEBMESSAGE_STATUS_CODE['NEW']))
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
            converted_send_date = m.message.sent_date.strftime("%Y-%m-%d %H:%M:%S")
            converted_received_date = m.message.received_date.strftime("%Y-%m-%d %H:%M:%S")
            message_object = MessageObject(id=int(m.id_msgMESSAGE),
                                           id_user_from=int(m.message.id_user_from),
                                           nickname_user_from=str(m.message.user_from.nickname.encode("utf-8")),
                                           sent_to_user_nicks=str(m.message._sent_to_user_nicks.encode("utf-8")),
                                           sent_to_group_names=str(m.message._sent_to_group_names.encode("utf-8")),
                                           subject=str(m.message.subject.encode("utf-8")),
                                           body=str(m.message.body.encode("utf-8")),
                                           sent_date=str(converted_send_date),
                                           received_date=str(converted_received_date),
                                           status=str(m.status))
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

        #convert unicodes to string
        uid = int(uid)
        users_nicknames_to_str = json_data['users_nicknames_to'].encode("utf-8")
        groups_names_to_str = json_data['groups_names_to'].encode("utf-8")
        subject_str = json_data['subject'].encode("utf-8")
        body_str = json_data['body'].encode("utf-8")
        sent_date_str = json_data['sent_date'].encode("utf-8")
        sent_date_db_datetime_object = datetime.strptime(sent_date_str, "%Y-%m-%d %H:%M:%S")

        created_message_id = \
            messagesAPI.create_message(uid_from=uid,
                                       users_to_str=users_nicknames_to_str,
                                       groups_to_str=groups_names_to_str,
                                       msg_subject=subject_str,
                                       msg_body=body_str,
                                       msg_send_on_date=sent_date_db_datetime_object)

        created_message = messagesAPI.get_message(created_message_id)

        #convert dates from the database
        converted_send_date = created_message.sent_date.strftime("%Y-%m-%d %H:%M:%S")       # string send_date
        converted_received_date = created_message.received_date.strftime("%Y-%m-%d %H:%M:%S")       # string received_date

        message_object = MessageObject(id=int(created_message.id),
                                       id_user_from=int(created_message.id_user_from),
                                       nickname_user_from=str(created_message.user_from.nickname.encode("utf-8")),
                                       sent_to_user_nicks=str(created_message._sent_to_user_nicks.encode("utf-8")),
                                       sent_to_group_names=str(created_message._sent_to_group_names.encode("utf-8")),
                                       subject=str(created_message.subject.encode("utf-8")),
                                       body=str(created_message.body.encode("utf-8")),
                                       sent_date=str(converted_send_date),
                                       received_date=str(converted_received_date),
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


def setup_app(app, api):
    api.add_resource(
        MessageResource,
        '/api/messages/<int:message_id>',
    )
    api.add_resource(
        MessagesListResource,
        '/api/messages/'
    )
