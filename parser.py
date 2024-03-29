import re
import datetime
import argparse
from humanize import naturalsize

class ArgsManager(object):

    dateformat = '%d-%m-%Y_%H-%M-%S'
    date_range = {'from_date': None, 'to_date': None}

    def arguments_parsing(self):
        # Initializing script arguments.
        parser = argparse.ArgumentParser()
        parser.add_argument('--from', dest='from_date',
                            help='Podaj datę od której należy rozpocząć parsowanie', required=False)
        parser.add_argument('--to', dest='to_date',
                            help='Podaj datę na której należy zakończyć parsowanie', required=False)
        parser.add_argument('filename', help="Podaj nazwe pliku z logami")
        self.convert_date(parser.parse_args().from_date, parser.parse_args().to_date)

        return parser.parse_args()

    def convert_date(self, from_date, to_date):
        # Converting date objects from input to datetime type or signalizing wrong input format.
        if from_date:
            try:
                from_date = datetime.datetime.strptime(from_date, self.dateformat)
                self.date_range['from_date'] = from_date
            except ValueError:
                print("Zły format daty: '", from_date, f"' Poprawny format: {self.dateformat}")

        if to_date:
            try:
                to_date = datetime.datetime.strptime(to_date, self.dateformat)
                self.date_range['to_date'] = to_date
            except ValueError:
                print("Zły format daty: '", to_date, f"' Poprawny format: {self.dateformat}")
        return self.date_range


class Lexer(object):

    LOG_RE = re.compile(r"""
    ^\[pid:\s  (?P<pid>\d+)  \|app:\s  (?P<app>\d+)  \|req:\s(?P<log_num>\d+)
    \/(?P<total_num>\d+)]\s(?P<ip>\d+.\d+.\d+.\d+)\s\(\)\s{(?P<vars>\d+\svars\sin\s\d+\sbytes)}\s\[
    (?P<datetime>.+?)\]\s(?P<method>\w+)\s.+generated\s(?P<request_size>\d+)[^(]+[^ ]+\s(?P<code_status>\d+).+
    """, re.X)

    arguments = ArgsManager().arguments_parsing()
    date_range = ArgsManager.date_range

    def read(self, filename):
        # Reading logfile line by line, transfering needed data from it with correct type.

        with open(filename, 'r') as logfile:
            log = logfile.readline()
            while log:
                if re.match(r'^\[pid', log):
                    log = self.LOG_RE.search(log).groupdict()
                    log['datetime'] = datetime.datetime.strptime(log['datetime'], '%c')
                    log['request_size'] = int(log['request_size'])
                    log_data = [log['log_num'], log['datetime'], log['code_status'], log['request_size']]
                    yield log_data
                log = logfile.readline()

    def parse_range(self, log_stats):
        # Setting date range for parsing, if date isn't transferred, the date from logs is taken.
        if self.date_range['from_date'] is None:
            self.date_range['from_date'] = log_stats[0][1]

        if self.date_range['to_date'] is None:
            self.date_range['to_date'] = log_stats[-1][1]

        return self.date_range

    def generate_logs(self):
        # Generating correct list with statistics for each log for defined date range.
        log_stats = [log for log in self.read(self.arguments.filename)]
        self.parse_range(log_stats)
        log_stats = [log for log in log_stats if self.date_range['from_date'] < log[1] < self.date_range['to_date']]
        return log_stats


class Parser(object):

    def __init__(self, filename=''):
        self.filename = filename
        self.date_range = {'from_date': None, 'to_date': None}
        self.log_stats = []

    @staticmethod
    def calc_rps(start_date, end_date, numbofreq):
        # Calculate requests per seconds.
        difference = (end_date - start_date)
        rps = int(difference.total_seconds())/numbofreq
        return f'Zapytania/sec: {round(rps, 2)}'

    @staticmethod
    def group_codes(log_stats):
        # Group codes by code and countering their average size.
        codes_size = {}
        codes_counter = {}

        for request in log_stats:
            if request[2] not in codes_size.keys():
                codes_size[request[2]] = request[3]
            else:
                codes_size[request[2]] += request[3]
            if request[2] not in codes_counter.keys():
                codes_counter[request[2]] = 1
            else:
                codes_counter[request[2]] += 1

        return codes_size, codes_counter

    def generate_response(self):

        # Generate number of requests.
        print(f'Zapytan: {len(self.log_stats)}')

        # Generate number of request per second.
        print(self.calc_rps(self.log_stats[0][1], self.log_stats[-1][1], len(self.log_stats)))

        codes_size, codes_counter = self.group_codes(self.log_stats)

        # Combine request for a code counter.
        response_code_size = ''
        response_code_counter = f"Odpowiedzi: ({', '.join(f'{key}: {value}' for key, value in codes_counter.items())})"

        # Combine request for a average code size.
        for code, size in codes_size.items():
            amount = naturalsize(size)
            response_code_size = response_code_size + f'Sredni rozmiar zapytan z kodem {code}: {amount} \n'

        print(response_code_counter)
        print(response_code_size)

    def main(self):

        self.log_stats = Lexer().generate_logs()

        try:
            self.generate_response()
        except IndexError:
            print(f'Podany przedział czasowy zwrócił {len(self.log_stats)} rekordów. Brak statystyk.')


if __name__ == '__main__':
    p = Parser()
    p.main()