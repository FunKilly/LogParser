import ply.lex as lex
from ply.lex import TOKEN
import datetime
import re


class MyLexer(object):
    # List of token names.
    tokens = (
        'TIME',
        'REQNUM',
        'RESPONSE_SIZE',
        'RESPONSE_CODE'
    )
    log_stat = []

    # Defining rules for searching regular expressions.
    datetime = r'\[\D+\s\D+\s\d+\s\d{2}:\d{2}:\d{2}\s\d{4}\]'
    reqnum = r'\D{3}:\s\d+\/\d+'
    response_size = r'generated\s\d+'
    response_code = r'\(HTTP/\d+.\d+\s\d+\)'

    # Action codes for particular tokens.
    @TOKEN(datetime)
    def t_TIME(self, t):
        t.value = datetime.datetime.strptime(t.value, '[%c]')
        return t

    @TOKEN(reqnum)
    def t_REQNUM(self, t):
        t.value = re.search(r'\/\d+', t.value)
        t.value = t.value.group(0).replace('/', '')
        return t

    @TOKEN(response_size)
    def t_RESPONSE_SIZE(self, t):
        t.value = re.search(r'\d+', t.value)
        t.value = int(t.value.group(0))
        return t

    @TOKEN(response_code)
    def t_RESPONSE_CODE(self, t):
        t.value = re.search(r'\s\d+', t.value)
        t.value = int(t.value.group(0))
        return t

    # Defining a rule for tracking line numbers.
    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)

    # A string containing ignored characters.
    t_ignore = ' \t'

    # Error handling rule.
    def t_error(self, t):
        t.lexer.skip(1)

    # Building the lexer.
    def build(self, **kwargs):
        self.lexer = lex.lex(module=self, **kwargs)

    # Starting the lexer.
    def run(self, data):
        self.lexer.input(data)
        while True:
            tok = self.lexer.token()
            if not tok:
                break
            self.log_stat.append(tok.value)