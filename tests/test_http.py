import http.client
import json
import tempfile
import threading
import unittest
from pathlib import Path

from karmina.server import make_server


class HttpTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.server = make_server(Path(self.tmp.name) / 'http.sqlite3', 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.tmp.cleanup()

    def request(self, method, path, data=None, headers=None):
        conn = http.client.HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        payload = None if data is None else json.dumps(data)
        conn.request(method, path, payload, {'Content-Type': 'application/json', **(headers or {})})
        response = conn.getresponse()
        body = response.read()
        status, result_headers = response.status, dict(response.getheaders())
        conn.close()
        return status, body, result_headers

    def test_static_config_and_request_security(self):
        for path in ['/', '/app.js', '/i18n.js', '/style.css']:
            status, body, headers = self.request('GET', path)
            self.assertEqual(status, 200)
            self.assertTrue(body)
            self.assertIn("frame-ancestors 'none'", headers['Content-Security-Policy'])
        config = json.loads(self.request('GET', '/api/config')[1])
        self.assertFalse(config['ohagent_available'])
        self.assertFalse(config['media_generation'])
        for headers in [{'Host': 'evil.example'}, {'Origin': 'https://evil.example'}, {'Sec-Fetch-Site': 'cross-site'}]:
            self.assertEqual(self.request('POST', '/api/projects', {}, headers)[0], 403)
        for data in [[], None, {'tenant_id': 'foreign'}]:
            self.assertEqual(self.request('POST', '/api/projects', data)[0], 400 if data is not None else 413)
        self.assertEqual(self.request('POST', '/api/projects', {}, {'Content-Type': 'text/plain'})[0], 415)
        self.assertEqual(self.request('GET', '/../../etc/passwd')[0], 404)

    def test_real_http_pipeline_and_error_codes(self):
        status, body, _ = self.request('POST', '/api/projects', {'title': 'Cinema', 'brief': 'A fictional story.', 'mode': 'photorealistic', 'language': 'lv'})
        self.assertEqual(status, 201)
        p = json.loads(body)
        base = f"/api/projects/{p['id']}"
        self.assertEqual(json.loads(self.request('GET', '/api/projects')[1])['projects'][0]['id'], p['id'])
        self.assertEqual(self.request('GET', base)[0], 200)
        self.assertEqual(self.request('GET', base + '/export')[0], 409)
        for role in ['producer', 'writer', 'art_director', 'director', 'sound_designer', 'reviewer']:
            for action in ['draft', 'approve']:
                status, body, _ = self.request('POST', f'{base}/steps/{role}/{action}', {'version': p['version']})
                self.assertEqual(status, 200, body)
                p = json.loads(body)
        pack = json.loads(self.request('GET', base + '/export')[1])
        self.assertFalse(pack['media_generated'])
        self.assertEqual(len(pack['artifacts']), 6)
        self.assertEqual(self.request('GET', '/api/projects/missing')[0], 404)
        self.assertEqual(self.request('POST', base + '/steps/producer/draft', {'version': 0})[0], 409)
        self.assertEqual(self.request('POST', base + '/steps/producer/draft', {'version': 12, 'runtime': 'ohagent'})[0], 503)


if __name__ == '__main__':
    unittest.main()
