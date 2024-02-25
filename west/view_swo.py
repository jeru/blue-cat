# Copyright 2024 Cheng Sheng
# SPDX-License-Identifier: Apache-2.0
'''
A (probably over-hardwired) SWO viewer as a `west` command.
'''

from textwrap import dedent

from west import log
from west.commands import WestCommand


class ViewSwo(WestCommand):
    def __init__(self):
        super().__init__(
            'view-swo',
            'Views the SWO output.',
            dedent('''
            TODO: FILL IN.
            '''))

    def do_add_parser(self, parser_adder):
        parser = parser_adder.add_parser(self.name, help=self.help,
                                         description=self.description)
        return parser

    def do_run(self, args, unknown_args):
        log.inf('Hello, view-swo')
