import pkgutil
import subprocess
from unittest import TestCase
import sys
import unittest
import os
import tempfile

from olymper.executable import Executable

__author__ = 'ksg'


class TestExecutable(TestCase):
    def setUp(self):
        self.saved_path = os.getcwd()

        self.tempdir = tempfile.TemporaryDirectory()
        os.chdir(self.tempdir.name)

    def tearDown(self):
        os.chdir(self.saved_path)
        self.tempdir.cleanup()

    def unpack_src(self, path):
        src = pkgutil.get_data('tests', os.path.join('executable_data', path))  # bytes
        src_file = tempfile.NamedTemporaryFile(delete=False)
        src_file.write(src)  # bytes too
        src_file.flush()
        return src_file

    def test_bash_support(self):
        src_name = 'bash_full.bash'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='Bash',
                                    use_precompiled=False, save_compiled=False)

            exec_res = executable.execute(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.assertEqual(exec_res.stdout, 'stdout example')
        self.assertEqual(exec_res.stderr, 'stderr example')
        self.assertEqual(exec_res.returncode, 4)

    def test_cpp_support(self):
        src_name = 'cpp_full.cpp'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='C++',
                                    use_precompiled=False, save_compiled=False)
            exec_res = executable.execute(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.assertEqual(exec_res.stdout, 'stdout example')
        self.assertEqual(exec_res.stderr, 'stderr example')
        self.assertEqual(exec_res.returncode, 4)

    def test_delphi_support(self):
        src_name = 'delphi_full.dpr'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='Delphi',
                                    use_precompiled=False, save_compiled=False)

            exec_res = executable.execute(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.assertEqual(exec_res.stdout, 'stdout example')
        self.assertEqual(exec_res.stderr, 'stderr example')
        # self.assertEqual(exec_res.returncode, 4)  # I don't know, how to set in Pascal/Delphi

    def test_pascal_support(self):
        src_name = 'pascal_full.pas'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='Pascal',
                                    use_precompiled=False, save_compiled=False)

            exec_res = executable.execute(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.assertEqual(exec_res.stdout, 'stdout example')
        self.assertEqual(exec_res.stderr, 'stderr example')
        # self.assertEqual(exec_res.returncode, 4)  # I don't know, how to set in Pascal/Delphi

    def test_python_support(self):
        src_name = 'python3_full.py'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='Python3',
                                    use_precompiled=False, save_compiled=False)

            exec_res = executable.execute(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.assertEqual(exec_res.stdout, 'stdout example')
        self.assertEqual(exec_res.stderr, 'stderr example')
        self.assertEqual(exec_res.returncode, 4)

    # tests manual compilation finishing for not compilable languages (like Python)
    def test_manual_compilation_finishing_1(self):
        src_name = 'python3_exit0.py'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='Python3',
                                    use_precompiled=False, save_compiled=False)
            executable.finish_compilation()
            exec_res = executable.execute(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.assertEqual(exec_res.returncode, 0)

    # tests manual compilation finishing for compilable languages (like C++)
    def test_manual_compilation_finishing_2(self):
        src_name = 'cpp_exit0.cpp'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='C++',
                                    use_precompiled=False, save_compiled=False)
            executable.finish_compilation()
            exec_res = executable.execute(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.assertEqual(exec_res.returncode, 0)

    def test_execution_tl_1(self):
        src_name = 'python3_tl_03.py'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='Python3',
                                    use_precompiled=False, save_compiled=False)

            with self.assertRaises(subprocess.TimeoutExpired):
                executable.execute(tl=0.1)

    def test_execution_tl_2(self):
        src_name = 'python3_tl_03.py'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='Python3',
                                    use_precompiled=False, save_compiled=False)

            # shouldn't raise subprocess.TimeoutExpired
            exec_res = executable.execute(tl=1)
        self.assertEqual(exec_res.returncode, 0)

    def test_execution_tl_3(self):
        src_name = 'python3_tl_03.py'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='Python3',
                                    use_precompiled=False, save_compiled=False)

            # shouldn't raise subprocess.TimeoutExpired
            exec_res = executable.execute()  # no TL
        self.assertEqual(exec_res.returncode, 0)

    @unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux")
    def test_execution_ml_1(self):
        src_name = 'cpp_ml_200.cpp'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='C++', ml=170,
                                    use_precompiled=False, save_compiled=False)

            exec_res = executable.execute()
        self.assertNotEqual(exec_res.returncode, 0)

    @unittest.skipUnless(sys.platform.startswith("linux"), "requires Linux")
    def test_execution_ml_2(self):
        src_name = 'cpp_ml_200.cpp'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='C++', ml=230,
                                    use_precompiled=False, save_compiled=False)

            exec_res = executable.execute()
        self.assertEqual(exec_res.returncode, 0)

    def test_execution_args_1(self):
        src_name = 'python3_args.py'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='Python',
                                    use_precompiled=False, save_compiled=False)

            exec_res = executable.execute(args='42')
        self.assertEqual(exec_res.returncode, 42)

    def test_execution_args_2(self):
        src_name = 'python3_args.py'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='Python',
                                    use_precompiled=False, save_compiled=False)

            exec_res = executable.execute(args='42 58')
        self.assertEqual(exec_res.returncode, 100)

    def test_work_dir_changing_python3(self):
        tempdir = tempfile.TemporaryDirectory()

        src_name = 'python3_path.py'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='Python3',
                                    use_precompiled=False, save_compiled=False,
                                    work_dir=tempdir.name)

            exec_res = executable.execute(stdout=subprocess.PIPE)

        self.assertEqual(exec_res.stdout, os.path.abspath(tempdir.name))

    def test_work_dir_changing_to_tmp_cpp(self):
        src_name = 'cpp_exit0.cpp'
        with self.unpack_src(src_name) as src_file:
            executable = Executable(src_file.name, src_name, lang='C++',
                                    use_precompiled=False, save_compiled=False,
                                    work_dir='tmp')

            exec_res = executable.execute(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.assertEqual(exec_res.returncode, 0)

    # @unittest.skip('')
    # def test_start_compilation(self):
    # self.fail()
    # @unittest.skip('')
    # def test_finish_compilation(self):
    # self.fail()
    # @unittest.skip('')
    # def test_execute(self):
    #     self.fail()

    def test_guess_lang_bash(self):
        self.assertEqual(Executable.guess_lang('name.bash'), 'Bash')

    def test_guess_lang_c(self):
        self.assertEqual(Executable.guess_lang('name.c'), 'C')

    def test_guess_lang_cpp(self):
        self.assertEqual(Executable.guess_lang('name.cpp'), 'C++')

    def test_guess_lang_delphi(self):
        self.assertEqual(Executable.guess_lang('name.dpr'), 'Delphi')

    def test_guess_lang_java(self):
        self.assertEqual(Executable.guess_lang('name.java'), 'Java')

    def test_guess_lang_pascal(self):
        self.assertEqual(Executable.guess_lang('name.pas'), 'Pascal')

    def test_guess_lang_python(self):
        self.assertEqual(Executable.guess_lang('name.py'), 'Python3')

    def test_guess_lang_shell(self):
        self.assertEqual(Executable.guess_lang('name.sh'), 'Shell')

    def test_guess_lang_unknown(self):
        with self.assertRaises(Exception) as cm:
            Executable.guess_lang('name')
        self.assertTrue(cm.exception.args[0].startswith('Compilation error (Unknown language,'))

        # @unittest.skip('')
        # def test_get_hash(self):
        #     self.fail()
        # @unittest.skip('')
        # def test_check_hash(self):
        #     self.fail()
        # @unittest.skip('')
        # def test_write_hash(self):
        #     self.fail()