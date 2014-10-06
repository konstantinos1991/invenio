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


from invenio.legacy.docextract.pdf import convert_PDF_to_plaintext


class TextReader(object):

    def __init__(self, full_file_path):
        """Initialization.

        :param full_file_path: absolute path of a pdf file
        """
        self.full_file_path = full_file_path
        self.text_lines = []

    def can_open_file(self):
        (self.text_lines, status) = convert_PDF_to_plaintext(
            self.full_file_path, True)
        if not self.text_lines:
            return False
        return True

    def get_lines(self):
        if self.can_open_file() is True:
            return self.text_lines
