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


import string


class CrossrefDoiValidation(object):

    exclude = [punctuation.decode('utf8')
               for punctuation in set(string.punctuation)
               if not isinstance(punctuation, unicode)]

    def __init__(self, lines_of_text, metadata, threshold):
        self.lines_of_text = lines_of_text
        self.metadata = metadata
        if (threshold < 0) or (threshold > 1):
            self.threshold = 0.8
        else:
            self.threshold = threshold
        self.terms_of_text = []
        self.terms_to_search = []
        self.score = 0
        self.__get_text_to_search()
        self.__get_title_and_authors()

    def __get_text_to_search(self):
        # join lines
        text = ' '.join([line for line in self.lines_of_text])
        # transform to unicode if necessary
        if not isinstance(text, unicode):
            text = text.decode('utf8')
        # lower all letters
        text = text.lower()
        # get the first 2000 characters
        text = text[0:2000]
        text = ''.join([c for c in text if c not in self.exclude])
        self.terms_of_text = text.split()

    def __get_title_and_authors(self):
        if self.metadata:
            print("Validation: metadata {0}".format(self.metadata))
            # TODO check if combination extractor returns unicode stuff!!!
            if ('crossref_title' in self.metadata) and \
               ('crossref_author' in self.metadata):
                if (self.metadata['crossref_title']) and \
                   (len(self.metadata['crossref_title'])):
                    title = self.metadata['crossref_title'][0]
                    if not isinstance(title, unicode):
                        title = title.decode('utf8')
                    # tokenize and clean title
                    title = ''.join([c for c in title
                                     if c not in self.exclude])
                    title = title.lower()
                    title_words = title.split()
                    for title_word in title_words:
                        self.terms_to_search.append(title_word)
                if (self.metadata['crossref_author']) and \
                   (len(self.metadata['crossref_author']) > 0):
                    authors = self.metadata['crossref_author']
                    for author in authors:
                        # clean author's full name
                        if not isinstance(author, unicode):
                            author = author.decode('utf8')
                        author = author.lower().split()[0]
                        author = ''.join([c for c in author
                                          if c not in self.exclude])
                        if author:
                            self.terms_to_search.append(author)

    def validate(self):
        if not self.terms_to_search:
            return False
        else:
            for st in self.terms_to_search:
                for tt in self.terms_of_text:
                    if st in tt:
                        self.score += 1
                        break
            self.score = float(self.score)/float(len(self.terms_to_search))
            if self.score >= self.threshold:
                return True
            else:
                return False
