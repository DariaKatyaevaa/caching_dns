import struct
import pickle
import time


class Cache:
    def __init__(self):
        self.data = self.load()

    def add(self, name, t, ttl, item):
        self.data[(name, t)] = (item, time.time(), ttl)

    @staticmethod
    def load():
        try:
            with open("cache.txt", 'rb') as f:
                print("Загрузка кэша...")
                data = pickle.load(f)
                need_delete = []
                for k, v in data.items():
                    if v[1] + v[2] <= time.time():
                        need_delete.append(k)
                for k in need_delete:
                    data.pop(k)
            print("готово")
            return data
        except EOFError:
            print("кэш пустой")
            return dict()

    def caching(self):
        with open("cache.txt", 'wb') as f:
            pickle.dump(self.data, f)

    def get_item(self, key):
        if key in self.data:
            value = self.data[key]
            if value[1] + value[2] >= time.time():
                return value
        return None


class Parser:
    def __init__(self, data):
        self.data = data
        self.header = self.parse_header()
        int_flags = bin(self.header[1])
        self.flags = '0' * (16 - len(int_flags) + 2) + str(int_flags)[2:]
        self.is_answer = self.flags[0]
        self.name, self.q_type, position = self.parse_question()
        self.question_len = position
        self.info = None
        if self.is_answer:
            self.info = self.parse_body(position)

    def parse_header(self):
        header = struct.unpack("!6H", self.data[0:12])
        return header

    def parse_question(self):
        name, end = self.parse_name2(12)
        q_type, q_class = struct.unpack("!HH", self.data[end: end + 4])
        information = "Queries: name {0}, type {1}, class {2}".format(name, q_type, q_class)
        print(information)
        return name, q_type, end + 4

    def parse_name2(self, start):
        name_list = []
        position = start
        end = start
        flag = False
        while True:
            if self.data[position] > 63:
                if not flag:
                    end = position + 2
                    flag = True
                position = ((self.data[position] - 192) << 8) + self.data[position + 1]
                continue
            else:
                length = self.data[position]
                if length == 0:
                    if not flag:
                        end = position + 1
                        flag = True
                    break
                position += 1
                name_list.append(self.data[position: position + length])
                position += length
        name = ".".join([i.decode('ascii') for i in name_list])
        return name, end

    def parse_body(self, start):
        answer_list, end1 = self.parse_rr(start, 3)
        authority_list, end2 = self.parse_rr(end1, 4)
        additional_list, end3 = self.parse_rr(end2, 5)
        if len(answer_list) != 0:
            for e in answer_list:
                self.print_rr(e[0], e[1], e[3])
        if len(authority_list) != 0:
            for e in authority_list:
                self.print_rr(e[0], e[1], e[3])
        if len(additional_list) != 0:
            for e in additional_list:
                self.print_rr(e[0], e[1], e[3])
        return answer_list + authority_list + additional_list

    @staticmethod
    def print_rr(name, t, value):
        information = "\tname {0}, type {1},  value{2}".format(name, t, value)
        print(information)

    def parse_rr(self, start, number):
        offset = start
        rr_list = []
        for i in range(self.header[number]):
            name, end = self.parse_name2(offset)
            offset = end
            r_type, r_class, r_ttl, rd_length = struct.unpack("!2HIH", self.data[offset: offset + 10])

            offset += 10
            if r_type == 1:
                ip = struct.unpack("!4B", self.data[offset: offset + 4])
                offset += 4
                rr_list.append((name, r_type, r_ttl, ip))
            elif r_type == 2:
                dns_server_name, dns_name_end = self.parse_name2(offset)
                offset = dns_name_end
                rr_list.append((name, r_type, r_ttl, dns_server_name))
            else:
                offset += rd_length

        return rr_list, offset

    def get_answer(self, ttl, value):
        header = list(self.header[:12])
        header[1] = 2 ** 15
        header[3] = 1
        question = self.data[12: self.question_len]
        name = self.data[12: self.question_len - 4]
        if self.q_type == 1:
            item = struct.pack("!4B", *value)
            length = 4
        if self.q_type == 2:
            octets = (name.decode()).split(".")
            result = []
            for o in octets:
                result.append(len(o))
                for l in o:
                    result.append(ord(l))
            result.append(0)
            item = struct.pack("!" + str(len(result)) + "B", *result)
            length = len(item)

        tail = struct.pack("!HHIH", self.q_type, 1, ttl, length)
        answer = struct.pack("!6H", *header) + question + name + tail + item
        return answer
