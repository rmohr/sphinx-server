#
# Copyright 2013 Roman Mohr <roman@fenkhuber.at>
#
# This file is part of sphinx-server.
#
# sphinx-server is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Foobar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

import zipfile
try:
    from io import BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO
from cgi import parse_qs, escape, FieldStorage
import json
from os import path, mkdir, walk
import shutil
from static import Cling


class app:

    def __init__(self, home, password_file=None):
        self.home = home
        if not home:
            self.home = path.expanduser("~/sphinx-docs")
        if not path.exists(self.home):
            mkdir(self.home)
        self.static_app = Cling(self.home)

    def __call__(self, environ, start_response):
        location = environ["PATH_INFO"]
        if environ["REQUEST_METHOD"] == "POST":
            try:
                request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            except (ValueError):
                request_body_size = 0
            request_body = BytesIO(
                environ['wsgi.input'].read(request_body_size))
            sphinx_docu = FieldStorage(fp=request_body, environ=environ)
            if sphinx_docu.getvalue(":action") != "doc_upload":
                start_response('400 Bad Request', [])
                return [b""]
            stream = BytesIO(sphinx_docu.getvalue("content"))
            try:
                archive = zipfile.ZipFile(stream, "r")
            except zipfile.BadZipfile:
                start_response('400 File is not a zip file', [])
                return [b""]
            try:
                if archive.testzip():
                    start_response('400 Zip file is not sane', [])
                    return [b""]
            except ValueError:
                start_response('400 Unexpected end of Zipfile', [])
                return [b""]

            location = path.join(self.home, sphinx_docu.getvalue("name"))
            real_location = path.realpath(location)
            if not real_location.startswith(path.realpath(self.home)):
                start_response('404 Forbidden', [])
                return [b""]
            if path.exists(location):
                shutil.rmtree(location)
            archive.extractall(location)
            start_response('200 OK', [])
            return [b""]
        else:
            if location == "/":
                index = self._index()
                response_header = [('Content-Type', 'text/html'),
                                   ('Content-Length',
                                    str(len(index)))]
                start_response('200 OK', response_header)
                return [index.encode("utf-8")]
            else:
                return self.static_app(environ, start_response)

    def _index(self):
        index = ["<html><head><title>Index</title></head><body>\n"]
        for url in next(walk(self.home))[1]:
            index.append('<a href="%s">%s</a></br>\n' % (url, url))
        index.append("\n</body></html>")
        return "".join(index)
