#!/usr/bin/env python
"""...
"""

import httplib
import json
import shutil
import tempfile
import random
import uuid

from keyczar import keyczar
from keyczar import keyczart
import requests
import tornado.httpserver
import tornado.netutil
import tornado.web

from tor_async_couchdb import async_model_actions
from tor_async_couchdb.model import Model

_database_url = r"http://127.0.0.1:5984/davewashere"

# curl http://127.0.0.1:5984/davewashere/_design/boo_by_boo_id/_view/boo_by_boo_id?include_docs=true
_design_doc_name = "boo_by_boo_id"
_design_doc = (
    '{'
    '    "language": "javascript",'
    '    "views": {'
    '        "%VIEW_NAME%": {'
    '            "map": "function(doc) { if (doc.type.match(/^boo_v1.0/i)) { emit(doc.boo_id) } }"'
    '        }'
    '    }'
    '}'
)
_design_doc = _design_doc.replace("%VIEW_NAME%", _design_doc_name)


class Boo(Model):

    def __init__(self, **kwargs):
        Model.__init__(self, **kwargs)

        if "doc" in kwargs:
            doc = kwargs["doc"]
            self.boo_id = doc["boo_id"]
            self.fruit = doc["fruit"]
            return

        self.boo_id = kwargs["boo_id"]
        self.fruit = type(self).get_random_fruit()

    def as_dict_for_store(self):
        rv = Model.as_dict_for_store(self)
        rv["type"] = "boo_v1.0"
        rv["boo_id"] = self.boo_id
        rv["fruit"] = self.fruit
        return rv

    @classmethod
    def get_random_fruit(cls, but_not_this_fruit=None):
        fruits = [
            "apple",
            "pear",
            "fig",
            "orange",
            "kiwi",
        ]
        while True:
            fruit = random.choice(fruits)
            if but_not_this_fruit is None:
                return fruit
            if but_not_this_fruit != fruit:
                return fruit


class AsyncBooPersister(async_model_actions.AsyncPersister):

    def __init__(self, boo, async_state=None):
        async_model_actions.AsyncPersister.__init__(self, boo, [], async_state)


class AsyncBooRetriever(async_model_actions.AsyncModelRetriever):

    def __init__(self, boo_id, async_state=None):
        async_model_actions.AsyncModelRetriever.__init__(
            self,
            "boo_by_boo_id",
            boo_id,
            async_state)

    def create_model_from_doc(self, doc):
        return Boo(doc=doc)


class AsyncBoosRetriever(async_model_actions.AsyncModelsRetriever):

    def __init__(self, async_state=None):
        async_model_actions.AsyncModelsRetriever.__init__(
            self,
            "boo_by_boo_id",
            async_state)

    def create_model_from_doc(self, doc):
        return Boo(doc=doc)


class RequestHandler(tornado.web.RequestHandler):
    """The ```TamperingIntegrationTestCase``` integration tests make
    async requests to this Tornado request handler which then calls
    the async model I/O classes to operate on persistent instances of
    Boo. Why is this request handler needed? The async model I/O
    classes need to operate in the context of a Tornado I/O loop.
    """

    post_url_spec = r"/boo/(.+)"

    @tornado.web.asynchronous
    def post(self, command):

        if command == "create":
            def on_persist_done(is_ok, is_conflict, ap):
                self.write(json.dumps(self._boo_as_dict(ap.model)))
                self.set_status(httplib.CREATED)
                self.finish()

            boo = Boo(boo_id=uuid.uuid4().hex)
            ap = AsyncBooPersister(boo)
            ap.persist(on_persist_done)
            return

        if command == "get":
            def on_fetch_done(is_ok, boo, abr):
                if boo is None:
                    self.set_status(httplib.NOT_FOUND)
                    self.finish()
                    return

                self.write(json.dumps(self._boo_as_dict(boo)))
                self.set_status(httplib.OK)
                self.finish()

            json_request_body = json.loads(self.request.body)
            boo_id = json_request_body.get("boo_id", None)
            assert boo_id is not None
            abr = AsyncBooRetriever(boo_id)
            abr.fetch(on_fetch_done)
            return

        if command == "get_all":
            def on_fetch_done(is_ok, boos, absr):
                assert boos is not None
                dicts = [self._boo_as_dict(boo) for boo in boos]
                self.write(json.dumps(dicts))
                self.set_status(httplib.OK)
                self.finish()

            absr = AsyncBoosRetriever()
            absr.fetch(on_fetch_done)
            return

        self.set_status(httplib.NOT_FOUND)
        self.finish()

    def _boo_as_dict(self, boo):
        return {
            "_id": boo._id,
            "_rev": boo._rev,
            "boo_id": boo.boo_id,
            "fruit": boo.fruit,
        }


if __name__ == "__main__":
    """Setup the integration tests environment. Specifically:

    -- create a temporary database including creating a design doc
    which permits reading persistant instances of Boo
    -- create a tampering signer
    -- configure the async model I/O classes to use the newly
    created tampering signer and temporary database

    """
    # in case a previous sample didn't clean itself up delete database
    # totally ignoring the result
    response = requests.delete(_database_url)
    # create database
    response = requests.put(_database_url)
    assert response.status_code == httplib.CREATED

    # install design doc
    url = "%s/_design/%s" % (_database_url, _design_doc_name)
    response = requests.put(
        url,
        data=_design_doc,
        headers={"Content-Type": "application/json; charset=utf8"})
    assert response.status_code == httplib.CREATED

    # create a tampering signer and get async_model_actions using it
    tampering_dir_name = tempfile.mkdtemp()

    keyczart.Create(
        tampering_dir_name,
        "some purpose",
        keyczart.keyinfo.SIGN_AND_VERIFY)
    keyczart.AddKey(
        tampering_dir_name,
        keyczart.keyinfo.PRIMARY)
    tampering_signer = keyczar.Signer.Read(tampering_dir_name)

    shutil.rmtree(tampering_dir_name, ignore_errors=True)

    # get async_model_actions using our temp database
    async_model_actions.database = _database_url

    # get async_model_actions using our tampering signer
    async_model_actions.tampering_signer = tampering_signer

    handlers = [
        (
            RequestHandler.post_url_spec,
            RequestHandler
        ),
    ]

    settings = {
    }

    app = tornado.web.Application(handlers=handlers, **settings)

    http_server = tornado.httpserver.HTTPServer(app, xheaders=True)
    http_server.listen(port=2525, address="127.0.0.1")

    tornado.ioloop.IOLoop.instance().start()
