from datetime import datetime

from twisted.internet import reactor, protocol
from twisted.trial import unittest
from twistedfcp.protocol import (FreenetClientProtocol, IdentifiedMessage, 
                                 logging)
from twistedfcp.util import sequence

logging.basicConfig(filename="twistedfcp.log", level=logging.DEBUG)

def withClient(f):
    "Obtains a client and passes it to the wrapped function as an argument."
    def _inner(self):
        creator = protocol.ClientCreator(reactor, FreenetClientProtocol)
        def cb(client):
            self.client = client
            return f(self, client)
        defer = creator.connectTCP('localhost', FreenetClientProtocol.port)
        return defer.addCallback(cb)
    return _inner

class FCPBaseTest(unittest.TestCase):
    "We always want to clean up after the test is done."
    def tearDown(self):
        if self.client is not None:
            self.client.transport.loseConnection()

class ClientHelloTest(FCPBaseTest):
    "Tests that the Freenet node responds to a ClientHello message."
    @withClient
    @sequence
    def test_hello(self, client):
        msg = yield client.deferred['NodeHello']
        self.assertEquals(msg['FCPVersion'], '2.0')

class GetPutTest(FCPBaseTest):
    "Tests get/put messages to the Freenet node."

    def __init__(self, *args):
        FCPBaseTest.__init__(self, *args)
        self.timeout = 60 * 60

    @withClient
    @sequence
    def test_ksk(self, client):
        _ = yield client.deferred['NodeHello']
        now = datetime.now()
        uri = "KSK@" + now.strftime("%Y-%m-%d-%H-%M")
        # First put.
        testdata = "Testing 123..."
        put = IdentifiedMessage("ClientPut", [("Verbosity", 1), ("URI", uri)])
        client.sendMessage(put, data=testdata)
        response = yield client.deferred["PutSuccessful"]
        self.assertEqual(response["Identifier"], put["Identifier"])
        # Then get.
        response = yield client.get_direct(uri)
        # Finally check the data.
        self.assertEqual(response["Data"], testdata)

