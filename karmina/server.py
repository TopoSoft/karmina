"""Loopback-only development server. Not a production authentication boundary."""
import argparse
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from .studio import AGENTS, Studio, StudioError

WEB = Path(__file__).parent / 'web'
LOCAL_TENANT = 'local-director'


def make_server(path, port=8787):
    studio = Studio(path)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def send(self, status, body, content_type='application/json; charset=utf-8'):
            if not isinstance(body, bytes):
                body = json.dumps(body, ensure_ascii=False).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def guard(self):
            host = f'127.0.0.1:{self.server.server_port}'
            if self.headers.get('Host') != host:
                raise StudioError('forbidden', 403)
            origin = self.headers.get('Origin')
            if origin and origin != f'http://{host}':
                raise StudioError('forbidden', 403)
            if self.headers.get('Sec-Fetch-Site') == 'cross-site':
                raise StudioError('forbidden', 403)

        def body(self):
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                raise StudioError('invalid_input', 415)
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 100000:
                    raise StudioError('invalid_input', 413)
                result = json.loads(self.rfile.read(length))
            except (ValueError, UnicodeError):
                raise StudioError('invalid_input') from None
            if not isinstance(result, dict):
                raise StudioError('invalid_input')
            return result

        def dispatch(self):
            try:
                self.guard()
                path = urlsplit(self.path).path
                if self.command == 'GET' and path in ('/', '/app.js', '/style.css', '/i18n.js'):
                    name = 'index.html' if path == '/' else path[1:]
                    kind = {'html': 'text/html', 'js': 'text/javascript', 'css': 'text/css'}[name.rsplit('.', 1)[1]]
                    return self.send(200, (WEB / name).read_bytes(), kind + '; charset=utf-8')
                if self.command == 'GET' and path == '/api/config':
                    return self.send(200, {'agents': AGENTS, 'runtime': 'local_template', 'ohagent_available': False, 'authentication': 'loopback_single_user', 'media_generation': False})
                if path == '/api/projects':
                    if self.command == 'GET':
                        return self.send(200, {'projects': studio.list(LOCAL_TENANT)})
                    return self.send(201, studio.create(LOCAL_TENANT, self.body()))
                parts = path.strip('/').split('/')
                if len(parts) >= 3 and parts[:2] == ['api', 'projects']:
                    project_id = parts[2]
                    if self.command == 'GET' and len(parts) == 3:
                        return self.send(200, studio.get(LOCAL_TENANT, project_id))
                    if self.command == 'GET' and len(parts) == 4 and parts[3] == 'export':
                        return self.send(200, studio.export(LOCAL_TENANT, project_id))
                    if self.command == 'POST' and len(parts) == 6 and parts[3] == 'steps':
                        data = self.body()
                        if set(data) - {'version', 'content', 'runtime'}:
                            raise StudioError('invalid_input')
                        if parts[5] == 'draft':
                            return self.send(200, studio.draft(LOCAL_TENANT, project_id, parts[4], data.get('version'), data.get('content'), data.get('runtime', 'local_template')))
                        if parts[5] == 'approve':
                            return self.send(200, studio.approve(LOCAL_TENANT, project_id, parts[4], data.get('version')))
                raise StudioError('not_found', 404)
            except StudioError as error:
                self.send(error.status, {'error': error.code})
            except Exception:
                self.send(500, {'error': 'internal_error'})

        do_GET = dispatch
        do_POST = dispatch

    server = ThreadingHTTPServer(('127.0.0.1', port), Handler)
    server.daemon_threads = True
    return server


def main():
    parser = argparse.ArgumentParser(description='Karmina local development studio')
    parser.add_argument('--port', type=int, default=8787)
    parser.add_argument('--database', default=os.environ.get('KARMINA_DATABASE', 'data/studio.sqlite3'))
    args = parser.parse_args()
    server = make_server(args.database, args.port)
    print(f'Karmina: http://127.0.0.1:{server.server_port} (local templates, no AI calls)', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
