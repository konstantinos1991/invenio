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


from .extractors import (
    CrossRefExtractor,
    DoiExtractor,
    XmpExtractor
)
from text_reader import TextReader
from validation import CrossrefDoiValidation


class MetadataExtraction(object):

    """Metadata extraction."""

    def __init__(self, file_path):
        """Initialization.

        :param file_path: a file's absolute path
        """
        self.file_path = file_path
        self.xmp_extractor = XmpExtractor(full_file_path=file_path)
        self.xmp_metadata = {}
        self.crossref_extractor = None
        self.crossref_metadata = {}
        self.text_reader = TextReader(self.file_path)

    def _mine_pdf_file(self):
        if self.text_reader.can_open_file() is True:
                lines = self.text_reader.get_lines()
                doi_extractor = DoiExtractor(lines, 5000)
                doi = doi_extractor.get_possible_doi()
                # if doi is not none
                if doi:
                    self.crossref_extractor = CrossRefExtractor(doi=doi)
                    if self.crossref_extractor.problem_with_connection() is False:
                        self.crossref_metadata = self.crossref_extractor.parse_metadata()
                        # validate the meta-data
                        validation = CrossrefDoiValidation(
                            lines, self.crossref_metadata, 0.8
                        )
                        if validation.validate() is True:
                            return self.crossref_metadata
                        else:
                            return {}
                    else:
                        return {}
                else:
                    return {}
        else:
            return {}

    def _extract(self):
        """The Metadata extraction algorithm."""
        if self.xmp_extractor.can_open_file() is True:
            self.xmp_metadata = self.xmp_extractor.parse_metadata()
            if self.xmp_extractor.doi_is_present() is True:
                doi = self.xmp_extractor.get_doi()
                self.crossref_extractor = CrossRefExtractor(doi=doi)
                if self.crossref_extractor.problem_with_connection() is False:
                    self.crossref_metadata = self.crossref_extractor.parse_metadata()
                    return self.crossref_metadata
                else:
                    return {}
            else:
                return self._mine_pdf_file()
        else:
            return self._mine_pdf_file()

    def get_metadata(self):
        metadata = self._extract()
        if 'crossref_DOI' in metadata:
            metadata['doi'] = metadata['crossref_DOI']
            del metadata['crossref_DOI']
        if 'crossref_title' in metadata:
            metadata['title'] = metadata['crossref_title']
            del metadata['crossref_title']
        if 'crossref_author' in metadata:
            metadata['author'] = metadata['crossref_author']
            del metadata['crossref_author']
        if 'crossref_subject' in metadata:
                metadata['subject'] = metadata['crossref_subject']
                del metadata['crossref_subject']
        if 'crossref_publisher' in metadata:
            metadata['publisher'] = metadata['crossref_publisher']
            del metadata['crossref_publisher']
        if 'crossref_type' in metadata:
            metadata['type'] = metadata['crossref_type']
            del metadata['crossref_type']
        if 'crossref_issue' in metadata:
            metadata['issue'] = metadata['crossref_issue']
            del metadata['crossref_issue']
        if 'crossref_ISSN' in metadata:
            metadata['issn'] = metadata['crossref_ISSN']
            del metadata['crossref_ISSN']
        if 'crossref_reference-count':
            metadata['reference-count'] = metadata['crossref_reference-count']
            del metadata['crossref_reference-count']
        return metadata
