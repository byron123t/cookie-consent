from collections import defaultdict
import random
import string

# https://chromium.googlesource.com/chromium/blink.git/+/master/Source/devtools/front_end/sdk/HAREntry.js
class HarPage:
    command_id = 200

    def __init__(self, _id):
        self.id = _id
        self._url = None

        self.failed = False
        self.original_request_id = None
        self.original_request_ms = 0
        self.dom_content_event_fired_ms = 0
        self.load_event_fired_ms = 0
        self.objects = defaultdict(dict)

    @property
    def finished(self):
        # TODO
        # // a page is considered "finished" either when is failed or when all these
        # // three messages arrived: a reply to the original request
        return self.failed or (self.original_request_ms is not None
                               and self.dom_content_event_fired_ms is not None
                               and self.load_event_fired_ms is not None)

    @property
    def url(self) -> str:
        return self._url

    @url.setter
    def url(self, url: str) -> None:
        self._url = url

    @property
    def next_command_id(self):
        self.command_id += 1
        return self.command_id

    def process_message(self, message, verbose=0):
        if verbose >= 3:
            print("## on process_message", message, type(message))
        method = message['method']
        domain = method.split('.')[0]
        if method == 'Page.domContentEventFired':
            self.dom_content_event_fired_ms = message['params']['timestamp'] * 1000
        elif method == 'Page.loadEventFired':
            self.load_event_fired_ms = message['params']['timestamp'] * 1000
        elif domain == 'Network':
            request_id = message['params'].get('requestId', 'default_request_id_' + ''.join(random.choices(string.ascii_lowercase, k=5)))
            if method == 'Network.requestWillBeSent':
                # // the first is the original request
                if self.original_request_id is None and message['params']['initiator']['type'] == 'other':
                    self.original_request_ms = message['params']['timestamp'] * 1000
                    self.original_request_id = request_id

                self.objects[request_id] = {
                    'requestMessage': message['params'],
                    'responseMessage': None,
                    'responseLength': 0,
                    'encodedResponseLength': 0,
                    'responseFinished': None,
                    'responseBody': None,
                    'responseBodyIsBase64': None
                }
            elif method == 'Network.requestWillBeSentExtraInfo':
                request_msg = self.objects[request_id].get('requestMessage')
                if request_msg is not None:
                    request_msg['associatedCookies'] = message['params']['associatedCookies']
            elif method == 'Network.dataReceived':
                if request_id in self.objects:
                    # TODO: should we accumulate or set a new value? original: accumalate
                    self.objects[request_id]['dataLength'] = self.objects[request_id].get(
                        'dataLength', 0) + message['params']['dataLength']
                    self.objects[request_id]['encodedDataLength'] = self.objects[request_id].get(
                        'encodedDataLength', 0) + message['params']['encodedDataLength']
            elif method == 'Network.responseReceived':
                if request_id in self.objects:
                    self.objects[request_id]['responseMessage'] = message['params']
            elif method == 'Network.loadingFinished':
                if request_id in self.objects:
                    self.objects[request_id]['responseFinished'] = message['params']['timestamp']
                    # // asynchronously fetch the request body (no check is
                    # // performed to really ensure that the fetching is over
                    # // before finishing this page processing because there is
                    # // the PAGE_DELAY timeout anyway; it should not be a problem...)

                    # if self.fetch_content:
                    #     # import pdb; pdb.set_trace()
                    #     params = {'requestId': request_id}
                    #     response = self.call_command(method='Network.getResponseBody', params=params)
                    #     # print "#### HWRE", response
                    #     self.objects[request_id]['responseBody'] = response['body']
                    #     self.objects[request_id]['responseBodyIsBase64'] = response['base64Encoded']

                    # if (self.fetchContent) {
                    #     self.chrome.Network.getResponseBody({'requestId': id}, function (error, response) {
                    #         if (!error) {
                    #             self.objects[id].responseBody = response.body;
                    #             self.objects[id].responseBodyIsBase64 = response.base64Encoded;
                    #         }
                    #     });
                    # }
            elif method == 'Network.loadingFailed':
                # // failure of the original request aborts the whole page
                if request_id == self.original_request_id:
                    self.failed = True

            if verbose >= 2:
                if request_id is None:
                    print('<-- ' + method + ': ' + self.url)
                else:
                    print('<-- ' + '[' + request_id + '] ' + method)
