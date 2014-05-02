#!/usr/bin/python3.3
import configparser
import hashlib
import os

__author__ = 'ksg'

pjoin = os.path.join


def get_hash(file, info=''):
    with open(file) as f:
        content = info + '-----' + f.read()
        m = hashlib.md5()
        m.update(content.encode('utf-8'))
        return m.hexdigest()


def check_hash(file, info=''):
    cur_hash = get_hash(file, info)
    prev_hash = ''
    if os.path.exists(pjoin('tmp', os.path.basename(file) + '.hash')):
        with open(pjoin('tmp', os.path.basename(file) + '.hash')) as f:
            prev_hash = f.read()

    return prev_hash == cur_hash


def write_hash(file, info=''):
    cur_hash = get_hash(file, info)
    with open(pjoin('tmp', os.path.basename(file) + '.hash'), 'w') as f:
        f.write(cur_hash)


def compile_file(file: str, target='', use_testlib=False, flags=''):
    print('Compiling {:s} (from {:s})...'.format(target, file))

    if file.endswith('.c') or file.endswith('.cpp'):  # C or C++
        if not os.path.exists('tmp'):
            os.mkdir('tmp')

        out = pjoin('tmp', os.path.basename(file) + '.out')

        if check_hash(file):
            print('Using previous version of binary\n')
            return out  # TODO check for preprocessor and compiler flags

        cxx_compiler = 'g++ -O2 -Wall -std=c++11 {} '.format(flags)
        if use_testlib:
            cxx_compiler += '-I{0} '.format(pjoin('..', '..', 'lib'))

        res = os.system('{:s} "{:s}" -o {:s}'.format(cxx_compiler, file, out))

        if not res == 0:
            raise Exception('Compilation error ({})'.format(file))

        write_hash(file)

        print()
        return out

    if file.endswith('.java'):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        out_folder = pjoin('tmp', os.path.basename(file[:-len('.java')]))
        if not os.path.exists(out_folder):
            os.mkdir(out_folder)

        out = 'java -cp {0} -Xmx256M -Xss64M {1}'.format(out_folder, os.path.basename(file[:-len('.java')]))

        if check_hash(file):
            print('Using previous version of binary\n')
            return out  # TODO check for preprocessor and compiler flags

        java_compiler = 'javac {0}'.format(flags)  # TODO java testlib
        res = os.system('{0:s} "{1:s}" -d {2:s}'.format(java_compiler, file, out_folder))

        if not res == 0:
            raise Exception('Compilation error ({})'.format(file))

        write_hash(file)

        print()
        return out

    if file.endswith('.py'):
        return 'python3 ' + file


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
            self.problem_cfg = configparser.ConfigParser()
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