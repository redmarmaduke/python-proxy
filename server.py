import os

from dotenv import load_dotenv
from flask import Flask, request, Response
# https://requests.readthedocs.io/en/latest/
import requests

load_dotenv()
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')

app = Flask(__name__,
            static_url_path = None,
            static_folder = "static",
            static_host = None,
            host_matching = False,
            subdomain_matching = False,
            template_folder = "templates",
            instance_path = None,
            instance_relative_config=None,
            root_path=None)

# target: 'https://api.github.com', // target host
# changeOrigin: true, // needed for virtual hosted sites
# // add request header 'Authorization'
# headers: {
#   Authorization: `Bearer ${GITHUB_TOKEN}`,
# },
# // rewrite the protocol from http to https
# protocolRewrite: 'https',
# // we want to verify the ssl certs
# secure: true,

# ref https://medium.com/@zwork101/making-a-flask-proxy-server-online-in-10-lines-of-code-44b8721bca6

@app.route('/graphql', defaults={'path': ''}, methods=["GET", "POST"])
def graphql(path):
    target = 'https://api.github.com/'

    # remove host and add Authorization
    headers = {k:v for k,v in request.headers if k.lower() != 'host'}
    headers['Authorization'] = f'Bearer {GITHUB_TOKEN}'

    target_res = requests.request(
        # use client request method
        method = request.method,
        # replace url with target url
        url = request.url.replace(request.host_url, target),
        params = None,
        data = request.get_data(),
        headers = headers,
        cookies = request.cookies,
        files = None,
        auth = None,
        timeout = None,
        allow_redirects = False,
        proxies = None,
        hooks = None,
        stream = True,
        verify = None,
        cert = None,
        json = None,
    )

    # remove hop by hop headers ref https://www.rfc-editor.org/rfc/rfc2616#section-13.5.1
    # strip out hop by hop headers as it should be done by a proxy server
    hop_by_hop_headers = [
      'Connection',
      'Keep-Alive',
      'Proxy-Authenticate',
      'Proxy-Authorization',     
      'TE',
      'Trailers',
      'Transfer-Encoding',
      'Upgrade'
    ]
    # strip out Content-Encoding since flask decompresses data
    encoding_headers = [
        'Content-Encoding'
    ]

    headers_to_strip = hop_by_hop_headers + encoding_headers

    headers_to_strip = list(map(lambda x : x.lower(), headers_to_strip))

    # headers must be an array of tuples or mapping and not a dict
    headers = [ (k,v) for k,v in target_res.raw.headers.items() if k.lower() not in headers_to_strip ]
    content_type = target_res.raw.headers['Content-Type']

    def generate():
        for chunk in target_res.iter_content(8192, False):
            yield chunk
    res = Response(generate(), target_res.status_code, headers, 
                   content_type=content_type, direct_passthrough=False)
    return res

@app.route('/', defaults={'path': ''}, methods=["GET", "POST"])
@app.route('/<path>', methods=["GET", "POST"])
def default(path):
    return '<p>default</p>'
