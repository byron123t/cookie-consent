from urllib.parse import urlparse
import urllib.parse
import datetime


from consent.har.har_page import HarPage

class HAR:

    def __init__(self):
        self.har = {
            'log': {
                'version': '1.2',
                'creator': {
                    'name': 'Chrome HAR Capturer',
                    'version': '0.1',
                },
                'pages': [],
                'entries': []
            }
        }

    def from_page(self, page: HarPage):
        # // page timings
        if page.original_request_id is None: # in case of background pages. TODO: investigate the root causes.
            started_date_time = None
        else:
            wall_time = page.objects[page.original_request_id]['requestMessage']['wallTime']
            started_date_time = datetime.datetime.utcfromtimestamp(wall_time).isoformat() + 'Z'

        # import pdb; pdb.set_trace()

        on_content_load = page.dom_content_event_fired_ms - page.original_request_ms
        on_load = page.load_event_fired_ms - page.original_request_ms

        for request_id, obj in page.objects.items():
            try:
                self.populate_entry(page, obj)
            except Exception as e:
                print("Error populating an entry:", e)

        self.har['log']['pages'] = [{
            "startedDateTime": started_date_time,
            "id": str(page.id),
            "url": page.url,
            "title": "",
            "pageTimings": {
                "onContentLoad": on_content_load,
                "onLoad": on_load
            }
        }]

    def populate_entry(self, page, obj):
            # // skip incomplete entries, those that have no timing information (since
            # // it's optional) or data URI requests
            if obj.get('responseMessage') is None \
                or obj.get('responseMessage').get('response') is None \
                or obj.get('responseMessage').get('response').get('timing') is None \
                or obj.get('responseFinished') is None \
                or obj.get('responseMessage') is None \
                or obj.get('requestMessage').get('request') is None \
                or obj.get('requestMessage').get('request').get('url') is None \
                or obj.get('requestMessage').get('request').get('url').startswith('data:'):
                return

            # // check for redirections
            redirect_url = obj['requestMessage'].get('redirectResponse', {}).get('url', '')

            # // HTTP version or protocol name (e.g., quic)
            protocol = obj['responseMessage']['response'].get('protocol', 'unknown')

            # # // process headers
            request_headers = convert_headers(
                obj['responseMessage']['response'].get('requestHeaders', '') or obj['requestMessage']['request'].get('headers')
            )

            response_headers = convert_headers(obj['responseMessage']['response'].get('headers'))
            # // estimaate the header size according to the protocol
            if False: # protocol.startswith('http/1'): # TODO(duc): 'size' is missing for some headers, such as on google.com and searchpreview
                # // add status line length (12 = "HTTP/1.x" + "  " + "\r\n")
                request_headers['size'] += (len(obj['requestMessage']['request']['method']) +
                                        len(obj['requestMessage']['request']['url']) + 12)
                response_headers['size'] += (len(str(obj['responseMessage']['response']['status'])) +
                                         len(obj['responseMessage']['response']['statusText']) + 12)
            else:
                # // information not available due to possible compression newer
                # // versions of HTTP
                request_headers['size'] = -1
                response_headers['size'] = -1

            # // query string. # Duc: post-processor will process directly from URL.
            # query_string = convert_querystring(obj['requestMessage']['request']['url'])

            # // skip entries with no timing information (it's optional)
            timing = obj['responseMessage']['response'].get('timing')
            # if (!timing) continue

            # 'startedDateTime': new Date(obj['requestStarted'] * 1000).toISOString(),
            entry_started_date_time = datetime.datetime.utcfromtimestamp(obj['requestMessage'].get('wallTime')).isoformat() + 'Z'
            # print started_date_time, entry_started_date_time

            # // compute timing informations: input
            dns_time = time_delta(timing['dnsStart'], timing['dnsEnd'])
            proxy_time = time_delta(timing['proxyStart'], timing['proxyEnd'])
            connect_time = time_delta(timing['connectStart'], timing['connectEnd'])
            ssl_time = time_delta(timing['sslStart'], timing['sslEnd'])
            send_time = time_delta(timing['sendStart'], timing['sendEnd'])
            wait_time = timing['receiveHeadersEnd'] - timing['sendEnd']
            receive_time = round(obj['responseFinished'] * 1000 - timing['requestTime'] * 1000 - timing['receiveHeadersEnd'])
            blocked_time = -1

            # // compute timing informations: output
            dns = proxy_time + dns_time
            connect = connect_time
            ssl = ssl_time
            send = send_time
            wait = wait_time
            receive = receive_time
            blocked = blocked_time  # // TODO

            total_time = dns + connect + ssl + send + wait + receive

            # // connection information
            server_ip_address = obj['responseMessage']['response'].get('remoteIPAddress')
            connection = obj['responseMessage']['response'].get('connectionId')

            ## // sizes
            compression = obj['responseLength'] - obj['encodedResponseLength']

            # // fill entry
            self.har['log']['entries'].append({
                'pageref': str(page.id),
                'startedDateTime': entry_started_date_time,
                'time': total_time,
                'request': {
                    'method': obj['requestMessage']['request'].get('method'),
                    'url': obj['requestMessage']['request'].get('url'),
                    'httpVersion': protocol,
                    'cookies': obj['requestMessage'].get('associatedCookies'),
                    'headers': request_headers.get('pairs'),
                    # 'queryString': query_string,  # Duc: post-processor will process directly from URL.
                    'headersSize': request_headers.get('size'),
                    'bodySize': obj['requestMessage']['request']['headers'].get('Content-Length', -1),
                },
                'response': {
                    'status': obj['responseMessage']['response'].get('status'),
                    'statusText': obj['responseMessage']['response'].get('statusText'),
                    'httpVersion': protocol,
                    'cookies': None,
                    'headers': response_headers.get('pairs'),
                    'redirectURL': redirect_url,
                    'headersSize': response_headers.get('size'),
                    'bodySize': obj.get('encodedResponseLength'),
                    '_transferSize': obj.get('encodedResponseLength'),
                    'content': {
                        'size': obj.get('responseLength'),
                        'mimeType': obj['responseMessage']['response'].get('mimeType'),
                        'compression': compression,
                        'text': obj.get('responseBody', ''),
                        'encoding': '',  # TODO: 'encoding': object.responseBodyIsBase64 ? 'base64' : undefined,
                    }
                },
                'cache': {},
                'timings': {
                    'blocked': blocked_time,
                    'dns': dns_time,
                    'connect': connect_time,
                    'send': send_time,
                    'wait': wait_time,
                    'receive': receive_time,
                    'ssl': ssl_time
                },
                'serverIPAddress': server_ip_address,
                'connection': str(connection),
                # '_initiator': obj['requestMessage']['initiator'] # no need for ConsentChk
            })



def time_delta(start, end):
    if start != -1 and end != -1:
        return end - start
    return 0


def first_non_negative(values):
    for v in values:
        if v >= 0:
            return v
    return -1


def to_milliseconds(time):
    return -1 if time == -1 else time * 1000


def convert_querystring(full_url):
    r = urlparse(full_url)
    dikt = urllib.parse.parse_qs(r.query, keep_blank_values=True)
    return [{'name': k, 'value': ','.join(v)} for k, v in dikt.items()]


def convert_headers(headers):
    headers_obj = {'pairs': [], 'size': None}
    if headers:
        headers_obj['size'] = 2  # // trailing "\r\n"
        for name, value in headers.items():
            headers_obj['pairs'].append({'name': name, 'value': value})
            headers_obj['size'] += (len(name) + len(value) + 4)  # // ": " + "\r\n"
    return headers_obj
