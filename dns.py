import socket
from util import *
import argparse


def start_server(ip="8.8.8.8"):
    cache = Cache()
    while 1:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.bind(('192.168.0.3', 53))
                data, address = sock.recvfrom(1024)
                parse_request = Parser(data)
                answer_from_cache = cache.get_item((parse_request.name, parse_request.q_type))
                if answer_from_cache is not None:
                    print("ответ из кэша")
                    p = parse_request.get_answer(answer_from_cache[2], answer_from_cache[0])
                    sock.sendto(p, address)
                else:
                    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as dns:
                        dns.bind(("192.168.0.3", 10))
                        dns.sendto(data, (ip, 53))
                        out = dns.recvfrom(1024)[0]
                    sock.sendto(out, address)
                    parse_answer = Parser(out)
                    for info in parse_answer.info:
                        cache.add(*info)
            print("\n***\n")
        except KeyboardInterrupt:
            break
        finally:
            cache.caching()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Кэширующий DNS сервер'
                                                 'Катяева Дарья КН-202 (МЕН280207)')
    parser.add_argument('-d', '--dns', type=str, help='ip of dns')
    args = parser.parse_args()
    if args.dns:
        start_server(args.dns)
    else:
        start_server()
