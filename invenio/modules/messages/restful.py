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
from flask.ext.login import current_user, login_required
#from invenio.base.manage import app
#from flask.ext import restful
from flask import jsonify
from invenio.modules.messages import api as messagesAPI


class MessageResource(Resource):

    @login_required
    def get(self, message_id):
        """Returns a message in json format

        :param message_id: the id of the message to return
        Returns:
            a dictionary as json that has the following format
            key: 'successful' -> values: 'True'(shows if message was successfully retrieved),'False'
            key: 'id_user_from' -> values: int(the message id)
            key: 'sent_to_user_nicks' -> values: string(the nicknames of users recipients)
            key: 'sent_to_group_names' -> values: string(the groups names)
            key: 'subject' -> values: string(the subject of the message)
            key: 'body' -> values: string(the body of the message)
            key: 'sent_date' -> values: string(the date the message was sent)
            key: 'received_date' -> values: string(the date the message was received)
        """
        uid = current_user.get_id()
        requested_message = messagesAPI.get_message(uid, message_id)
        return_dictionary = {}  # data to return as json
        if requested_message is None:
            return_dictionary['successful'] = 'False'
        else:
            return_dictionary['successful'] = 'True'
            return_dictionary['id'] = int(requested_message.id)
            return_dictionary['id_user_from'] = int(requested_message.id_user_from)
            return_dictionary['sent_to_user_nicks'] = str(requested_message._sent_to_user_nicks)
            return_dictionary['sent_to_group_names'] = str(requested_message._sent_to_group_names)
            return_dictionary['subject'] = str(requested_message.subject)
            return_dictionary['body'] = str(requested_message.body)
            return_dictionary['sent_date'] = str(requested_message.sent_date)
            return_dictionary['received_date'] = str(requested_message.received_date)
        return jsonify(return_dictionary)

    @login_required
    def delete(self, message_id):
        """Deletes a message

        :param message_id: the id of the message to delete
        Returns:
            a dictionary as json that has the following format
            key: 'message_deleted' -> values: 'True'(if message is deleted) , 'False'
        """
        uid = current_user.get_id()
        delete_message_result = messagesAPI.delete_message_from_user_inbox(uid, message_id)
        return_dictionary = {}
        if delete_message_result == 1:
            return_dictionary['message_deleted'] = 'True'
        else:
            return_dictionary['message_deleted'] = 'False'
        return jsonify(return_dictionary)

    @login_required
    def put(self, message_id):
        """Replies to a message

        First it accepts the body that will be added to the body
        of the old message
        :param msg_id: the id of the message to reply to
        """
        pass

    def head(self, message_id):
        abort(405)

    def options(self, message_id):
        abort(405)

    def patch(self, message_id):
        abort(405)


class MessagesListResource(Resource):
    @login_required
    def get(self):
        """Gets information about all messages of a user
        Returns:
            A dictionary is returned and every record is
            a dictionary that represents a message.
        """
        # from flask import request
        # request.args
        uid = current_user.get_id()
        return_dictionary = {}    # the dictionary that will contain the messages as dictionaries. the keys will be the message ids
        messages_lists = messagesAPI.get_all_messages_for_user(uid)     # this is a list of lists
        for m_list in messages_lists:
            message_as_dictionary = {}      # this dictionary will represent a single message
            message_id = int(m_list[0])     # get the message id
            message_as_dictionary['message_id'] = message_id
            id_user_from = int(m_list[1])   # get the id of the sender
            message_as_dictionary['id_user_from'] = int(id_user_from)
            nickname_user_from = str(m_list[2])     # get the nickname of the sender
            message_as_dictionary['nickname_user_from'] = nickname_user_from
            message_subject = str(m_list[3])    # get the subject
            message_as_dictionary['message_subject'] = message_subject
            message_sent_date = str(m_list[4])      # get the date the message was sent
            message_as_dictionary['message_sent_date'] = message_sent_date
            message_status = str(m_list[5])     # get the status of the message
            message_as_dictionary['message_status'] = message_status
            key = 'MSG_'+message_id     # create a key
            return_dictionary[key] = message_as_dictionary    # add the the message to the dictionary
        return jsonify(return_dictionary)

    @login_required
    def delete(self):
        """Deletes all messages of a user(except the reminders)

        Returns:
            a dictionary containing the number of the deleted messages
        """
        uid = current_user.get_id()
        number_of_deleted_messages = messagesAPI.delete_all_messages(uid)
        return_dictionary = {}
        return_dictionary['number_of_deleted_messages'] = number_of_deleted_messages
        return jsonify(return_dictionary)

    @login_required
    def post(self):
        """Creates and sends a new message
        """
        pass

    def head(self):
        abort(405)

    def options(self):
        abort(405)

    def patch(self):
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