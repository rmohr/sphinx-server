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
import StringIO
from cgi import parse_qs, escape, FieldStorage
import json
from os import path, mkdir
import shutil
from static import Shock


class app:

    def __init__(self, home, password_file=None):
        self.home = home
        if not home:
            self.nome = path.expanduser("~/sphinx-docs")
        if not path.exists(self.home):
            mkdir(self.home)
        self.static_app = Shock(self.home)

    def __call__(self, environ, start_response):
        status = '200 OK'
        location = environ["PATH_INFO"]
        if environ["REQUEST_METHOD"] == "POST":
            try:
                request_body_size = int(environ.get('CONTENT_LENGTH', 0))
            except (ValueError):
                request_body_size = 0
            request_body = StringIO.StringIO(
                environ['wsgi.input'].read(request_body_size))
            sphinx_docu = FieldStorage(fp=request_body, environ=environ)
            if sphinx_docu.getvalue(":action") != "doc_upload":
                start_response('400 Bad Request', [])
                return ""
            stream = StringIO.StringIO(sphinx_docu.getvalue("content"))
            archive = zipfile.ZipFile(stream, "r")
            location = path.join(self.home, sphinx_docu.getvalue("name"))
            real_location = path.realpath(location)
            if not real_location.startswith(path.realpath(self.home)):
                start_response('404 Forbidden', [])
                return ""
            if path.exists(location):
                shutil.rmtree(location)
            archive.extractall(location)
            start_response('200 OK', [])
            return ""
        else:
            return self.static_app(environ, start_response)
