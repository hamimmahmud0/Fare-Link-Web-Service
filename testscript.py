import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = os.environ.get('TEST_BASE_URL', 'http://127.0.0.1:5000')


def request_json(path, method='GET', data=None, query=None):
    url = BASE_URL + path
    headers = {}
    body = None

    if query:
        url += '?' + urllib.parse.urlencode(query)

    if data is not None:
        body = urllib.parse.urlencode(data).encode()
        headers['Content-Type'] = 'application/x-www-form-urlencoded'

    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode()
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            pass
        return exc.code, payload


def pretty(label, value):
    print(label)
    print(json.dumps(value, indent=2, sort_keys=True))


def main():
    user_id = f'test-user-{int(time.time())}'
    announce_payload = {
        'user-id': user_id,
        'access-link': 'https://example.test/contact',
        'visible': 'True',
        'expire': '0',
    }

    status, payload = request_json('/contacts/announce', method='POST', data=announce_payload)
    pretty('announce', {'status_code': status, 'payload': payload})

    status, payload = request_json('/contacts/search', method='GET', data={'user-id': user_id})
    pretty('search-after-announce', {'status_code': status, 'payload': payload})

    status, payload = request_json('/contacts/view', method='GET', query={'page': 1, 'limit': 10})
    pretty('view-after-announce', {'status_code': status, 'payload': payload})

    print('sleeping 65 seconds to allow scheduler cycle...')
    sys.stdout.flush()
    time.sleep(65)

    status, payload = request_json('/contacts/search', method='GET', data={'user-id': user_id})
    pretty('search-after-scheduler-wait', {'status_code': status, 'payload': payload})

    status, payload = request_json('/contacts/view', method='GET', query={'page': 1, 'limit': 10})
    pretty('view-after-scheduler-wait', {'status_code': status, 'payload': payload})


if __name__ == '__main__':
    main()
