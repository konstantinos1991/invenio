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
some utility functions
"""

from invenio.modules.accounts.models import User, Usergroup, UserUsergroup
#from invenio.legacy.dbquery import run_sql, OperationalError
from invenio.legacy.websession.websession_config import CFG_WEBSESSION_USERGROUP_STATUS
from invenio.modules.messages.config import CFG_WEBMESSAGE_STATUS_CODE
from invenio.ext.sqlalchemy import db
from invenio.modules.messages.models import UserMsgMESSAGE


def user_exists(uid):
    """
        checks if a user exists in the system, given his uid
        @param uid: the user id
        @return: True if the user exists in the system, else False
    """
    user_to_search = User.query.filter_by(id=uid).first()
    if user_to_search is not None:
        return True
    else:
        return False


# def get_nicknames_like(pattern):
#     """get nicknames like pattern"""
#     if pattern:
#         try:
#             res = run_sql("SELECT nickname FROM user WHERE nickname RLIKE %s", (pattern,))
#         except OperationalError:
#             res = ()
#         return res
#     return ()


# def get_groupnames_like(uid, pattern):
#     """Get groupnames like pattern. Will return only groups that user is allowed to see
#     """
#     groups = {}
#     if pattern:
#         # For this use case external groups are like invisible one
#         query1 = "SELECT id, name FROM usergroup WHERE name RLIKE %s AND join_policy like 'V%%' AND join_policy<>'VE'"
#         try:
#             res = run_sql(query1, (pattern,))
#         except OperationalError:
#             res = ()
#         # The line belows inserts into groups dictionary every tuple the database returned,
#         # assuming field0=key and field1=value
#         map(lambda x: groups.setdefault(x[0], x[1]), res)
#         query2 = """SELECT g.id, g.name
#                     FROM usergroup g, user_usergroup ug
#                     WHERE g.id=ug.id_usergroup AND ug.id_user=%s AND g.name RLIKE %s"""
#         try:
#             res = run_sql(query2, (uid, pattern))
#         except OperationalError:
#             res = ()
#         map(lambda x: groups.setdefault(x[0], x[1]), res)
#     return groups


# def get_nicks_from_uids(uids):
#     """
#     **REFACTORED
#     Get the association uid/nickname of given uids
#     @param uids: list or sequence of uids
#     @return: a dictionary {uid: nickname} where empty value is possible
#     """
#     if not((type(uids) is list) or (type(uids) is tuple)):
#         uids = [uids]
#     users = {}
#     for uid in uids:
#         u = User.query.filter_by(id=uid).first()
#         if u is not None:
#             users[int(uid)] = u.nickname
#     return users


def get_uids_from_emails(emails):
    """
    **REFACTORED
    Get the association uid/email of given emails
    @param emails: list or sequence of strings, each string being an email
    @return: a dictionary {email: uid}
    """
    # FIXME: test case
    if not((type(emails) is list) or (type(emails) is tuple)):
        emails = [emails]
    users = {}
    for e in emails:
        u = User.query.filter_by(email=e).first()
        if u is not None:
            users[e] = u.id
    return users


def get_gids_from_groupnames(groupnames):
    """
    **REFACTORED
    Get the gids of given groupnames
    @param groupnames: list or sequence of strings, each string being a groupname
    @return: a dictionary {groupname: gid}
    """
    # FIXME: test case
    if not((type(groupnames) is list) or (type(groupnames) is tuple)):
        groupnames = [groupnames]
    groups = {}
    for groupname in groupnames:
        group = Usergroup.query.filter_by(name=groupname)
        if group is not None:
            groups[groupname] = group.id
    return group


def get_uids_members_of_groups(gids):
    """
    **REFACTORED
    Get the distinct ids of users members of given groups.
    @param groupnames: list or sequence of group ids
    @return: a dictionary in the form {group_id:[list of user ids]}
    """
    if not((type(gids) is list) or (type(gids) is tuple)):
        gids = [gids]
    groups_uids = {}
    for groupid in gids:
        uids_in_groupid = []  # a list of user ids of a group
        records_of_groupid = UserUsergroup.query.filter_by(id_usergroup=groupid)
        for rec in records_of_groupid:
            if rec.status != CFG_WEBSESSION_USERGROUP_STATUS['PENDING']:
                uids_in_groupid.append(rec.id_user)
        groups_uids[groupid] = uids_in_groupid
    return groups_uids


def get_uids_from_nicks(nicks):
    """
    **REFACTORED
    Get the association uid/nickname of given nicknames
    @param nicks: list or sequence of strings, each string being a nickname
    @return: a dictionary {nickname: uid}
    """
    # FIXME: test case
    if not((type(nicks) is list) or (type(nicks) is tuple)):
        nicks = [nicks]
    users = {}
    for nick in nicks:
        user = User.query.filter_by(nickname=nick).first()
        if user is not None:
            users[nick] = user.id
    return users


def filter_messages_from_user_with_status(uid, status):
    """
    Filter message from user with status code.
    @param uid: user id
    @return: sqlalchemy.sql.expression.ClauseElement
    """
    # AsBINARY removed!!!
    return (UserMsgMESSAGE.status.__eq__(status)) & \
           (UserMsgMESSAGE.id_user_to == uid)


def filter_all_messages_from_user(uid):
    """
    Filter all message from user with status code not 'reminder'.
    @param uid: user id
    @return: sqlalchemy.sql.expression.ClauseElement
    """
    reminder = CFG_WEBMESSAGE_STATUS_CODE['REMINDER']
    return db.not_(UserMsgMESSAGE.status.__eq__(reminder)) & (UserMsgMESSAGE.id_user_to == uid)


def filter_user_message(uid, msgid):
    """
    Filter message from user with defined id(s).
    @param uid: user id
    @param msgid: message id(s)
    @return: sqlalchemy.sql.expression.ClauseElement
    """
    try:
        iter(msgid)
        return (UserMsgMESSAGE.id_user_to == uid) & (UserMsgMESSAGE.id_msgMESSAGE.in_(msgid))
    except:
        return ((UserMsgMESSAGE.id_user_to == uid) & (UserMsgMESSAGE.id_msgMESSAGE == msgid))