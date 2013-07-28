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
from zipfile import ZipFile
import os


@pytest.fixture
def app(tmpdir):
    from sphinxserver import app
    return app(home=tmpdir.join("root").strpath)


@pytest.fixture
def testapp(app):
    return webtest.TestApp(app)


def simple_zip(tmpdir):
    os.chdir(tmpdir.strpath)
    tmpfile = tmpdir.join("test.txt")
    tmpfile.write("hello world\n")
    zipfile_path = tmpdir.join("test.zip").strpath
    zipfile = ZipFile(zipfile_path, 'w')
    try:
        zipfile.write("test.txt")
    except:
        zipfile.close()
        raise
    zipfile.close()
    return zipfile_path


def test_bad_request(testapp):
    res = testapp.post("/", {':action': 'doc_uploadXXX', 'name': 'test.txt'},
                       upload_files=[("content", "test.zip", b"hello world")], status=400)
    assert "Bad Request" in str(res)


def test_nozip_upload(testapp, tmpdir):
    tmpfile = tmpdir.join("test.txt")
    tmpfile.write("test")
    res = testapp.post("/", {':action': 'doc_upload', 'name': 'test.txt'},
                       upload_files=[("content", tmpfile.strpath)], status=400)
    assert "not a zip file" in str(res)
    assert "test" not in testapp.get("/")


def test_invalid_zip_upload(testapp, tmpdir):
    zipfile = simple_zip(tmpdir)
    stream = open(zipfile, 'rb')
    content = stream.read()
    if type(content) != type(""): #python3
        faulty_char = content[0] + 1
        content = list(content)
        content[0] = faulty_char
        content = bytes(content)
    else: #python2
        faulty_char = chr(ord(content[0])+1)
        content = list(content)
        content[0] = faulty_char
        content = ''.join(content)
    res = testapp.post(
        "/", {':action': 'doc_upload', 'name': 'test'},
        upload_files=[("content", zipfile, content)], status=400)
    assert "not sane" in str(res)
    assert "test" not in testapp.get("/")


def test_too_short_zip_upload(testapp, tmpdir):
    zipfile = simple_zip(tmpdir)
    stream = open(zipfile, 'rb')
    content = stream.read()
    content = content[1:]
    res = testapp.post(
        "/", {':action': 'doc_upload', 'name': 'test'},
        upload_files=[("content", zipfile, content)], status=400)
    assert "Unexpected end" in str(res)
    assert "test" not in testapp.get("/")


def test_zip_upload(testapp, tmpdir):
    zipfile = simple_zip(tmpdir)
    res = testapp.post(
        "/", {':action': 'doc_upload', 'name': 'test'},
        upload_files=[("content", zipfile)])
    assert "test" in testapp.get("/")
    assert "hello world" in testapp.get("/test/test.txt")


def test_app_factory():
    from sphinxserver import app_factory
    app = app_factory(None, home="~/")
    testapp = webtest.TestApp(app)
    testapp.get("/")
