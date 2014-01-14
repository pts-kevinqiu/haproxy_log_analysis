# -*- coding: utf-8 -*-
from datetime import datetime
from datetime import timedelta
from haproxy import filters
from haproxy.main import create_parser
from haproxy.main import main
from haproxy.main import parse_arguments
from haproxy.haproxy_logfile import HaproxyLogFile
from tempfile import NamedTemporaryFile

import sys
import unittest


class RedirectStdout(object):

    def __init__(self, stdout=None):
        self._stdout = stdout or sys.stdout
        self.old_stdout = None

    def __enter__(self):
        self.old_stdout = sys.stdout
        self.old_stdout.flush()
        sys.stdout = self._stdout

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush()
        sys.stdout = self.old_stdout


class ArgumentParsingTest(unittest.TestCase):

    def setUp(self):
        self.parser = create_parser()
        self.default_arguments = [
            '-c', 'counter', '-l', 'haproxy/tests/files/huge.log',
        ]

    def test_arg_parser_start_valid(self):
        """Check that 'start' argument is validated as a datetime object."""
        arguments = ['-s', '11/Dec/2013', ] + self.default_arguments
        data = parse_arguments(self.parser.parse_args(arguments))
        self.assertEqual(datetime(2013, 12, 11), data['start'])

        arguments = ['-s', '11/Dec/2013:13', ] + self.default_arguments
        data = parse_arguments(self.parser.parse_args(arguments))
        self.assertEqual(datetime(2013, 12, 11, hour=13),
                         data['start'])

        arguments = ['-s', '11/Dec/2013:14:15', ] + self.default_arguments
        data = parse_arguments(self.parser.parse_args(arguments))
        self.assertEqual(datetime(2013, 12, 11, hour=14, minute=15),
                         data['start'])

        arguments = ['-s', '11/Dec/2013:14:15:16', ] + self.default_arguments
        data = parse_arguments(self.parser.parse_args(arguments))
        self.assertEqual(datetime(2013, 12, 11, hour=14, minute=15, second=16),
                         data['start'])

    def test_arg_parser_start_invalid(self):
        """Check that if a 'start' argument is not valid an exception is
        raised.
        """
        arguments = ['-s', '/Dec/2013:14:15:16', ] + self.default_arguments
        with self.assertRaises(ValueError):
            parse_arguments(self.parser.parse_args(arguments))

    def test_arg_parser_delta_valid_deltas(self):
        """Check that deltas are correctly checked and processed as timedelta
        values.
        """
        arguments = ['-d', '45s', ] + self.default_arguments
        data = parse_arguments(self.parser.parse_args(arguments))
        self.assertEqual(timedelta(seconds=45), data['delta'])

        arguments = ['-d', '2m', ] + self.default_arguments
        data = parse_arguments(self.parser.parse_args(arguments))
        self.assertEqual(timedelta(minutes=2), data['delta'])

        arguments = ['-d', '13h', ] + self.default_arguments
        data = parse_arguments(self.parser.parse_args(arguments))
        self.assertEqual(timedelta(hours=13), data['delta'])

        arguments = ['-d', '1d', ] + self.default_arguments
        data = parse_arguments(self.parser.parse_args(arguments))
        self.assertEqual(timedelta(days=1), data['delta'])

    def test_arg_parser_delta_invalid(self):
        """Check that if an invalid delta argument is passed an exception is
        raised.
        """
        arguments = ['-d', 'invalid', ] + self.default_arguments
        with self.assertRaises(ValueError):
            parse_arguments(self.parser.parse_args(arguments))

    def test_arg_parser_log_file_valid(self):
        """Check that any log file passed does exist before handling it
        further.
        """
        arguments = ['-c', 'counter',
                     '-l', 'haproxy/tests/test_argparse.py', ]
        data = parse_arguments(self.parser.parse_args(arguments))
        self.assertEqual('haproxy/tests/test_argparse.py', data['log'])

    def test_arg_parser_log_file_invalid(self):
        """Check that if the log file passed does not exist an exception is
        raised.
        """
        arguments = ['-c', 'counter',
                     '-l', 'non_existing.log', ]
        with self.assertRaises(ValueError):
            parse_arguments(self.parser.parse_args(arguments))

    def test_arg_parser_commands_valid(self):
        """Test that valid commands are correctly parsed."""
        arguments = ['-c', 'http_methods',
                     '-l', 'haproxy/tests/files/huge.log', ]
        data = parse_arguments(self.parser.parse_args(arguments))
        self.assertEqual(['http_methods', ], data['commands'])

    def test_arg_parser_commands_invalid(self):
        """Test that trying to input non existing commands raises an
        exception.
        """
        with self.assertRaises(ValueError):
            arguments = ['-c', 'non_existing_method',
                         '-l', 'haproxy/tests/files/huge.log', ]
            parse_arguments(self.parser.parse_args(arguments))

    def test_arg_parser_list_commands(self):
        """Test that list commands argument is parsed."""
        arguments = ['--list-commands', ]
        data = parse_arguments(self.parser.parse_args(arguments))

        for arg in data:
            if arg == 'list_commands':
                self.assertTrue(data['list_commands'])
            else:
                self.assertEqual(data[arg], None)

    def test_arg_parser_list_commands_output(self):
        """Test that list commands argument outputs what's expected."""
        arguments = ['--list-commands', ]
        data = parse_arguments(self.parser.parse_args(arguments))
        test_output = NamedTemporaryFile(mode='w', delete=False)

        with RedirectStdout(stdout=test_output):
            main(data)

        with open(test_output.name, 'r') as output_file:
            output_text = output_file.read()

            for cmd in HaproxyLogFile.commands():
                self.assertIn(cmd, output_text)

    def test_arg_parser_help_output(self):
        """Test that when no arguments are given the help is shown."""
        data = parse_arguments(self.parser.parse_args([]))
        test_output = NamedTemporaryFile(mode='w', delete=False)

        with RedirectStdout(stdout=test_output):
            main(data)

        with open(test_output.name, 'r') as output_file:
            output_text = output_file.read()

            for keyword in ('LOG', 'START', 'DELTA', 'COMMAND'):
                self.assertIn(keyword, output_text)

    def test_arg_parser_help_output_only_log_file(self):
        """Test that when no arguments are given the help is shown."""
        arguments = ['-l', 'haproxy/tests/files/huge.log', ]
        data = parse_arguments(self.parser.parse_args([]))
        test_output = NamedTemporaryFile(mode='w', delete=False)

        with RedirectStdout(stdout=test_output):
            main(data)

        with open(test_output.name, 'r') as output_file:
            output_text = output_file.read()

            for keyword in ('LOG', 'START', 'DELTA', 'COMMAND'):
                self.assertIn(keyword, output_text)

    def test_arg_parser_list_filters_output(self):
        """Test that list filters argument outputs what's expected."""
        arguments = ['--list-filters', ]
        data = parse_arguments(self.parser.parse_args(arguments))
        test_output = NamedTemporaryFile(mode='w', delete=False)

        with RedirectStdout(stdout=test_output):
            main(data)

        with open(test_output.name, 'r') as output_file:
            output_text = output_file.read()

            filters_list = [f for f in dir(filters) if f.startswith('filter_')]

            for filter_name in filters_list:
                self.assertIn(filter_name[7:], output_text)
