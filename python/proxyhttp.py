
import requests
from flask import Flask, Response, request
from urllib.parse import urlparse, quote

##########################################################################################################
##########################################################################################################
##########################################################################################################
HOST = '0.0.0.0'  # 监听地址，建议监听本地然后由web服务器反代
PORT = 8989  # 监听端口

request_header = [
    'Host', 'Referer', "Authorization", "Accept", "Cookie", "Content-Type",
    "If-None-Match", "If-Modified-Since", "Date", 'User-Agent', 'Encrypt'
]
response_header = [
    "Location", "Set-Cookie", "Content-Type", "Cache-Control", "ETag",
    "Access-Control-Allow-Origin", "Date", "Age", "Via", "Server",
    "Encrypt"
]
proxies = {'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}

##########################################################################################################
##########################################################################################################
##########################################################################################################



app = Flask(__name__)
CHUNK_SIZE = 1024 * 10


# 以下配置用于仅ipv4连接
# import socket
# old_getaddrinfo = socket.getaddrinfo
# def str_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
#     return old_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
# 
# socket.getaddrinfo = str_getaddrinfo

# def generate():
#     for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
#         yield chunk
# return Response(generate(), headers=headers, status=r.status_code)

def buildRequestHeaders(originHeaders, host):
    r_headers = {}
    for i, v in originHeaders:
        if i in request_header:
            r_headers[i] = v
            continue
    return r_headers

def buildResonseHeaders(originHeaders):
    headers = {}
    for i in originHeaders:
        if i in response_header:
            headers[i] = originHeaders.get(i)
    return headers


@app.route('/', methods=['GET', "POST", "HEAD", "PUT", "PATCH", "DELETE", "CONNECT", "OPTIONS", "TRACE"])
@app.route('/<path:path>', methods=['GET', "POST", "HEAD", "PUT", "PATCH", "DELETE", "CONNECT", "OPTIONS", "TRACE"])
def proxy(path):
    err_headers = {}
    err_headers['Content-Type'] = 'text/html; charset=UTF-8'
    req_url = request.full_path.lstrip('/')
    print(req_url)

    if not (req_url.startswith("http://") or req_url.startswith("https://")):
        if req_url.startswith("http:/"):
            req_url = req_url.replace('http:/', 'http://')
        elif req_url.startswith("https:/"):
            req_url = req_url.replace('https:/', 'https://')
        else:
            return Response('需要 url: ' + req_url, status=500, headers=err_headers)

    r_headers = buildRequestHeaders(request.headers, urlparse(req_url).hostname)
    try:
        r_headers['Host'] = urlparse(req_url).hostname
        print(r_headers)

        r = requests.request(method=request.method, url=req_url, data=request.data, 
            headers=r_headers, stream=True, allow_redirects=False, timeout=60, proxies=proxies)
        def generate():
            try:
                with r:
                    for chunk in r.iter_content(chunk_size=CHUNK_SIZE):
                        yield chunk
            finally:
                r.close()

        headers = buildResonseHeaders(r.headers)
        cur_next_location = headers.get('Location', '')
        if cur_next_location != '':
            if cur_next_location.startswith('http'):
                headers['Location'] = '/' + quote(cur_next_location)
            elif cur_next_location.startswith('/'):
                parsed = urlparse(req_url)
                headers['Location'] = '/' + quote(f"{parsed.scheme}://{parsed.netloc}{cur_next_location}")
            else:
                parsed = urlparse(req_url)
                headers['Location'] = '/' + quote(f"{parsed.scheme}://{parsed.netloc}{parsed.path}/{cur_next_location}")

        print('success response', headers)
        return Response(generate(), headers=headers, status=r.status_code)
    except Exception as e:
        print(e)
        return Response('server error', status=500, headers=err_headers)


if __name__ == '__main__':
    app.run(host=HOST, port=PORT)

