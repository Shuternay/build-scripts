# !/usr/bin/python3.3
import configparser
import subprocess
import time

import collections
import hashlib
import os


__author__ = 'ksg'

pjoin = os.path.join


class Executable:
    def __init__(self, src_path, target='', use_testlib=False, lang=None, compiler_flags='',
                 work_dir='.', ml=512, use_precompiled=True, save_compiled=True):
        self.src_path = src_path
        self.target = target
        self.lang = lang or Executable.guess_lang(src_path)
        self.use_testlib = use_testlib
        self.flags = compiler_flags
        self.work_dir = work_dir
        self.ml = int(ml)
        self.use_precompiled = use_precompiled
        self.save_compiled = save_compiled
        self.compile_process = None
        self.compiled = False
        self.exec_cmd = ''

        self.start_compilation()

    def compile_cpp(self):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')

        exec_out = self.exec_cmd = pjoin('tmp', os.path.basename(self.src_path) + '.out')

        if self.use_precompiled and Executable.check_hash(self.src_path):
            print('Using previous version of binary\n')
            self.compiled = True
            return  # TODO check for preprocessor and compiler flags

        cxx_compiler = 'g++ {} '.format(self.flags or '-O2 -Wall -xc++ -std=c++11')
        if self.use_testlib:
            cxx_compiler += '-I{0} '.format(pjoin('..', '..', 'lib'))
        self.compile_process = subprocess.Popen('{0} "{1}" -o {2}'.format(cxx_compiler, self.src_path, exec_out),
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    def compile_java(self):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        out_folder = pjoin('tmp', os.path.basename(self.src_path[:-len('.java')]))
        if not os.path.exists(out_folder):
            os.mkdir(out_folder)

        ml = self.ml
        self.exec_cmd = 'java -cp {0} -Xmx{2}M -Xss{3}M {1}'.format(out_folder,
                                                                    os.path.basename(self.src_path[:-len('.java')]),
                                                                    ml, ml // 2)

        if self.use_precompiled and Executable.check_hash(self.src_path):
            print('Using previous version of binary\n')
            self.compiled = True
            return  # TODO check for preprocessor and compiler flags

        java_compiler = 'javac {0}'.format(self.flags)  # TODO java testlib
        self.compile_process = subprocess.Popen('{0} "{1}" -d {2}'.format(java_compiler, self.src_path, out_folder),
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    def compile_python3(self):
        if os.system('python3 -V') == 0:  # command 'python3' doesn't exists on Windows
            self.exec_cmd = 'python3 ' + self.src_path
        else:
            self.exec_cmd = 'python ' + self.src_path
        self.compiled = True

    def compile_shell(self):
        self.exec_cmd = 'sh ' + self.src_path
        self.compiled = True

    def start_compilation(self):
        print('Starting compilation of {0}'.format(self.target))

        lang_to_comp = {
            'C': self.compile_cpp,
            'C++': self.compile_cpp,
            'Java': self.compile_java,
            'Python': self.compile_python3,
            'Python3': self.compile_python3,
            'Shell': self.compile_shell,
        }

        (lang_to_comp[self.lang])()

    def finish_compilation(self):
        if self.compiled:
            return

        print('Finishing compilation of {0}'.format(self.target))
        cout, cerr = self.compile_process.communicate()

        cout = self.process_output(cout)
        cerr = self.process_output(cerr)

        for x in (cout, cerr):
            if x:
                print(x)

        res = self.compile_process.returncode

        if res != 0:
            raise Exception('Compilation error ({})'.format(self.src_path))

        if self.save_compiled:
            Executable.write_hash(self.src_path)

        print('Compilation of {0} finished'.format(self.target))

        self.compiled = True

    def execute(self, stdin=None, stdout=None, stderr=None, tl=None, args=''):
        if not self.compiled:
            self.finish_compilation()

        start_time = time.time()

        process = subprocess.Popen((self.exec_cmd + ' ' + args).split(),
                                   stdin=stdin, stdout=stdout, stderr=stderr,
                                   preexec_fn=self.get_limit_func())

        try:
            cout, cerr = process.communicate(timeout=tl)
        except subprocess.TimeoutExpired:
            process.kill()
            raise

        cout = self.process_output(cout)
        cerr = self.process_output(cerr)

        res = process.returncode

        end_time = time.time()
        exec_time = end_time - start_time

        exec_res_type = collections.namedtuple('exec_res_type',
                                               ['returncode', 'exec_time', 'stdout', 'stderr'])
        return exec_res_type(res, exec_time, cout, cerr)

    def get_limit_func(self):
        if self.lang == 'Java':
            return None
        try:
            # noinspection PyUnresolvedReferences
            import resource  # works only for Unix

            ml = self.ml
            if ml != -1:
                ml *= 1024 ** 2
            hard_limit = resource.getrlimit(resource.RLIMIT_AS)[1]
            return lambda: resource.setrlimit(resource.RLIMIT_AS, (ml, hard_limit))
        except ImportError:
            return None

    @staticmethod
    def guess_lang(src_path: str):
        suffix2lang = [
            ('.c', 'C'),
            ('.cpp', 'C++'),
            ('.java', 'Java'),
            ('.py', 'Python3'),
            ('.sh', 'Shell')
        ]
        for suffix, lang in suffix2lang:
            if src_path.endswith(suffix):
                return lang

        raise Exception('Compilation error (Unknown language, {0})'.format(src_path))

    @staticmethod
    def get_hash(file, info=''):
        with open(file) as f:
            content = info + '-----' + f.read()
            m = hashlib.md5()
            m.update(content.encode('utf-8'))
            return m.hexdigest()

    @staticmethod
    def check_hash(file, info=''):
        cur_hash = Executable.get_hash(file, info)
        prev_hash = ''
        if os.path.exists(pjoin('tmp', os.path.basename(file) + '.hash')):
            with open(pjoin('tmp', os.path.basename(file) + '.hash')) as f:
                prev_hash = f.read()

        return prev_hash == cur_hash

    @staticmethod
    def write_hash(file, info=''):
        cur_hash = Executable.get_hash(file, info)
        with open(pjoin('tmp', os.path.basename(file) + '.hash'), 'w') as f:
            f.write(cur_hash)

    @staticmethod
    def process_output(output):
        if output:
            output = str(output, 'utf-8')
            if output.endswith('\n'):
                output = output[:-1]
        else:
            output = None
        return output


def write_log(s: str, end='\n', file='', out=None, write_to_stdout=True, write_to_file=True):
    if write_to_stdout:
        print(s, end=end)

    if write_to_file and (out or not file == ''):
        if not out:
            out = open(file, 'a')
        print(s, end=end, file=out)
        out.close()


class Config:
    def __init__(self):
        if os.path.exists('problem.conf'):
            self.problem_cfg = configparser.ConfigParser(allow_no_value=True)
            self.problem_cfg.read('problem.conf')

        if get_contest_root():
            self.contest_cfg = configparser.ConfigParser()
            self.contest_cfg.read(os.path.join(get_contest_root(), 'contest.conf'))

    def get_main_solution(self):
        return self.problem_cfg[self.problem_cfg['general']['main solution']]['path']

    def get_solutions(self):
        lst = self.problem_cfg.sections()[:]
        lst.remove('general')
        return [(x, self.problem_cfg[x]['path']) for x in lst]

    def get_problem_param(self, param, use_default=False):
        if use_default:
            return self.problem_cfg['general'].get(param, None)
        else:  # crash on Key Error
            return self.problem_cfg['general'].get(param)

    def has_problem_param(self, param):
        return param in self.problem_cfg['general']

    def get_contest_host(self):
        return self.contest_cfg['default']['contest_host']

    def get_server_contest_path(self):
        return self.contest_cfg['default']['contest_path']


def get_contest_root():
    if os.path.exists('lib') and os.path.exists('problems') and os.path.exists('contest.conf'):
        root = os.curdir
    elif os.path.exists('../lib') and os.path.exists('../problems') and os.path.exists('../contest.conf'):
        root = os.path.normpath(os.path.join('../', os.curdir))
    elif os.path.exists('../../lib') and os.path.exists('../../problems') and os.path.exists('../../contest.conf'):
        root = os.path.normpath(os.path.join('../../', os.curdir))
    else:
        root = None
    return root
