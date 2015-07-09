import pkgutil
from unittest import TestCase

import tempfile
import os

from misc import Config

__author__ = 'ksg'


class TestConfig(TestCase):
    def setUp(self):
        self.saved_path = os.getcwd()

        self.tempdir = tempfile.TemporaryDirectory()
        os.chdir(self.tempdir.name)

    def tearDown(self):
        os.chdir(self.saved_path)
        self.tempdir.cleanup()

    def unpack_src(self, path):
        src = pkgutil.get_data('tests', os.path.join('config_data', path))  # bytes
        src_file = tempfile.NamedTemporaryFile(delete=False)
        src_file.write(src)  # bytes too
        src_file.flush()
        return src_file

    def unpack_named_src(self, path, name=None):
        name = name or os.path.basename(path)
        src = pkgutil.get_data('tests', os.path.join('config_data', path))  # bytes
        src_file = open(name, 'w')
        src_file.write(src.decode())  # str
        src_file.flush()
        return src_file

    def test_get_main_solution_ini(self):
        with self.unpack_named_src('problem.conf') as conf_file:
            cfg = Config()
            self.assertEqual(cfg.get_main_solution(), 'solutions/floors_ks.cpp')

    def test_get_main_solution_json(self):
        with self.unpack_named_src('problem.json') as conf_file:
            cfg = Config()
            self.assertEqual(cfg.get_main_solution(), 'solutions/floors_ks.cpp')

    def test_get_solutions_ini(self):
        with self.unpack_named_src('problem.conf') as conf_file:
            cfg = Config()
            self.assertCountEqual(cfg.get_solutions(),
                                  [('ks_py', 'solutions/floors_ks.py'),
                                   ('ks', 'solutions/floors_ks.cpp'),
                                   ('ks_slow', 'solutions/floors_ks_slow.cpp')])

    def test_get_solutions_json(self):
        with self.unpack_named_src('problem.json') as conf_file:
            cfg = Config()
            self.assertCountEqual(cfg.get_solutions(),
                                  [('ks_fast', 'solutions/floors_ks_fast.cpp'),
                                   ('floors_ks.cpp', 'solutions/floors_ks.cpp'),
                                   ('floors_ks_slow.cpp', 'solutions/floors_ks_slow.cpp')])

    def test_get_problem_param_ini(self):
        with self.unpack_named_src('problem.conf') as conf_file:
            cfg = Config()
            self.assertEqual(cfg.get_problem_param('title', False), '???')
            self.assertEqual(cfg.get_problem_param('title'), '???')

    def test_get_problem_param_json(self):
        with self.unpack_named_src('problem.json') as conf_file:
            cfg = Config()
            self.assertEqual(cfg.get_problem_param('title', False), '')
            self.assertEqual(cfg.get_problem_param('title'), '')

    def test_get_bool_problem_param_ini(self):
        with self.unpack_named_src('problem.conf') as conf_file:
            cfg = Config()
            # self.assertFalse(cfg.get_problem_param('use_doall'))
            self.assertFalse(cfg.get_problem_param('qwerty'))

    def test_get_bool_problem_param_json(self):
        with self.unpack_named_src('problem.json') as conf_file:
            cfg = Config()
            self.assertFalse(cfg.get_problem_param('use_doall'))
            self.assertFalse(cfg.get_problem_param('qwerty'))

    def test_get_not_existing_problem_param_ini(self):
        with self.unpack_named_src('problem.conf') as conf_file:
            cfg = Config()
            self.assertIsNone(cfg.get_problem_param('qwerty'))
            with self.assertRaises(KeyError):
                cfg.get_problem_param('qwerty', False)

    def test_get_not_existing_problem_param_json(self):
        with self.unpack_named_src('problem.json') as conf_file:
            cfg = Config()
            self.assertIsNone(cfg.get_problem_param('qwerty'))
            with self.assertRaises(KeyError):
                cfg.get_problem_param('qwerty', False)

                # def test_has_problem_param(self):
                #     self.fail()
                #
                # def test_get_contest_host(self):
                #     self.fail()
                #
                # def test_get_server_contest_path(self):
                #     self.fail()
