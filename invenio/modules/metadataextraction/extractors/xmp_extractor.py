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


from libxmp.consts import XMP_NS_DC
from libxmp import XMPFiles


class XmpExtractor(object):

    """Extract metadata from XMP."""

    def __init__(self, full_file_path):
        """Initialization."""
        try:
            # boolean to note if xmp is None
            self.is_xmp_none = False
            self.xmp_file = XMPFiles(file_path=full_file_path)
            if not self.xmp_file:
                # xmp will be None
                self.is_xmp_none = True
            self.xmp = self.xmp_file.get_xmp()
            if not self.xmp:
                # xmp will be None
                self.is_xmp_none = True
            self.metadata = {}
        except UnicodeDecodeError:
            self.xmp = None
            self.is_xmp_none = True

    def can_open_file(self):
        """Return true if XMP can open the file."""
        if self.is_xmp_none:
            return False
        return True

    def __parse_dc_metadata(self):
        """Parse Dublin core schema fields."""
        # parse identifier
        if self.xmp.does_property_exist(XMP_NS_DC, "identifier"):
            dc_identifier = self.xmp.get_property(XMP_NS_DC, "identifier")
            if not isinstance(dc_identifier, unicode):
                dc_identifier = dc_identifier.decode('utf8')
            self.metadata["dc_identifier"] = dc_identifier
        # parse title
        if self.xmp.does_property_exist(XMP_NS_DC, "title"):
            title_num = self.xmp.count_array_items(XMP_NS_DC, "title")
            # maybe the following if is not needed
            if title_num == 1:
                dc_title = self.xmp.get_array_item(
                    XMP_NS_DC, "title", title_num)
                if not isinstance(dc_title, unicode):
                    dc_title = dc_title.decoce('uf8')
                self.metadata['dc_title'] = dc_title
        # parse subject , a list of keywords
        if self.xmp.does_property_exist(XMP_NS_DC, "subject"):
            keywords_num = self.xmp.count_array_items(XMP_NS_DC, "subject")
            # a list to store keywords about document's subject
            keywords = []
            for i in range(1, keywords_num+1):
                keyword = self.xmp.get_array_item(XMP_NS_DC, "subject", i)
                if not isinstance(keyword, unicode):
                    keyword = keyword.decode('utf8')
                keywords.append(keyword)
            self.metadata['dc_subject'] = keywords
        # parse description
        if self.xmp.does_property_exist(XMP_NS_DC, "description"):
            description_num = self.xmp.count_array_items(
                XMP_NS_DC, "description")
            if description_num == 1:
                dc_description = self.xmp.get_array_item(
                    XMP_NS_DC, "description", description_num)
                if not isinstance(dc_description, unicode):
                    dc_description = dc_description.decode('utf8')
                self.metadata['dc_description'] = dc_description
        # parse creator
        if self.xmp.does_property_exist(XMP_NS_DC, "creator"):
            creators_num = self.xmp.count_array_items(XMP_NS_DC, "creator")
            # a list to store authors names
            creators = []
            for i in range(1, creators_num+1):
                creator = self.xmp.get_array_item(XMP_NS_DC, "creator", i)
                if not isinstance(creator, unicode):
                    creator = creator.decode('utf8')
                creators.append(creator)
            self.metadata['dc_creator'] = creators
        # parse publisher
        if self.xmp.does_property_exist(XMP_NS_DC, "publisher"):
            publishers_num = self.xmp.count_array_items(XMP_NS_DC, "publisher")
            # a list to store publishers
            publishers = []
            for i in range(1, publishers_num+1):
                publisher = self.xmp.get_array_item(XMP_NS_DC, "publisher", i)
                if not isinstance(publisher, unicode):
                    publisher = publisher.decode('utf8')
                publishers.append(publisher)
            self.metadata['dc_publisher'] = publishers
        # parse rights
        if self.xmp.does_property_exist(XMP_NS_DC, "rights"):
            rights_num = self.xmp.count_array_items(XMP_NS_DC, "rights")
            # a list to store rights
            rights = []
            for i in range(1, rights_num+1):
                right = self.xmp.get_array_item(XMP_NS_DC, "rights", i)
                if not isinstance(right, unicode):
                    right = right.decode('utf8')
                rights.append(right)
            self.metadata['dc_rights'] = rights
        # parse language
        if self.xmp.does_property_exist(XMP_NS_DC, "language"):
            language_num = self.xmp.count_array_items(XMP_NS_DC, "language")
            # a list to store languages
            languages = []
            for i in range(1, language_num+1):
                lang = self.xmp.get_array_item(XMP_NS_DC, "language", i)
                if not isinstance(lang, unicode):
                    lang = lang.decode('utf8')
                languages.append(lang)
            self.metadata['dc_language'] = languages

    def __parse_prism_metadata(self):
        """Parse prism fields."""
        XMP_NS_PRISM = 'http://prismstandard.org/namespaces/basic/2.0/'
        # parse doi
        if self.xmp.does_property_exist(XMP_NS_PRISM, "doi"):
            prism_doi = self.xmp.get_property(XMP_NS_PRISM, "doi")
            if not isinstance(prism_doi, unicode):
                prism_doi = prism_doi.decode('utf8')
            self.metadata['prism_doi'] = prism_doi
        # parse publicationName
        if self.xmp.does_property_exist(XMP_NS_PRISM, "publicationName"):
            pub_name = self.xmp.get_property(XMP_NS_PRISM, "publicationName")
            if not isinstance(pub_name, unicode):
                pub_name = pub_name.decode('utf8')
            self.metadata['prism_publicationName'] = pub_name
        # parse copyright
        if self.xmp.does_property_exist(XMP_NS_PRISM, "copyright"):
            prism_copyright = self.xmp.get_property(XMP_NS_PRISM, "copyright")
            if not isinstance(prism_copyright, unicode):
                prism_copyright = prism_copyright.decode('utf8')
            self.metadata['prism_copyright'] = prism_copyright
        # parse distributor
        if self.xmp.does_property_exist(XMP_NS_PRISM, "distributor"):
            prism_distributor = self.xmp.get_property(
                XMP_NS_PRISM, "distributor")
            if not isinstance(prism_distributor, unicode):
                prism_distributor = prism_distributor.decode('utf8')
            self.metadata['prism_distributor'] = prism_distributor
        # parse eIssn
        if self.xmp.does_property_exist(XMP_NS_PRISM, "eIssn"):
            prism_eissn = self.xmp.get_property(XMP_NS_PRISM, "eIssn")
            if not isinstance(prism_eissn, unicode):
                prism_eissn = prism_eissn.decode('utf8')
            self.metadata['prism_eIssn'] = prism_eissn
        # parse issn
        if self.xmp.does_property_exist(XMP_NS_PRISM, "issn"):
            prism_issn = self.xmp.get_property(XMP_NS_PRISM, "issn")
            if not isinstance(prism_issn, unicode):
                prism_issn = prism_issn.decode('utf8')
            self.metadata['prism_issn'] = prism_issn
        # parse isbn
        if self.xmp.does_property_exist(XMP_NS_PRISM, "isbn"):
            prism_isbn = self.xmp.get_property(XMP_NS_PRISM, "isbn")
            if not isinstance(prism_isbn, unicode):
                prism_isbn = prism_isbn.decode('utf8')
            self.metadata['prism_isbn'] = prism_isbn

    def parse_metadata(self):
        """Parse metadata from the XMP structure."""
        # if xmp is not none get metadata
        if self.is_xmp_none:
            return {}
        else:
            # parse dc fields
            self.__parse_dc_metadata()
            # parse prism fields
            self.__parse_prism_metadata()
            # close xmp structure
            self.xmp_file.close_file()
            # del self.xmp
            return self.metadata

    def doi_is_present(self):
        """Return true if doi is present in the XMP structure.

        Must be called after the parse_metadata is called.
        """
        if 'prism_doi' in self.metadata:
            return True
        if ('dc_identifier' in self.metadata) and \
           ('prism_doi' not in self.metadata):
            return True
        if ('dc_identifier' not in self.metadata) and \
           ('prism_doi' not in self.metadata):
            return False

    def get_doi(self):
        """Return a doi if it is present."""
        if self.doi_is_present() is False:
            return None
        else:
            if 'prism_doi' in self.metadata:
                return self.metadata['prism_doi']
            if ('dc_identifier' in self.metadata) and \
               ('prism_doi' not in self.metadata):
                return self.metadata['dc_identifier']

    def get_xmp_metadata(self):
        self.parse_metadata()
        if not self.metadata:
            return {}
        else:
            xmp_metadata = {}
            if self.doi_is_present() is True:
                xmp_metadata['xmp_doi'] = self.get_doi()
            if 'dc_title' in self.metadata:
                xmp_metadata['xmp_title'] = self.metadata['dc_title']
            # subject is a list of words
            if 'dc_subject' in self.metadata:
                xmp_metadata['xmp_subject'] = self.metadata['dc_subject']
            if 'dc_description' in self.metadata:
                xmp_metadata['xmp_description'] = self.metadata['dc_description']
            # creator is a list of strings
            if 'dc_creator' in self.metadata:
                xmp_metadata['xmp_creator'] = self.metadata['dc_creator']
            if 'dc_publisher' in self.metadata:
                xmp_metadata['xmp_publisher'] = self.metadata['xmp_publisher']
            elif ('dc_publisher' not in self.metadata and
                  'prism_publicationName' in self.metadata):
                xmp_metadata['xmp_publisher'] = self.metadata['prism_publicationName']
            if 'prism_distributor' in self.metadata:
                xmp_metadata['xmp_distributor'] = self.metadata['prism_distributor']
            if 'dc_rights' in self.metadata:
                xmp_metadata['xmp_rights'] = self.metadata['dc_rights']
            if 'prism_copyright' in self.metadata:
                xmp_metadata['xmp_copyright'] = self.metadata['prism_copyright']
            if 'prism_eIssn' in self.metadata:
                xmp_metadata['xmp_eIssn'] = self.metadata['prism_eIssn']
            if 'prism_issn' in self.metadata:
                xmp_metadata['xmp_issn'] = self.metadata['prism_issn']
            if 'prism_isbn' in self.metadata:
                xmp_metadata['xmp_isbn'] = self.metadata['prism_isbn']
            if 'dc_language' in self.metadata:
                xmp_metadata['xmp_language'] = self.metadata['dc_language']
            return xmp_metadata
