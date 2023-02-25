from enum import Enum
import requests
from urllib.parse import urlparse, urljoin
import os
import io

# response = requests.get("http://example.com")
# content = response.text

class LoadType(Enum):
    BIN='arraybuffer'
    TEXT='text'
    IO='io'

def load(url:str,type:LoadType):
    if url.startswith('http'):
        response = requests.get(url)
        if type==LoadType.BIN:
            return response.content
        elif type==LoadType.TEXT:
            return response.text
        elif type==LoadType.IO:
            return io.BytesIO(response.content)
            
    else:
        if type==LoadType.IO:
            return open(url,'rb')

        f = open(url,'r')
        data = f.read()
        return data

def normalize_path(path:str):
    """
    path可以是网络地址，也可以是本地地址
    """
    url_parts = urlparse(path)
    if url_parts.scheme and url_parts.netloc:
        p = url_parts.path
        rpath = os.path.normpath(p).replace('\\', '/')
        return urljoin(path,rpath)
    return os.path.normpath(path)
    