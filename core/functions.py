import socks
import re

def ProxyFromUrl(url):
    pattern = re.compile(
        r'(?P<scheme>\w+)://(?:([^:/]+):([^@]+)@)?([^:/]+):(\d+)')
    match = pattern.match(url)
    if match:
        proxy = {
            "proxy_type": match.group('scheme'),
            "addr": match.group(4),
            "port": int(match.group(5)),
            "username": match.group(2),
            "password": match.group(3)
        }
        if match.group('scheme') == "http":
            proxy_f = (socks.HTTP, match.group(4), int(match.group(5)),
                       True, match.group(2), match.group(3))
        elif match.group('scheme') == "socks4":
            proxy_f = (socks.SOCKS4, match.group(4), int(match.group(5)),
                       True, match.group(2), match.group(3))
        elif match.group('scheme') == "socks5":
            proxy_f = {"http": url}

        if len(proxy['addr'].split(".")) > 1 and proxy['proxy_type'] in ('http', 'socks4', 'socks5'):

            return proxy_f

    else:
        return
