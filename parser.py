from lexer import MyLexer
import re
import datetime
import argparse
from typing import NewType

dt = NewType('dt', datetime.datetime)


class Parser(object):
    """ Function process a return from lexer to logs statistics """
    def __init__(self, filename=''):
        self.filename = filename
        self.log_stats = []
        self.lexer = MyLexer()
        self.date_range = {'from_date': None, 'to_date': None}

    def arguments_parsing(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--from', dest='from_date',
                            help='Podaj datę od której należy rozpocząć parsowanie', required=False)
        parser.add_argument('--to', dest='to_date',
                            help='Podaj datę na której należy zakończyć parsowanie', required=False)
        parser.add_argument('filename', help="Podaj nazwe pliku z logami")
        args = parser.parse_args()
        self.convert_date(args.from_date, args.to_date)
        return args.filename

    def convert_date(self, from_date, to_date):
        if from_date:
            try:
                from_date = datetime.datetime.strptime(from_date, '%d-%m-%Y_%H-%M-%S')
                self.date_range['from_date'] = from_date
            except ValueError:
                print("Zły format daty: '", from_date, "' Poprawny format: %d-%m-%Y_%H-%M-%S")

        if to_date:
            try:
                to_date = datetime.datetime.strptime(to_date, '%d-%m-%Y_%H-%M-%S')
                self.date_range['to_date'] = to_date
            except ValueError:
                print("Zły format daty: '", to_date, "' Poprawny format: %d-%m-%Y_%H-%M-%S")
        pass

    def parse_range(self):
        '''for log in self.log_stats:
            if self.date_range['from_date'] and log[1] < self.date_range['from_date']:
                print(log)
            if self.date_range['to_date'] and log[1] > self.date_range['to_date']:
                print(self.date_range['to_date'])
                self.log_stats.pop(self.log_stats.index(log))'''
        if self.date_range['from_date'] is None:
            self.date_range['from_date'] = self.log_stats[0][1]
        elif self.date_range['to_date'] is None:
            self.date_range['to_date'] = self.log_stats[-1][1]
        self.log_stats = [log for log in self.log_stats if self.date_range['from_date'] <= log[1] <= self.date_range['to_date']]
        return self.log_stats


    @staticmethod
    def read(filename):
        # Read a log file.
        with open(filename, 'r') as logfile:
            logs = logfile.readlines()
        return logs

    @staticmethod
    def group_tokens(tokens: list, n: int):
        # Group tokens from 1 request.
        for i in range(0, len(tokens), n):
            val = tokens[i:i + n]
            if len(val) == n:
                yield tuple(val)

    @staticmethod
    def calc_rps(start_date: dt, end_date: dt, numbofreq: int):
        # Calculate requests per seconds.
        difference = (end_date - start_date)
        rps = int(difference.total_seconds())/numbofreq
        return f'Zapytania/sec: {round(rps, 2)}'

    @staticmethod
    def group_codes(log_stats: list):
        # Group codes by size and counter them.
        codes_size = {}
        codes_counter = {}

        for request in log_stats:
            if request[3] not in codes_size.keys():
                codes_size[request[3]] = request[2]
            else:
                codes_size[request[3]] += request[2]
            if request[3] not in codes_counter.keys():
                codes_counter[request[3]] = 1
            else:
                codes_counter[request[3]] += 1

        return codes_size, codes_counter

    def generate_response(self):
        # Generate response for script.

        # Generate number of requests
        print(f'Zapytan: {len(self.log_stats)}')

        # Generate number of request per second
        print(self.calc_rps(self.log_stats[0][1], self.log_stats[-1][1], len(self.log_stats)))

        codes_size, codes_counter = self.group_codes(self.log_stats)
        # Combine request for a code counter
        response_code_size = ''
        response_code_counter = ', '.join(f'{key}: {value}' for key, value in codes_counter.items())
        response_code_counter = f'Odpowiedzi: ({response_code_counter})'

        # Combine request for a average code size
        for code, size in codes_size.items():
            unit = 'Mb'
            size_rounded = round(((size / codes_counter[code]) / (1024 * 1024)), 2)
            if size_rounded == 0:
                size_rounded = round(((size / codes_counter[code]) / 1024), 2)
                unit = 'Kb'
                if size_rounded == 0:
                    size_rounded = round((size / codes_counter[code]), 2)
                    unit = 'b'
            response_code_size = response_code_size + f'Sredni rozmiar zapytan z kodem {code}: {size_rounded} {unit} \n'

        print(response_code_counter)
        print(response_code_size)

    def main(self):
        # Reading a file, than creating lexer instance with input.
        for line in self.read(self.arguments_parsing()):
            if re.match(r"\[\D{3}:\s\d+", line):
                self.lexer.build()
                self.lexer.run(line)
        # Process of return from lexer
        self.log_stats = [item for item in self.group_tokens(self.lexer.log_stat, 4)]
        if self.date_range:
            self.parse_range()

        self.generate_response()


if __name__ == '__main__':
    p = Parser()
    p.main()
