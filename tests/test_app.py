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

import pytest
import webtest
from webtest.forms import Form
from static import Shock
from zipfile import ZipFile
import os


@pytest.fixture
def app(tmpdir):
    from sphinxserver import app
    return app(home=tmpdir.strpath)


@pytest.fixture
def testapp(app):
    return webtest.TestApp(app)


def test_nozip_upload(testapp, tmpdir):
    tmpfile = tmpdir.join("test.txt")
    tmpfile.write("test")
    res = testapp.post("/", {':action': 'doc_upload', 'name': 'test.txt'},
                       upload_files=[("content", tmpfile.strpath)], status=400)


def test_zip_upload(testapp, tmpdir):
    os.chdir(tmpdir.strpath)
    tmpfile = tmpdir.join("test.txt")
    tmpfile.write("hello world\n")
    zf = tmpdir.join("test.zip").strpath
    zipfile = ZipFile(zf, 'w')
    try:
        zipfile.write("test.txt")
    except:
        zipfile.close()
        raise
    zipfile.close()
    res = testapp.post(
        "/", {':action': 'doc_upload', 'name': 'test'}, upload_files=[("content", zf)])
    assert "test" in testapp.get("/")
    assert "hello world" in testapp.get("/test/test.txt")
