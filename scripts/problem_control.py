#!/usr/bin/python3.3
import argparse
import datetime
import os
import random
import shutil
import subprocess
import ftplib
import netrc
import time
import sys

import tex2xml
import misc
from misc import write_log


__author__ = 'ksg'
TL = 3.0


class Test:
    """iterator that returns tests in specified folder"""

    def __init__(self, folder):
        self.folder = folder
        self.test_cnt = 0
        if not os.path.exists(folder):
            raise Exception('Folder with tests does not exists')

    def __iter__(self):
        self.test_cnt = 0
        return self

    def __next__(self):
        self.test_cnt += 1
        if not os.path.exists(os.path.join(self.folder, '{:0>2d}'.format(self.test_cnt))):
            raise StopIteration

        return self

    def __len__(self):
        len = 1
        while os.path.exists(os.path.join(self.folder, '{:0>2d}'.format(len))):
            len += 1
        return len - 1

    def test_num(self):
        return self.test_cnt

    def inf_path(self):
        return os.path.join(self.folder, "{:0>2d}".format(self.test_cnt))

    def ans_path(self):
        return os.path.join(self.folder, "{:0>2d}.a".format(self.test_cnt))

    def inf_name(self):
        return "{:0>2d}".format(self.test_cnt)

    def ans_name(self):
        return "{:0>2d}.a".format(self.test_cnt)

    def open_inf(self, mode='r'):
        return open(self.inf_path(), mode)

    def open_ans(self, mode='r'):
        return open(self.ans_path(), mode)


def validate_tests(args=None):
    validator = 'validator/validator.cpp'

    validator_ex = misc.compile_file(validator, 'validator', True)

    if not os.path.exists('tmp/log'):
        os.mkdir('tmp/log')
    log_file_name = os.path.join('tmp/log', '{}.log'.format(os.path.basename(validator)))
    write_log('\nValidating tests ({})...'.format(datetime.datetime.today()), file=log_file_name)

    ok_count = 0

    for t in Test('tests'):
        write_log('test {:0>2d}: '.format(t.test_num()), end='', file=log_file_name)

        with t.open_inf() as inf:
            process = subprocess.Popen(validator_ex, stdin=inf, stderr=subprocess.PIPE)
        for line in process.stderr:
            write_log(str(line, 'utf-8').strip(), end='', file=log_file_name)

        time.sleep(0.1)  # FIXME strange RE
        res = process.poll()
        if res == 0:
            ok_count += 1
            write_log('OK', file=log_file_name)
        else:
            write_log(' [{}]'.format(res), file=log_file_name)

    write_log('correct {:d} from {:d}'.format(ok_count, len(Test('tests'))), file=log_file_name)
    print('Validating complete\n')

    return [ok_count, len(Test('tests'))]


def build_tests(args):
    main_solution = args['main_solution'] or cfg.get_main_solution()

    gen_ex = misc.compile_file('gen/gen.cpp', 'gen', True)

    if not os.path.exists('tmp/log'):
        os.mkdir('tmp/log')
    log_file_name = os.path.join('tmp/log', 'gen_{}.log'.format(os.path.basename(main_solution)))
    write_log('\nGenerating tests ({})...'.format(datetime.datetime.today()), file=log_file_name)

    if os.path.exists('tests'):
        shutil.rmtree('tests')
    os.mkdir('tests')

    res = os.system('{:s} 0'.format(gen_ex))
    if not res == 0:
        raise Exception('Generator error')

    validate_tests()

    solution_ex = misc.compile_file(main_solution, 'main_solution')

    write_log('\nGenerating answers...', file=log_file_name)

    for t in Test('tests'):
        write_log('test {:0>2d}: '.format(t.test_num()), end="", file=log_file_name)

        with t.open_inf('r') as inf, t.open_ans('w') as ans:
            res = subprocess.call(
                solution_ex.split(),
                stdin=inf,
                stdout=ans)

        if not res == 0:
            write_log("Run-time error [{}]".format(res), file=log_file_name)
            continue
        else:
            write_log("Generated", file=log_file_name)


def check_solution(args):
    solution = args['solution'] or cfg.get_main_solution()
    sol_ex = misc.compile_file(solution, 'solution')

    check_ex = misc.compile_file('check/check.cpp', 'check', True)

    if not os.path.exists('tmp/log'):
        os.mkdir('tmp/log')
    log_file_name = os.path.join('tmp/log', '{}.log'.format(os.path.basename(solution)))
    write_log('\nChecking solution ({})...'.format(datetime.datetime.today()), file=log_file_name)

    ok_count = 0
    for t in Test('tests'):
        write_log('test {:0>2d}: '.format(t.test_num()), end='', file=log_file_name)

        try:
            with t.open_inf('r') as inf, open('tmp/problem.out', 'w') as ouf:
                res = subprocess.call(sol_ex.split(), stdin=inf, stdout=ouf, timeout=TL)
        except subprocess.TimeoutExpired:
            write_log('Time-limit error ({} s.)'.format(TL), file=log_file_name)
            continue

        if not res == 0:
            write_log('Run-time error [{}]'.format(res), file=log_file_name)
            continue

        process = subprocess.Popen([check_ex, t.inf_path(), 'tmp/problem.out', t.ans_path()],
                                   stderr=subprocess.PIPE)
        for line in process.stderr:
            write_log(str(line, 'utf-8').strip(), end='', file=log_file_name)

        time.sleep(0.1)  # FIXME strange RE
        res = process.poll()
        if res == 0:
            write_log('', file=log_file_name)
            ok_count += 1
        else:
            write_log(' [{}]'.format(res), file=log_file_name)

        os.remove('tmp/problem.out')

    write_log('passed {:d} from {:d}'.format(ok_count, len(Test('tests'))), end='\n\n', file=log_file_name)

    return [ok_count, len(Test('tests'))]


def check_all_solutions(args):
    solutions = cfg.get_solutions()

    results = []
    for sol in solutions:
        results.append(check_solution({'solution': sol[1]}))

    for sol, res in zip(solutions, results):
        print('{} ({}): [{} / {}]'.format(sol[0], sol[1], res[0], res[1]))


def stress_test(args):
    model_solution_path = args['model_solution'] or cfg.get_main_solution()
    user_solution_path = args['solution']
    gen_path = 'gen/gen.cpp'
    checker_path = 'check/check.cpp'

    gen_ex = misc.compile_file(gen_path, 'gen', True)
    check_ex = misc.compile_file(checker_path, 'check', True)
    m_sol_ex = misc.compile_file(model_solution_path, 'model_solution')
    u_sol_ex = misc.compile_file(user_solution_path, 'user_solution')

    mtl = args['MTL'] or 5
    tl = args['TL'] or 2

    if os.path.exists('stress_tests'):
        shutil.rmtree('stress_tests')
    os.mkdir('stress_tests')

    if not os.path.exists('tmp/log'):
        os.mkdir('tmp/log')
    log_file_name = os.path.join('tmp/log', 'stress_{}.log'.format(os.path.basename(user_solution_path)))
    write_log('\nStart stress testing({})...'.format(datetime.datetime.today()), file=log_file_name)

    n = args['num'] or -1
    cur_test = 0
    ok_count = 0

    while cur_test < n or n == -1:
        cur_test += 1
        write_log('{:0>3d}: '.format(cur_test), end='', file=log_file_name)

        for suf in ['in', 'out', 'ans']:
            if os.path.exists('tmp/problem.' + suf):
                os.remove('tmp/problem.' + suf)

        res = os.system('{:s} 2 "{}" 1>tmp/problem.in'.format(gen_ex, random.randint(0, 10 ** 18)))
        if not res == 0:
            raise Exception('Generator error')

        try:
            with open('tmp/problem.in', 'r') as inf, open('tmp/problem.ans', 'w') as ans:
                res = subprocess.call(m_sol_ex.split(), stdin=inf, stdout=ans, timeout=mtl)
        except subprocess.TimeoutExpired:
            write_log('Time-limit error at model solution ({} s.)'.format(tl), file=log_file_name)
            shutil.copy('tmp/problem.in', 'stress_tests/{:0>3d}'.format(cur_test))
            shutil.copy('tmp/problem.ans', 'stress_tests/{:0>3d}.a'.format(cur_test))
            continue

        if not res == 0:
            write_log('Run-time error at model solution [{}]'.format(res), file=log_file_name)
            shutil.copy('tmp/problem.in', 'stress_tests/{:0>3d}'.format(cur_test))
            shutil.copy('tmp/problem.ans', 'stress_tests/{:0>3d}.a'.format(cur_test))
            continue

        try:
            with open('tmp/problem.in', 'r') as inf, open('tmp/problem.out', 'w') as ans:
                res = subprocess.call(u_sol_ex.split(), stdin=inf, stdout=ans, timeout=tl)
        except subprocess.TimeoutExpired:
            write_log('Time-limit error ({} s.)'.format(tl), file=log_file_name)
            shutil.copy('tmp/problem.in', 'stress_tests/{:0>3d}'.format(cur_test))
            shutil.copy('tmp/problem.ans', 'stress_tests/{:0>3d}.a'.format(cur_test))
            shutil.copy('tmp/problem.out', 'stress_tests/{:0>3d}.out'.format(cur_test))
            continue

        if not res == 0:
            write_log('Run-time error [{}]'.format(res), file=log_file_name)
            shutil.copy('tmp/problem.in', 'stress_tests/{:0>3d}'.format(cur_test))
            shutil.copy('tmp/problem.ans', 'stress_tests/{:0>3d}.a'.format(cur_test))
            shutil.copy('tmp/problem.out', 'stress_tests/{:0>3d}.out'.format(cur_test))
            continue

        process = subprocess.Popen([check_ex, 'tmp/problem.in', 'tmp/problem.out', 'tmp/problem.ans'],
                                   stderr=subprocess.PIPE)
        for line in process.stderr:
            write_log(str(line, 'utf-8').strip(), end='', file=log_file_name)

        time.sleep(0.1)  # FIXME strange RE
        res = process.poll()
        if res == 0:
            write_log('', file=log_file_name)
            ok_count += 1
        else:
            write_log(' [{}]'.format(res), file=log_file_name)
            shutil.copy('tmp/problem.in', 'stress_tests/{:0>3d}'.format(cur_test))
            shutil.copy('tmp/problem.ans', 'stress_tests/{:0>3d}.a'.format(cur_test))
            shutil.copy('tmp/problem.out', 'stress_tests/{:0>3d}.out'.format(cur_test))

    write_log('passed {:d} from {:d}'.format(ok_count, n), end='\n\n', file=log_file_name)

    return [ok_count, n]


def build_st(args):
    with open('statement/' + cfg.get_problem_param('short name') + '.tex') as fin:
        with open('statement/statement.xml', 'w') as fout:
            tex2xml.convert(fin, fout,
                            cfg.get_problem_param('system name'),
                            cfg.get_problem_param('source', True),
                            cfg.get_problem_param('pdf link', True))


def upload(args):
    if os.path.exists(os.path.expanduser('~/.netrc')):
        auth_data = netrc.netrc(os.path.expanduser('~/.netrc')).authenticators(cfg.get_contest_host())
    else:
        auth_data = None

    if not auth_data:
        login = input('login: ')
        password = input('password: ')
        auth_data = (login, None, password)

    with ftplib.FTP(cfg.get_contest_host()) as ftp:
        print(ftp.login(auth_data[0], auth_data[2]))
        ftp.cwd(cfg.get_server_contest_path() + 'problems/' + cfg.get_problem_param('system name'))

        if args['checker']:
            print('Uploading checker')
            with open('check/check.cpp', 'rb') as f:
                ftp.storbinary('STOR check.cpp', f)

        if args['validator']:
            print('Uploading validator')
            with open('validator/validator.cpp', 'rb') as f:
                ftp.storbinary('STOR validator.cpp', f)

        if args['testlib']:
            print('Uploading testlib')
            with open('../../lib/testlib.h', 'rb') as f:
                ftp.storbinary('STOR testlib.h', f)

        if args['tests']:
            print('Uploading tests')
            for t in Test('tests'):
                print('uploading {} and {}'.format(t.inf_name(), t.ans_name()))
                with open(t.inf_path(), 'rb') as f:
                    ftp.storbinary('STOR tests/{}'.format(t.inf_name()), f)
                with open(t.ans_path(), 'rb') as f:
                    ftp.storbinary('STOR tests/{}'.format(t.ans_name()), f)

        if args['statement']:
            print('Uploading statement.xml')
            with open('statement/statement.xml', 'rb') as f:
                ftp.storbinary('STOR statement.xml', f)

        if args['gvaluer']:
            print('Uploading valuer.cfg')
            with open('valuer.cfg', 'rb') as f:
                ftp.storbinary('STOR valuer.cfg', f)

        ftp.quit()


def clean(args):
    shutil.rmtree('tests')
    shutil.rmtree('stress_tests')
    shutil.rmtree('tmp')


def add(args):
    contest_root = misc.get_contest_root()
    problem_name = args['name']
    problem_path = os.path.join(contest_root, 'problems', problem_name)
    bootstrap_path = os.path.join(contest_root, 'lib/bootstrap')

    os.mkdir(problem_path)

    os.mkdir(os.path.join(problem_path, 'check'))
    shutil.copy(os.path.join(bootstrap_path, 'check.cpp'), os.path.join(problem_path, 'check/check.cpp'))

    shutil.copytree(os.path.join(bootstrap_path, 'gen'), os.path.join(problem_path, 'gen'))

    shutil.copytree(os.path.join(bootstrap_path, 'validator'), os.path.join(problem_path, 'validator'))

    os.mkdir(os.path.join(problem_path, 'solutions'))
    os.mkdir(os.path.join(problem_path, 'solutions', 'WIP'))
    shutil.copytree(os.path.join(bootstrap_path, 'sol'),
                    os.path.join(problem_path, 'solutions/WIP/' + problem_name + '_ksg'))
    shutil.move(os.path.join(problem_path, 'solutions/WIP/' + problem_name + '_ksg/sol.cpp'),
                os.path.join(problem_path, 'solutions/WIP/{0}_ksg/{0}_ksg.cpp'.format(problem_name)))

    os.mkdir(os.path.join(problem_path, 'statement'))
    shutil.copy(os.path.join(bootstrap_path, 'st.tex'),
                os.path.join(problem_path, 'statement/' + problem_name + '.tex'))

    with open(os.path.join(problem_path, 'problem.conf'), 'w') as f:
        f.write('''\
[general]
title = ???
short name = {0}
system name = {0}
main solution = main_ksg_solution

[main_ksg_solution]
is main = true
path = solutions/{0}_ksg.cpp'''.format(problem_name))


def update_scripts(args):
    dst_folder = os.path.join(misc.get_contest_root(), 'scripts')
    src_folder = os.path.dirname(sys.argv[0])

    if os.path.normpath(os.path.expandvars(dst_folder)) == os.path.normpath(os.path.expandvars(src_folder)):
        raise Exception('dst_path == src_path')

    if os.path.exists(dst_folder):
        shutil.rmtree(dst_folder)

    shutil.copytree(src_folder, dst_folder)


cfg = misc.Config()

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers(help='sub-command help')

parser_build = subparsers.add_parser('build', help='build tests and gen answers')
parser_build.add_argument('main_solution', nargs='?', help='model solution for answers')
parser_build.set_defaults(func=build_tests)

parser_check = subparsers.add_parser('check', help='Check solution on tests')
parser_check.add_argument('solution', nargs='?', help='path to solution for check')
parser_check.set_defaults(func=check_solution)

parser_check_all = subparsers.add_parser('check_all', help='check all solutions')
parser_check_all.set_defaults(func=check_all_solutions)

parser_validate = subparsers.add_parser('validate', help='validate tests')
parser_validate.set_defaults(func=validate_tests)

parser_stress = subparsers.add_parser('stress', help='stress testing')
parser_stress.add_argument('solution', help='path to solution for check')
parser_stress.add_argument('model_solution', nargs='?', help='model solution for answers')
parser_stress.add_argument('-n', '--num', type=int, help='number of tests')
parser_stress.add_argument('--MTL', type=float, help='Time limit for model solution')
parser_stress.add_argument('--TL', type=float, help='Time limit for user solution')
parser_stress.set_defaults(func=stress_test)

parser_build_st = subparsers.add_parser('build_st', help='build statement.xml from .tex statement')
parser_build_st.set_defaults(func=build_st)

parser_upload = subparsers.add_parser('upload', help='upload data on contest server')
parser_upload.add_argument('-t', '--tests', action='store_true', help='upload tests')
parser_upload.add_argument('-c', '--checker', action='store_true', help='upload checker sources')
parser_upload.add_argument('-v', '--validator', action='store_true', help='upload validator sources')
parser_upload.add_argument('-l', '--testlib', action='store_true', help='upload testlib.h')
parser_upload.add_argument('-s', '--statement', action='store_true', help='upload statement.xml')
parser_upload.add_argument('-g', '--gvaluer', action='store_true', help='upload valuer.cfg')
parser_upload.set_defaults(func=upload)

parser_clean = subparsers.add_parser('clean', help='clean')
parser_clean.set_defaults(func=clean)

parser_add = subparsers.add_parser('add', help='add problem')
parser_add.add_argument('name', help='problem name')
parser_add.set_defaults(func=add)

parser_update = subparsers.add_parser('update', help='update scripts in current contest directory')
parser_update.set_defaults(func=update_scripts)

in_args = parser.parse_args()
if in_args.__contains__('func'):
    in_args.func(vars(in_args))
else:
    parser.print_help()