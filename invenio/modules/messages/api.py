## This file is part of Invenio.
## Copyright (C) 2008, 2009, 2010, 2011, 2012, 2013, 2014 CERN.
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
This is the API file for the database-related
functions of messages. The ORM mechanism of sqlalchemy
will be mostly used here.
"""

from datetime import datetime
#from invenio.legacy.dbquery import OperationalError
from invenio.legacy.dbquery import run_sql
from invenio.modules.messages.config import \
    CFG_WEBMESSAGE_STATUS_CODE, \
    CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA, \
    CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES

#from invenio.modules.messages.config import CFG_WEBMESSAGE_DAYS_BEFORE_DELETE_ORPHANS

#from invenio.utils.date import datetext_default, convert_datestruct_to_datetext
#from invenio.legacy.websession.websession_config import CFG_WEBSESSION_USERGROUP_STATUS

from invenio.ext.sqlalchemy import db
from invenio.modules.messages.models import MsgMESSAGE, UserMsgMESSAGE
from invenio.modules.accounts.models import User
from invenio.modules.messages.util import filter_messages_from_user_with_status, filter_all_messages_from_user, \
    filter_user_message
from invenio.modules.messages import errors
# from invenio.modules.messages.errors import MessageNotFound, MessageNotDeleted, \
#     MessagesNotFetchedError, MessageNotCreatedError


def check_user_owns_message(uid, msgid):
    """Checks whether a user owns a message

    **REFACTORED
    :param uid:   user id
    :param msgid: message id
    :returns: bool -- True if the user owns the message, else False
    """
    user_msg = UserMsgMESSAGE.query.filter_by(id_user_to=uid,
                                              id_msgMESSAGE=msgid).first()
    if user_msg is None:
        return False
    return True


def message_exists(msgid):
    """Checks if a message with exists in the database

    :param msgid: message id
    :returns: bool -- True if msgid exists else False
    """
    m = MsgMESSAGE.query.filter_by(id=msgid).first()
    if m is None:
        return False
    return True


def get_message(msgid):
    """ Fetches a message from the table MsgMESSAGE

    :param msgid: the id of the message
    :returns: -- an object of type MsgMESSAGE
    """
    try:
        return MsgMESSAGE.query.filter(MsgMESSAGE.id == int(msgid)).one()
    except Exception as e:
        print e.args
        raise errors.MessageNotFound("Message cannot be found")


def get_message_from_user_inbox(uid, msgid):
    """Get a message with its status and sender nickname.

    :param uid: user id
    :param msgid: message id
    :returns: exactly one message or raise an exception.
    """
    # try:
    #     return UserMsgMESSAGE.query.options(db.joinedload_all(UserMsgMESSAGE.message, MsgMESSAGE.user_from)).\
    #         options(db.joinedload(UserMsgMESSAGE.user_to)).filter(filter_user_message(uid, msgid)).one()
    # except Exception:
    #     raise MessageNotFound("Message cannot be found")
    try:
        return UserMsgMESSAGE.query.\
            filter(UserMsgMESSAGE.id_user_to == int(uid),
                   UserMsgMESSAGE.id_msgMESSAGE == int(msgid)).one()
    except Exception:
        raise errors.MessageNotFound("Message cannot be found")


def set_message_status(uid, msgid, new_status):
    """Change the status of a message (e.g. from "new" to "read").

    the status is a single character string, specified in constant
    CFG_WEBMESSAGE_STATUS_CODE in file webmessage_config.py
    examples:
        N: New message
        R: already Read message
        M: reminder
    :param uid:        user ID
    :param msgid:      Message ID
    :param new_status: new status. Should be a single character
    :returns: int -- 1 if success, 0 if not
    """
    return db.session.query(UserMsgMESSAGE).filter(filter_user_message(uid, msgid)).update({UserMsgMESSAGE.status: new_status})


def update_user_inbox_for_reminders(uid):
    """Updates user's inbox with any reminders that should have arrived

    :param uid: user id
    :returns: int -- number of new expired reminders
    """
    #now = convert_datestruct_to_datetext(localtime())
    reminder_status = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']
    new_status = CFG_WEBMESSAGE_STATUS_CODE['NEW']
    expired_reminders = db.session.query(UserMsgMESSAGE.id_msgMESSAGE).\
        join(UserMsgMESSAGE.message).\
        filter(db.and_(UserMsgMESSAGE.id_user_to == uid, UserMsgMESSAGE.status.like(reminder_status), MsgMESSAGE.received_date <= datetime.now())).all()

    if len(expired_reminders):
        filter = db.and_(
            UserMsgMESSAGE.id_user_to == uid,
            UserMsgMESSAGE.id_msgMESSAGE.in_(
                [i for i, in expired_reminders]))

        res = UserMsgMESSAGE.query.filter(filter).\
            update({UserMsgMESSAGE.status: new_status}, synchronize_session='fetch')
        return res


def get_nb_new_messages_for_user(uid):
    """ Get number of new mails for a given user
    :param uid: user id (int)
    :return: number of new mails as int.
    """
    update_user_inbox_for_reminders(uid)
    new_status = CFG_WEBMESSAGE_STATUS_CODE['NEW']
    return db.session.query(db.func.count(UserMsgMESSAGE.id_msgMESSAGE)).select_from(UserMsgMESSAGE).filter(filter_messages_from_user_with_status(uid, new_status)).scalar()


def get_nb_readable_messages_for_user(uid):
    """ Get number of mails of a fiven user. Reminders are not counted
    :param uid: user id (int)
    :returns: int -- number of messages
    """
    return \
        db.session.query(db.func.count(UserMsgMESSAGE.id_msgMESSAGE)).\
        select_from(UserMsgMESSAGE).\
        filter(filter_all_messages_from_user(uid)).\
        scalar()


def get_all_messages_for_user(uid):
    """Get all messages for a user's inbox,
    without the eventual non-expired reminders.

    :param uid: user id
    :returns: -- a list of objects of type UserMsgMESSAGE
    :returns: [(message_id,
              id_user_from,
              nickname_user_from,
              message_subject,
              message_sent_date,
              message_status)]
    """
    try:
        update_user_inbox_for_reminders(uid)
        reminder = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']
        return \
            UserMsgMESSAGE.query.join(MsgMESSAGE).\
            filter(MsgMESSAGE.id == UserMsgMESSAGE.id_msgMESSAGE,
                   UserMsgMESSAGE.id_user_to == int(uid),
                   UserMsgMESSAGE.status != reminder).\
            order_by(MsgMESSAGE.received_date).all()
        # return \
        #     MsgMESSAGE.query.options(db.joinedload(MsgMESSAGE.user_from)).\
        #     join(UserMsgMESSAGE).\
        #     filter(filter_all_messages_from_user(uid)).\
        #     order_by(MsgMESSAGE.sent_date).all()
    except Exception:
        raise errors.MessagesNotFetchedError("Could not fetch messages")


def number_of_all_messages_in_inbox_of_user(uid):
    """Get the number of all messages of a user's inbox

    :param uid: user id
    :returns: int -- number of messages of a user's inbox
    """
    return len(get_all_messages_for_user(uid))


def get_new_messages_for_user(uid):
    """ Fetches all new messages

    :param uid: the user id_user_from
    :returns: -- a list of objects of type UserMsgMESSAGE
    """
    try:
        update_user_inbox_for_reminders(uid)
        NEW = CFG_WEBMESSAGE_STATUS_CODE['NEW']
        return \
            UserMsgMESSAGE.query.join(MsgMESSAGE).\
            filter(MsgMESSAGE.id == UserMsgMESSAGE.id_msgMESSAGE,
                   UserMsgMESSAGE.id_user_to == int(uid),
                   UserMsgMESSAGE.status == NEW).\
            order_by(MsgMESSAGE.received_date).all()
    except Exception:
        raise errors.MessagesNotFetchedError("Could not fetch new messages")


def number_of_new_messages_for_user(uid):
    """ Counts the new messages of a user

    :param uid: the user id
    :returns: int -- the number of the new messages in a user's inbox
    """
    return len(get_new_messages_for_user(uid))


def get_the_read_messages_in_inbox_of_user(uid):
    """ Fetches the messages that a user has read already

    :param uid: the user id
    :returns: -- a list of objects of type UserMsgMESSAGE
    """
    try:
        update_user_inbox_for_reminders(uid)
        READ = CFG_WEBMESSAGE_STATUS_CODE['READ']
        return \
            UserMsgMESSAGE.query.join(MsgMESSAGE).\
            filter(MsgMESSAGE.id == UserMsgMESSAGE.id_msgMESSAGE,
                   UserMsgMESSAGE.id_user_to == int(uid),
                   UserMsgMESSAGE.status == READ).\
            order_by(MsgMESSAGE.received_date).all()
    except Exception:
        raise errors.MessagesNotFetchedError("Could not fetch the messages that are already read")


def number_of_read_messages_in_inbox_of_user(uid):
    """ Counts the read messages of a user

    :param uid: the user id
    :returns: int -- the number of the new messages in a user's inbox
    """
    return len(get_the_read_messages_in_inbox_of_user(uid))


def count_nb_messages(uid):
    """Counts the messages of a user

    :param uid: user id
    :returns: int -- number of messages a user has, 0 if none
    """
    uid = int(uid)
    return \
        db.session.query(db.func.count(UserMsgMESSAGE.id_user_to)).\
        select_from(UserMsgMESSAGE).\
        filter(UserMsgMESSAGE.id_user_to == uid).\
        scalar()


def delete_message_from_user_inbox(uid, msg_id):
    """Delete message from users inbox

    If this message does not exist in any other user's inbox,
    delete it permanently from the database
    :param uid: user id
    :param msg_id: message id
    :returns: int 1 if delete was successful, 0 else
    """
    try:
        res = \
            UserMsgMESSAGE.query.filter(filter_user_message(uid, msg_id)).\
            delete(synchronize_session=False)
        check_if_need_to_delete_message_permanently(msg_id)
        if res == 0:
            raise errors.MessageNotDeleted("Message could not be deleted")
        return res
    except Exception:
        raise errors.MessageNotDeleted("Message could not be deleted")


def check_if_need_to_delete_message_permanently(msg_ids):
    """Checks if a list of messages exist in anyone's inbox, if not,
    delete them permanently

    :param msg_id: sequence of message ids
    :returns: int -- number of deleted messages
    """
    if not((type(msg_ids) is list) or (type(msg_ids) is tuple)):
        msg_ids = [msg_ids]

    msg_used = \
        db.session.query(UserMsgMESSAGE.id_msgMESSAGE).\
        filter(UserMsgMESSAGE.id_msgMESSAGE.in_(msg_ids)).\
        group_by(UserMsgMESSAGE.id_msgMESSAGE).\
        having(db.func.count(UserMsgMESSAGE.id_user_to) > 0).\
        subquery()

    return \
        MsgMESSAGE.query.filter(MsgMESSAGE.id.in_(msg_ids) & db.not_(MsgMESSAGE.id.in_(msg_used))).\
        delete(synchronize_session=False)


def delete_all_messages(uid):
    """Delete all messages of a user (except reminders)

    :param uid: user id
    :returns: int -- the number of messages deleted
    """
    try:
        reminder_status = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']
        msg_ids = map(lambda (x, ): x, db.session.query(UserMsgMESSAGE.id_msgMESSAGE).filter(db.and_(UserMsgMESSAGE.id_user_to == uid, UserMsgMESSAGE.status != reminder_status)).all())
        nb_messages = \
            UserMsgMESSAGE.query.filter(db.and_(UserMsgMESSAGE.id_user_to == uid, UserMsgMESSAGE.status != reminder_status)).delete(synchronize_session=False)
        if len(msg_ids) > 0:
            check_if_need_to_delete_message_permanently(msg_ids)
        return nb_messages
    except Exception:
        raise errors.MessageNotDeleted("Error while deleting all messages")


def check_if_user_has_free_space(uid):
    """checks if a user has free space to his inbox

    **ADDED
    :param uid: user id
    :returns: bool -- True if the user has free space in inbox , else False
    """
    users_with_full_mailbox = check_quota(CFG_WEBMESSAGE_MAX_NB_OF_MESSAGES)
    if uid in users_with_full_mailbox:
        return False
    else:
        return True


def create_message(uid_from,
                   users_to_str="",
                   groups_to_str="",
                   msg_subject="",
                   msg_body="",
                   msg_send_on_date=datetime.strptime(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "%Y-%m-%d %H:%M:%S")):
    """
    **REFACTORED
    Creates a message in the msgMESSAGE table. Does NOT send the message.
    This function is like a datagramPacket...
    :param uid_from: uid of the sender (int)
    :param users_to_str: a string, with nicknames separated by semicolons (';')
    :param groups_to_str: a string with groupnames separated by semicolons
    :param msg_subject: string containing the subject of the message
    :param msg_body: string containing the body of the message
    :param msg_send_on_date: date on which message must be sent. Has to be a
                             datetex format (i.e. YYYY-mm-dd HH:MM:SS)
    :returns: int -- id of the created message
    """
    try:
        # if isinstance(msg_send_on_date,str):      #convert string to datetime.datetime
        #     dt = datetime.strptime(msg_send_on_date, "%Y-%m-%d %H:%M:%S")
        #     msg_send_on_date = dt
        #     print "conversion"
        # print "after datetime.strptime"
        # m = MsgMESSAGE()
        # print "created object m"
        # m.id_user_from = uid_from
        # print "set id_user_from"
        # m.sent_date = msg_send_on_date
        # print "set sent_date"
        # m.received_date = msg_send_on_date
        # print "set received_date"
        # print users_to_str,type(users_to_str)
        # m._sent_to_user_nicks = db.String(users_to_str)
        # print "set user_nicks"
        # m._sent_to_group_names = db.String(groups_to_str)
        # print "set groups"
        # m.subject = db.String(msg_subject)
        # print "set subject"
        # m.body = db.String(msg_body)
        # print "set body"
        m = MsgMESSAGE(id_user_from=uid_from, sent_to_user_nicks=users_to_str,
                       sent_to_group_names=groups_to_str,
                       subject=msg_subject, body=msg_body,
                       sent_date=msg_send_on_date,
                       received_date=msg_send_on_date)
        return m.send()
    except Exception as e:
        print e.args
        raise errors.MessageNotCreatedError("Message could not be created")


def reply_to_sender(msg_id, reply_body, uid):
    """Replies back to sender

    :param msg_id: the id of the message to which a user wants to reply to
    :param reply_body: the body of the new message
    :param uid: the id of the user that replies back
    """
    m = get_message(msg_id)
    return m.reply_to_sender_only(reply_body=reply_body, user_id=uid)


# def send_message(uids_to, msgid, status=CFG_WEBMESSAGE_STATUS_CODE['NEW']):
#     """Send message to uids

#     **REFACTORED
#     @param uids: sequence of user ids
#     @param msg_id: id of message
#     @param status: status of the message. (single char, see webmessage_config.py).
#     @returns: a list of users having their mailbox full
#     """
#     if not((type(uids_to) is list) or (type(uids_to) is tuple)):
#         uids_to = [uids_to]

#     users_with_full_mailbox = []
#     #find the people with full mailbox and exclude them from the list of recipients
#     for uid in uids_to:
#         if check_if_user_has_free_space(uid) is False:
#             users_with_full_mailbox.append(uid)
#             uids_to.delete(uid)
#     #send the message to the remaining recipients if there are any
#     if len(uids_to) > 0:
#         for uid in uids_to:
#             user_msg_rec = UserMsgMESSAGE(id_user_to=uid, id_msgMESSAGE=msgid, status=status)
#             db.session.add(user_msg_rec)
#         db.session.commit()
#     return users_with_full_mailbox

# def reply_to_message(uid, body_to_be_added, reply_msg_id):
#     """
#         a user can reply back to a certain message
#         @param uid: the user id
#         @param msg_id: the message id to reply to
#     """
#     old_message = MsgMESSAGE.query.filter_by(id=reply_msg_id)
#     uid_from = uid
#     uids_to_str = []
#     uids_to_str.append(str(old_message.id_user_from))
#     new_subject = 'RE: '+old_message.subject
#     new_body = body_to_be_added+'\n'+'---------'+'\n'+old_message.body
#     now = convert_datestruct_to_datetext(localtime())
#     send_date = now
#     received_date = now
#     new_msg_id = create_message(uid_from,uids_to_str,"",new_subject,new_body,received_date)
#     #now that the message is created , send it
#     uids_to = []
#     for uid in uids_to_str:
#         uids_to.append(int(uid))
#     send_message(uids_to,new_msg_id,CFG_WEBMESSAGE_STATUS_CODE['NEW'])


def check_quota(nb_messages):
    """
    :param nb_messages: max number of messages a user can have
    :returns: a dictionary of users over-quota
    """
    from invenio.legacy.webuser import collect_user_info
    from invenio.modules.access.control import acc_is_user_in_role, acc_get_role_id
    no_quota_role_ids = [acc_get_role_id(role) for role in CFG_WEBMESSAGE_ROLES_WITHOUT_QUOTA]
    res = {}
    for uid, n in run_sql("SELECT id_user_to, COUNT(id_user_to) FROM user_msgMESSAGE GROUP BY id_user_to HAVING COUNT(id_user_to) > %s", (nb_messages, )):
        user_info = collect_user_info(uid)
        for role_id in no_quota_role_ids:
            if acc_is_user_in_role(user_info, role_id):
                break
        else:
            res[uid] = n
    return res


#get_nicknames_like(pattern) NOT check_if_need_to_delete_message_permanently
#get_groupnames_like(uid, pattern) NOT NEEDED
#get_element(sql_res) NOT NEEDED

def clean_messages():
    """ Cleans MsgMESSAGE table"""
    msgids_to_delete = []

    all_messages_ids = db.session.query(MsgMESSAGE.id).all()
    all_users_messages_ids = db.session.query(UserMsgMESSAGE.id_msgMESSAGE).all()

    # case 1
    # find the ids of the messages that must be deleted
    for msgid in all_messages_ids:
        if msgid not in all_users_messages_ids:
            msgids_to_delete.append(msgid)

    # case 2
    messages_users_dictionary = {}  # dictionary in form {m_id: [uids]}
    #get the distinct message ids from UserMsgMESSAGE
    distinct_mids_in_user_messages = \
        db.session.query(UserMsgMESSAGE.id_msgMESSAGE.distinct()).order_by(UserMsgMESSAGE.id_msgMESSAGE).all()

    for mid in distinct_mids_in_user_messages:
        #get the user ids that have mid in their mailbox
        uids_with_mid = \
            db.session.query(UserMsgMESSAGE.id_user_to).\
            filter_by(id_msgMESSAGE=mid).order_by(UserMsgMESSAGE.id_user_to).all()
        messages_users_dictionary[mid] = uids_with_mid

    for mid in messages_users_dictionary:   # for every (distinct) message id in the User_MsgMESSAGE table
        counter_uid_with_mid_not_in_users = 0
        for uid in messages_users_dictionary[mid]:  # get the users that have received the message with mid
            if uid not in db.session.query(User.id).order_by(User.id).all():
                counter_uid_with_mid_not_in_users += 1
        if counter_uid_with_mid_not_in_users == len(messages_users_dictionary[mid]):    # if none of the users that has receive the message with mid as id ,is not in the system anymore
            msgids_to_delete.append()

    #delete all the messages that their ids belong to the list 'message_to_delete'
    if len(msgids_to_delete) > 0:
        for msgid in msgids_to_delete:
            message_to_delete = MsgMESSAGE.query.filter_by(id=msgid).first()
            db.session.delete(message_to_delete)

        db.session.commit()
