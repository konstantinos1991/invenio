# -*- coding: utf-8 -*-
##
## This file is part of Invenio.
## Copyright (C) 2013, 2014 CERN.
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
    Exceptions for Invenio Messages module
"""


class InvenioWebMessageError(Exception):
    """A generic error for WebMessage."""
    def __init__(self, message="General error concerning messages"):
        """Initialisation."""
        self.message = message

    def __str__(self):
        """String representation."""
        return repr(self.message)


class MessageNotCreatedError(InvenioWebMessageError):
    """An error indicating that a message could be created"""

    def __init__(self, error_msg):
        """Initialize using the parent class"""
        InvenioWebMessageError.__init__(self, error_msg)


class MessageNotFoundError(InvenioWebMessageError):
    """An error indicating that a message cannot be found"""

    def __init__(self, error_msg):
        """Initialize using the parent class"""
        InvenioWebMessageError.__init__(self, error_msg)


class MessageNotDeletedError(InvenioWebMessageError):
    """An error indicating that a message cannot be deleted"""

    def __init__(self, error_msg):
        """Initialize using the parent class"""
        InvenioWebMessageError.__init__(self, error_msg)


class MessagesNotFetchedError(InvenioWebMessageError):
    """An error indicating that the messages of a user cannot be fetched """

    def __init__(self, error_msg):
        """Initialize using the parent class"""
        InvenioWebMessageError.__init__(self, error_msg)


__all__ = ['InvenioWebMessageError', 'MessageNotCreatedError',
           'MessageNotFoundError', 'MessageNotDeletedError',
           'MessagesNotFetchedError']
