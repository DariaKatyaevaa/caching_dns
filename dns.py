import socket
from util import *


def start_server():
    cache = Cache()
    while 1:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('192.168.0.3', 53))
                data, addr = sock.recvfrom(1024)
                parse_request = Parser(data)
                value = cache.get_item((parse_request.name, parse_request.q_type))
                if value is not None:
                    print("ответ из кэша")
                    p = parse_request.get_answer(value[2], value[0])
                    sock.sendto(p, addr)
                else:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as dns:
                        dns.bind(("192.168.0.3", 10))
                        dns.sendto(data, ("8.8.8.8", 53))
                        out = dns.recvfrom(1024)[0]
                    sock.sendto(out, addr)
                    parse_answer = Parser(out)
                    for info in parse_answer.info:
                        cache.add(*info)
            print("\n***\n")
        except KeyboardInterrupt:
            break
        finally:
            cache.caching()


if __name__ == '__main__':
    start_server()
