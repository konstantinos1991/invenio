# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2014 CERN.
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
## along with Invenio; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.

"""
test_messages_restful.py contains the tests
for the the restful api that concerns messages
"""


from invenio.ext.restful.utils import APITestCase
from invenio.ext.sqlalchemy import db
from datetime import datetime


class TestMessagesRestfulAPI(APITestCase):
    """This class tests the restful api for the messages"""

    def setUp(self):
        """Runs before each test"""
        from invenio.modules.accounts.models import User

        self.user_a = User(email='user_a@example.com', _password='iamusera',
                           nickname='user_a')
        self.user_b = User(email='user_b@example.com', _password='iamuserb',
                           nickname='user_b')
        try:
            db.session.add(self.user_a)
            db.session.add(self.user_b)
            db.session.commit()
        except Exception:
            db.session.rollback()

        self.create_oauth_token(self.user_a.id, scopes=[""])
        self.create_oauth_token(self.user_b.id, scopes=[""])

    def tearDown(self):
        """Runs after every test"""
        from invenio.modules.accounts.models import User

        self.remove_oauth_token()
        User.query.filter(User.nickname.in_([
            self.user_a.nickname,
            self.user_b.nickname,
        ])).delete(synchronize_session=False)
        db.session.commit()

    def test_405_methods_messages_list_resource(self):
        methods_messages_list_resource = [self.head, self.options, self.patch]
        for m in methods_messages_list_resource:
            m(
                'messageslistresource',
                user_id=self.user_a.id,
                code=405,
            )

    def test_create_message_pass(self):
        from invenio.modules.messages.models import MsgMESSAGE, UserMsgMESSAGE
        # user_a creates and sends a message to user_b
        message_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        answer = self.post(
            'messageslistresource',
            data=message_data,
            user_id=self.user_a.id,
            code=201,
        )
        print "Inside test_create_message_pass"
        print answer.json
        try:
            #delete the message that was created
            m_id = int(answer.json['id'])
            um = UserMsgMESSAGE.query.filter(UserMsgMESSAGE.id_user_to == self.user_b.id,
                                             UserMsgMESSAGE.id_msgMESSAGE == m_id).one()
            db.session.delete(um)
            m = MsgMESSAGE.query.filter(MsgMESSAGE.id == m_id).one()
            db.session.delete(m)
            db.session.commit()
        except Exception as e:
            print e.args

    def test_create_message_fail(self):
        message_data = dict(
            users_nicknames_to="user_b",
            groups_names_to=1,
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date='1900-01-01 00:00:00',
        )
        answer = self.post(
            'messageslistresource',
            data=message_data,
            user_id=self.user_a.id,
            code=400,
        )
        self.assertEqual(answer.json['message'], "validation failed")
        self.assertEqual(answer.json['status'], 400)

    def test_get_all_messages(self):
        from invenio.modules.messages.models import MsgMESSAGE, UserMsgMESSAGE
        #first create and send two messages from user_a to user_b
        m1_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        answer1 = self.post(
            'messageslistresource',
            data=m1_data,
            user_id=self.user_a.id,
            code=201,
        )

        m2_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="second message from user_a to user_b",
            body="this is the second message from user_a to user_b",
            sent_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        answer2 = self.post(
            'messageslistresource',
            data=m2_data,
            user_id=self.user_a.id,
            code=201,
        )
        #get the messages of user_b
        get_all_messages_answer = self.get(
            'messageslistresource',
            user_id=self.user_b.id,
        )
        print "Inside test_get_all_messages"
        print get_all_messages_answer.json
        #delete the messages that were created
        try:
            m1_id = answer1.json['id']
            um1 = UserMsgMESSAGE.query.filter(UserMsgMESSAGE.id_user_to == self.user_b.id,
                                              UserMsgMESSAGE.id_msgMESSAGE == m1_id).one()
            db.session.delete(um1)
            m1 = MsgMESSAGE.query.filter(MsgMESSAGE.id == m1_id).one()
            db.session.delete(m1)
            db.session.commit()

            m2_id = answer2.json['id']
            um2 = UserMsgMESSAGE.query.filter(UserMsgMESSAGE.id_user_to == self.user_b.id,
                                              UserMsgMESSAGE.id_msgMESSAGE == m2_id).one()
            db.session.delete(um2)
            m2 = MsgMESSAGE.query.filter(MsgMESSAGE.id == m2_id).one()
            db.session.delete(m2)
            db.session.commit()
        except Exception as e:
            e.args

    def test_delete_all_messages(self):
        #first create and send two messages from user_a to user_b
        m1_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.post(
            'messageslistresource',
            data=m1_data,
            user_id=self.user_a.id,
            code=201,
        )

        m2_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="second message from user_a to user_b",
            body="this is the second message from user_a to user_b",
            sent_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        self.post(
            'messageslistresource',
            data=m2_data,
            user_id=self.user_a.id,
            code=201,
        )
        self.delete(
            'messageslistresource',
            user_id=self.user_b.id,
            code=204,
        )

    def test_get_message(self):
        from invenio.modules.messages.models import MsgMESSAGE, UserMsgMESSAGE
        #create and send a message from user_a to user_b
        message_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        answer_post = self.post(
            'messageslistresource',
            data=message_data,
            user_id=self.user_a.id,
            code=201,
        )
        #get the message of user_b with the specified message id
        get_answer = self.get(
            'messageresource',
            urlargs=dict(message_id=int(answer_post.json['id'])),
            user_id=self.user_b.id,
        )

        print "Inside test_get_message"
        print get_answer.json
        try:
            #delete the message that was created
            m_id = int(get_answer.json['id'])
            um = UserMsgMESSAGE.query.filter(UserMsgMESSAGE.id_user_to == self.user_b.id,
                                             UserMsgMESSAGE.id_msgMESSAGE == m_id).one()
            db.session.delete(um)
            m = MsgMESSAGE.query.filter(MsgMESSAGE.id == m_id).one()
            db.session.delete(m)
            db.session.commit()
        except Exception as e:
            print e.args

    def test_delete_message(self):
        #first create and send a message from user_a to user_b
        m1_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        answer_post = self.post(
            'messageslistresource',
            data=m1_data,
            user_id=self.user_a.id,
            code=201,
        )
        self.delete(
            'messageresource',
            urlargs=dict(message_id=int(answer_post.json['id'])),
            user_id=self.user_b.id,
            code=204,
        )

    def test_reply_to_sender(self):
        from invenio.modules.messages.models import MsgMESSAGE, UserMsgMESSAGE
        #send a message from user_a to user_b
        m_data = dict(
            users_nicknames_to="user_b",
            groups_names_to="",
            subject="first message from user_a to user_b",
            body="this is the first message from user_a to user_b",
            sent_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
        answer_post = self.post(
            'messageslistresource',
            data=m_data,
            user_id=self.user_a.id,
            code=201,
        )

        #user_b replies to message
        data_to_reply = dict(
            reply_body="this is a reply to the message of user_a"
        )
        answer_put = self.put(
            'messageresource',
            urlargs=dict(message_id=int(answer_post.json['id'])),
            data=data_to_reply,
            user_id=self.user_b.id,
            code=201,
        )
        print "Inside test_reply_to_sender"
        print answer_put.json

        #delete what has been created
        try:
            m_id = int(answer_post.json['id'])
            um = UserMsgMESSAGE.query.filter(UserMsgMESSAGE.id_user_to == self.user_b.id,
                                             UserMsgMESSAGE.id_msgMESSAGE == m_id).one()
            db.session.delete(um)
            m = MsgMESSAGE.query.filter(MsgMESSAGE.id == m_id).one()
            db.session.delete(m)
            db.session.commit()

            m_id = int(answer_put.json['id'])
            um = UserMsgMESSAGE.query.filter(UserMsgMESSAGE.id_user_to == self.user_a.id,
                                             UserMsgMESSAGE.id_msgMESSAGE == m_id).one()
            db.session.delete(um)
            m = MsgMESSAGE.query.filter(MsgMESSAGE.id == m_id).one()
            db.session.delete(m)
            db.session.commit()
        except Exception as e:
            print e.args
