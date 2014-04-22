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

        The dictionary that is returned as json has the following format
        key: 'successful' -> values: 'True'(shows if message was successfully retrieved),'False'
        key: 'id_user_from' -> values: int(the message id)
        key: 'sent_to_user_nicks' -> values: string(the nicknames of users recipients)
        key: 'sent_to_group_names' -> values: string(the groups names)
        key: 'subject' -> values: string(the subject of the message)
        key: 'body' -> values: string(the body of the message)
        key: 'sent_date' -> values: string(the date the message was sent)
        key: 'received_date' -> values: string(the date the message was received)
        :param message_id: the id of the message to return
        """
        uid = current_user.get_id()
        requested_message = messagesAPI.get_message(uid, message_id)
        return_dictionary = {}  # data to return as json
        if requested_message is None:
            return_dictionary['successful'] = 'False'
            #maybe add a 'problem' key to specify what error happened
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

        The dictionary that is returned as json has the following format
        key: 'message_deleted' -> values: 'True'(if message is deleted) , 'False'
        :param message_id: the id of the message to delete
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
        """
        replies to a message
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
        """
        returns all messages of a user
        """
        # from flask import request
        # request.args
        pass

    @login_required
    def delete(self):
        """
        deletes all messages of a user
        """
        pass

    @login_required
    def post(self):
        """
        creates and sends a new message
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