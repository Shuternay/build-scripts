import json
import pkgutil
from unittest import TestCase
from xml.etree import ElementTree

import os
import tempfile

from build_scripts import polygon

__author__ = 'ksg'


class TestImportProblem(TestCase):
    def setUp(self):
        self.saved_path = os.getcwd()

        self.tempdir = tempfile.TemporaryDirectory()
        os.chdir(self.tempdir.name)

    def tearDown(self):
        os.chdir(self.saved_path)
        self.tempdir.cleanup()

    def unpack_src(self, path):
        src = pkgutil.get_data('tests', os.path.join('polygon_data', path))  # bytes
        src_file = tempfile.NamedTemporaryFile(delete=False)
        src_file.write(src)  # bytes too
        src_file.flush()
        return src_file

    def unpack_named_src(self, path, name=None):
        name = name or os.path.basename(path)
        src = pkgutil.get_data('tests', os.path.join('polygon_data', path))  # bytes
        src_file = open(name, 'wb')
        src_file.write(src)
        src_file.flush()
        return src_file

    def test_import_problem(self):
        self.unpack_named_src('problem_full.xml', 'problem.xml')
        self.unpack_named_src('file.txt', 'doall.sh')
        self.unpack_named_src('file.txt', 'wipe.sh')
        os.mkdir('statements')
        os.mkdir('statements/russian')
        self.unpack_named_src('file.txt', 'statements/russian/problem.tex')
        os.mkdir('solutions')
        self.unpack_named_src('file.txt', 'solutions/fastSolution.cpp')
        self.unpack_named_src('file.txt', 'solutions/slowSolution.cpp')
        self.unpack_named_src('file.txt', 'statements/russian/problem.tex')
        os.mkdir('files')
        self.unpack_named_src('file.txt', 'files/validator_1.cpp')
        self.unpack_named_src('file.txt', 'files/checker_1.cpp')
        os.mkdir('scripts')
        self.unpack_named_src('file.txt', 'scripts/script.sh')

        tempdir = tempfile.TemporaryDirectory()
        polygon.import_problem('.', tempdir.name)

        self.assertTrue(os.path.exists(os.path.join(tempdir.name, 'files', 'checker_1.cpp')))
        self.assertTrue(os.path.exists(os.path.join(tempdir.name, 'scripts', 'script.sh')))
        self.assertTrue(os.path.exists(os.path.join(tempdir.name, 'doall.sh')))
        self.assertTrue(os.path.exists(os.path.join(tempdir.name, 'wipe.sh')))

        with open(os.path.join(tempdir.name, 'problem.json')) as fd:
            conf = json.loads(fd.read())
            self.maxDiff = None
            self.assertEqual({
                "title": "Печальная ванилька",
                "short_name": "vanilla",
                "system_name": "vanilla",
                "solutions": [
                    {'path': 'solutions/fastSolution.cpp',
                     'is_main': True,
                     'tag': 'main',
                     'type': 'cpp.g++'},
                    {'path': 'solutions/slowSolution.cpp',
                     'is_main': False,
                     'tag': 'time-limit-exceeded',
                     'type': 'cpp.g++'},
                ],
                "test_num_width": 2,
                "samples_num": 0,
                "tl": 2,
                "ml": 64,
                "validator": "validator_1.cpp",
                "checker": "checker_1.cpp",
                # "gen": "gen.cpp",
                # "gen_work_dir": ".",
                "use_doall": True,
                "doall_cmd": "bash doall.sh",
                "use_wipe": True,
                "wipe_cmd": "bash wipe.sh",
            }, conf)

    def test_import_statement(self):
        self.unpack_named_src('problem_full.xml', 'problem.xml')
        os.mkdir('statements')
        os.mkdir('statements/russian')
        self.unpack_named_src('file.txt', 'statements/russian/problem.tex')
        polygon_conf_tree = ElementTree.parse('problem.xml')
        polygon_conf_root = polygon_conf_tree.getroot()

        tempdir = tempfile.TemporaryDirectory()

        polygon.import_statement('.', tempdir.name, polygon_conf_root, 'short_name')

        self.assertTrue(os.path.exists(os.path.join(tempdir.name, 'statements', 'short_name.tex')))
        with open(os.path.join(tempdir.name, 'statements', 'short_name.tex')) as fd:
            self.assertEqual('file', fd.read())

    def test_import_statement_default(self):
        self.unpack_named_src('problem_empty.xml', 'problem.xml')
        polygon_conf_tree = ElementTree.parse('problem.xml')
        polygon_conf_root = polygon_conf_tree.getroot()

        tempdir = tempfile.TemporaryDirectory()

        polygon.import_statement('.', tempdir.name, polygon_conf_root, 'short_name')

        self.assertTrue(os.path.exists(os.path.join(tempdir.name, 'statements', 'short_name.tex')))

    def test_import_solutions(self):
        self.unpack_named_src('problem_full.xml', 'problem.xml')
        os.mkdir('solutions')
        self.unpack_named_src('file.txt', 'solutions/fastSolution.cpp')
        self.unpack_named_src('file.txt', 'solutions/slowSolution.cpp')
        polygon_conf_tree = ElementTree.parse('problem.xml')
        polygon_conf_root = polygon_conf_tree.getroot()

        tempdir = tempfile.TemporaryDirectory()

        conf = {}
        polygon.import_solutions('.', tempdir.name, polygon_conf_root, conf)

        self.assertDictEqual({
            'solutions': [
                {'path': 'solutions/fastSolution.cpp',
                 'is_main': True,
                 'tag': 'main',
                 'type': 'cpp.g++'},
                {'path': 'solutions/slowSolution.cpp',
                 'is_main': False,
                 'tag': 'time-limit-exceeded',
                 'type': 'cpp.g++'},
            ]}, conf)

    def test_import_validator(self):
        self.unpack_named_src('problem_full.xml', 'problem.xml')
        os.mkdir('files')
        self.unpack_named_src('file.txt', 'files/validator_1.cpp')
        polygon_conf_tree = ElementTree.parse('problem.xml')
        polygon_conf_root = polygon_conf_tree.getroot()

        tempdir = tempfile.TemporaryDirectory()

        conf = {}
        polygon.import_validator('.', tempdir.name, polygon_conf_root, conf)
        self.assertDictEqual({'validator': 'validator_1.cpp'}, conf)

        self.assertTrue(os.path.exists(os.path.join(tempdir.name, 'validator_1.cpp')))
        with open(os.path.join(tempdir.name, 'validator_1.cpp')) as fd:
            self.assertEqual('file', fd.read())

    def test_import_validator_default(self):
        self.unpack_named_src('problem_empty.xml', 'problem.xml')
        polygon_conf_tree = ElementTree.parse('problem.xml')
        polygon_conf_root = polygon_conf_tree.getroot()

        tempdir = tempfile.TemporaryDirectory()

        conf = {}
        polygon.import_validator('.', tempdir.name, polygon_conf_root, conf)
        self.assertDictEqual({'validator': 'validator.cpp'}, conf)

        self.assertTrue(os.path.exists(os.path.join(tempdir.name, 'validator.cpp')))

    def test_import_checker(self):
        self.unpack_named_src('problem_full.xml', 'problem.xml')
        os.mkdir('files')
        self.unpack_named_src('file.txt', 'files/checker_1.cpp')
        polygon_conf_tree = ElementTree.parse('problem.xml')
        polygon_conf_root = polygon_conf_tree.getroot()

        tempdir = tempfile.TemporaryDirectory()

        conf = {}
        polygon.import_checker('.', tempdir.name, polygon_conf_root, conf)
        self.assertDictEqual({'checker': 'checker_1.cpp'}, conf)

        self.assertTrue(os.path.exists(os.path.join(tempdir.name, 'checker_1.cpp')))
        with open(os.path.join(tempdir.name, 'checker_1.cpp')) as fd:
            self.assertEqual('file', fd.read())

    def test_import_checker_default(self):
        self.unpack_named_src('problem_empty.xml', 'problem.xml')
        polygon_conf_tree = ElementTree.parse('problem.xml')
        polygon_conf_root = polygon_conf_tree.getroot()

        tempdir = tempfile.TemporaryDirectory()

        conf = {}
        polygon.import_checker('.', tempdir.name, polygon_conf_root, conf)
        self.assertDictEqual({'checker': 'checker.cpp'}, conf)

        self.assertTrue(os.path.exists(os.path.join(tempdir.name, 'checker.cpp')))
