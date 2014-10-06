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

import json
import urllib


class CrossRefExtractor(object):
    """Extract metadata from documents."""

    crossref_site = "http://api.crossref.org/works?filter=doi:"

    def __init__(self, doi):
        """Initialization."""
        self.doi = doi
        self.json_data = {}
        self.metadata = {}
        # query crossref site
        self.__connect_to_crossref_and_read()

    def __connect_to_crossref_and_read(self):
        """Connect to crossref and read data."""
        query = self.crossref_site + self.doi
        query = query.encode('utf8')
        # query = self.crossref_site.format(self.doi)
        connection = None
        try:
            connection = urllib.urlopen(query)
            self.json_data = json.loads(connection.read())
        except Exception:
            print("crossref error when connecting/reading")
            self.json_data = {}
        finally:
            if connection:
                connection.close()

    def problem_with_connection(self):
        if not self.json_data:
            return True
        return False

    def parse_metadata(self):
        """Parse json data from the response."""

        if not self.json_data:
            return {}

        if self.json_data['status'] != 'ok':
            print("Status of response is {0}".format(self.json_data['status']))
            return {}

        if self.json_data['message']['total-results'] == 1:
            # get the sub-dictionary with the important metadata
            important_data = self.json_data['message']['items'][0]
            # get the 'subject' of the document
            if 'subject' in important_data:
                if len(important_data['subject']) > 0:
                    subjects = []
                    for m_subject in important_data['subject']:
                        if not isinstance(m_subject, unicode):
                            m_subject = m_subject.decode('utf8')
                        subjects.append(m_subject)
                    self.metadata['crossref_subject'] = subjects
            # get the 'author'
            if 'author' in important_data:
                if len(important_data['author']):
                    authors = []
                    for element in important_data['author']:
                        last_name = element['family']
                        first_name = element['given']
                        if not isinstance(last_name, unicode):
                            last_name = last_name.decode("utf8")
                        if not isinstance(first_name, unicode):
                            first_name = first_name.decode("utf8")
                        author_to_add = last_name + ', ' + first_name
                        authors.append(author_to_add)
                    self.metadata['crossref_author'] = authors
            # instead of 'author' we might find 'editor'

            # get the 'title' , is of type <list>
            if 'title' in important_data:
                if len(important_data['title']) > 0:
                    titles = []
                    for t in important_data['title']:
                        if not isinstance(t, unicode):
                            t = t.decode('utf8')
                        titles.append(t)
                    self.metadata['crossref_title'] = titles
            # get 'type' of the document, eg book, journal
            if 'type' in important_data:
                m_type = important_data['type']
                if not isinstance(m_type, unicode):
                    m_type = m_type.decode('utf8')
                self.metadata['crossref_type'] = m_type
            # get 'DOI'
            if 'DOI' in important_data:
                m_doi = important_data['DOI']
                if not isinstance(m_doi, unicode):
                    m_doi = m_doi.decode('utf8')
                self.metadata['crossref_DOI'] = m_doi
            # get 'URL'
            if 'URL' in important_data:
                m_url = important_data['URL']
                if not isinstance(m_url, unicode):
                    m_url = m_url.decode('utf8')
                self.metadata['crossref_URL'] = m_url
            # get 'publisher'
            if 'publisher' in important_data:
                m_publisher = important_data['publisher']
                if not isinstance(m_publisher, unicode):
                    m_publisher = m_publisher.decode('utf8')
                self.metadata['crossref_publisher'] = m_publisher
            # get 'reference-count'
            if 'reference-count' in important_data:
                self.metadata['crossref_reference-count'] = (
                    important_data['reference-count'])
            # get issue number
            if 'issue' in important_data:
                issue = important_data['issue']
                if not isinstance(issue, unicode):
                    issue = issue.decode('utf8')
                self.metadata['crossref_issue'] = issue
            # get ISSN , is of type <list>
            if 'ISSN' in important_data:
                issn_list = []
                for issn in important_data['ISSN']:
                    if not isinstance(issn, unicode):
                        issn = issn.decode('utf8')
                    issn_list.append(issn)
                self.metadata['crossref_ISSN'] = issn_list

            return self.metadata
        else:
            return {}

    def get_subject(self):
        """Get the subject."""
        if not self.metadata:
            self.parse_metadata()
        if 'crossref_subject' in self.metadata:
            return self.metadata['crossref_subject']
        else:
            return None

    def get_authors(self):
        """Get the author(s)."""
        if not self.metadata:
            self.parse_metadata()
        if 'crossref_author' in self.metadata:
            return self.metadata['crossref_author']
        else:
            return None

    def get_title(self):
        """Get the title."""
        if not self.metadata:
            self.parse_metadata()
        if 'crossref_title' in self.metadata:
            return self.metadata['crossref_title']
        else:
            return None

    def get_type(self):
        """Get the type."""
        if not self.metadata:
            self.parse_metadata()
        if 'crossref_type' in self.metadata:
            return self.metadata['crossref_type']
        else:
            return None

    def get_DOI(self):
        """Get the DOI."""
        if not self.metadata:
            self.parse_metadata()
        if 'crossref_DOI' in self.metadata:
            return self.metadata['crossref_DOI']
        else:
            return None

    def get_URl(self):
        """Get URL based on DOI."""
        if not self.metadata:
            self.parse_metadata()
        if 'crossref_URL' in self.metadata:
            return self.metadata['crossref_URL']
        else:
            return None

    def get_publisher(self):
        """Get publisher."""
        if not self.metadata:
            self.parse_metadata()
        if 'crossref_publisher' in self.metadata:
            return self.metadata['crossref_publisher']
        else:
            return None

    def get_reference_count(self):
        """Get reference-count."""
        if not self.metadata:
            self.parse_metadata()
        if 'crossref_reference-count' in self.metadata:
            return self.metadata['crossref_reference-count']
        else:
            return None
