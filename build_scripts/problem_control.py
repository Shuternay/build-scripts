#!/usr/bin/python3.3
import argparse
import datetime
import os
import pkgutil
import random
import shutil
import stat
import subprocess
import ftplib
import netrc
import time

from build_scripts import tex2xml
from build_scripts import misc
from build_scripts.misc import write_log


pjoin = os.path.join

__author__ = 'ksg'
TL = 3.0
DEFAULT_TEST_NUM_WIDTH = 2


class Test:
    """iterator that returns tests in specified folder"""

    def __init__(self, folder, test_num):
        self.folder = folder
        self.test_num = test_num
        if not os.path.exists(folder):
            raise Exception('Folder with tests does not exists')
        name_width = cfg.get_problem_param('test_num_width') or str(DEFAULT_TEST_NUM_WIDTH)
        self.str_format = '{:0>' + name_width + 'd}'  # '{:0>2d}'

    def exists(self):
        return os.path.exists(pjoin(self.folder, self.str_format.format(self.test_num)))

    def test_num(self):
        return self.test_num

    def inf_path(self):
        return pjoin(self.folder, self.str_format.format(self.test_num))

    def ans_path(self):
        return pjoin(self.folder, (self.str_format + '.a').format(self.test_num))

    def sample_inf_path(self, samples_folder):
        return pjoin(samples_folder, (self.str_format + '.t').format(self.test_num))

    def sample_ans_path(self, samples_folder):
        return pjoin(samples_folder, (self.str_format + '.t.a').format(self.test_num))

    def inf_name(self):
        return self.str_format.format(self.test_num)

    def ans_name(self):
        return (self.str_format + '.a').format(self.test_num)

    def open_inf(self, mode='r'):
        return open(self.inf_path(), mode)

    def open_ans(self, mode='r'):
        return open(self.ans_path(), mode)

    @staticmethod
    def test_gen(folder):
        test_cnt = 1
        while Test(folder, test_cnt).exists():
            yield Test(folder, test_cnt)
            test_cnt += 1

    @classmethod
    def test_len(cls, folder):
        test_cnt = 0
        while cls(folder, test_cnt + 1).exists():
            test_cnt += 1
        return test_cnt


def validate_tests(args=None):
    validator_path = cfg.get_problem_param('validator', True) or 'validator.cpp'
    validator_path = os.path.normpath(validator_path)

    validator_ex = misc.compile_file(validator_path, 'validator', True)

    if not os.path.exists(pjoin('tmp', 'log')):
        os.mkdir(pjoin('tmp', 'log'))
    log_file_name = pjoin('tmp', 'log', '{}.log'.format(os.path.basename(validator_path)))
    write_log('\nValidating tests ({})...'.format(datetime.datetime.today()), file=log_file_name)

    ok_count = 0

    for t in Test.test_gen('tests'):
        write_log(('test ' + t.str_format + ': ').format(t.test_num), end='', file=log_file_name)

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

    write_log('correct {:d} from {:d}'.format(ok_count, Test.test_len('tests')), file=log_file_name)
    print('Validating complete\n')

    return [ok_count, Test.test_len('tests')]


def build_tests(args):
    main_solution = args['main_solution'] or cfg.get_main_solution()

    gen_path = cfg.get_problem_param('gen', True) or 'gen.cpp'
    gen_path = os.path.normpath(gen_path)
    gen_ex = misc.compile_file(gen_path, 'gen', True)

    if not os.path.exists(pjoin('tmp', 'log')):
        os.mkdir(pjoin('tmp', 'log'))
    log_file_name = pjoin('tmp', 'log', 'gen_{}.log'.format(os.path.basename(main_solution)))
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

    for t in Test.test_gen('tests'):
        write_log(('test ' + t.str_format + ': ').format(t.test_num), end="", file=log_file_name)

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

    if cfg.get_problem_param('samples_num', True):
        samples_num = int(cfg.get_problem_param('samples_num'))
        samples_folder = cfg.get_problem_param('samples_folder', True) or 'samples'
        if os.path.exists(samples_folder):
            shutil.rmtree(samples_folder)
        os.mkdir(samples_folder)
        for i in range(1, samples_num + 1):
            shutil.copy2(Test('tests', i).inf_path(), Test('tests', i).sample_inf_path(samples_folder))
            shutil.copy2(Test('tests', i).ans_path(), Test('tests', i).sample_ans_path(samples_folder))


def check_solution(args):
    solution = args['solution'] or cfg.get_main_solution()
    sol_ex = misc.compile_file(solution, 'solution')

    checker_path = cfg.get_problem_param('checker', True) or 'checker.cpp'
    checker_path = os.path.normpath(checker_path)
    check_ex = misc.compile_file(checker_path, 'checker', True)

    if not os.path.exists(pjoin('tmp', 'log')):
        os.mkdir(pjoin('tmp', 'log'))
    log_file_name = pjoin('tmp', 'log', '{}.log'.format(os.path.basename(solution)))
    write_log('\nChecking solution ({})...'.format(datetime.datetime.today()), file=log_file_name)

    ok_count = 0
    for t in Test.test_gen('tests'):
        write_log(('test ' + t.str_format + ': ').format(t.test_num), end='', file=log_file_name)

        try:
            with t.open_inf('r') as inf, open(pjoin('tmp', 'problem.out'), 'w') as ouf:
                res = subprocess.call(sol_ex.split(), stdin=inf, stdout=ouf, timeout=TL)
        except subprocess.TimeoutExpired:
            write_log('Time-limit error ({} s.)'.format(TL), file=log_file_name)
            continue

        if not res == 0:
            write_log('Run-time error [{}]'.format(res), file=log_file_name)
            continue

        process = subprocess.Popen([check_ex, t.inf_path(), pjoin('tmp', 'problem.out'), t.ans_path()],
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

        os.remove(pjoin('tmp', 'problem.out'))

    write_log('passed {:d} from {:d}'.format(ok_count, Test.test_len('tests')), end='\n\n', file=log_file_name)

    return [ok_count, Test.test_len('tests')]


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

    gen_path = cfg.get_problem_param('gen', True) or 'gen.cpp'
    gen_path = os.path.normpath(gen_path)

    checker_path = cfg.get_problem_param('checker', True) or 'checker.cpp'
    checker_path = os.path.normpath(checker_path)

    gen_ex = misc.compile_file(gen_path, 'gen', True)
    check_ex = misc.compile_file(checker_path, 'check', True)
    m_sol_ex = misc.compile_file(model_solution_path, 'model_solution')
    u_sol_ex = misc.compile_file(user_solution_path, 'user_solution')

    mtl = args['MTL'] or 5
    tl = args['TL'] or 2

    if os.path.exists('stress_tests'):
        shutil.rmtree('stress_tests')
    os.mkdir('stress_tests')

    if not os.path.exists(pjoin('tmp', 'log')):
        os.mkdir(pjoin('tmp', 'log'))
    log_file_name = pjoin('tmp', 'log', 'stress_{}.log'.format(os.path.basename(user_solution_path)))
    write_log('\nStart stress testing({})...'.format(datetime.datetime.today()), file=log_file_name)

    n = args['num'] or -1
    cur_test = 0
    ok_count = 0

    while cur_test < n or n == -1:
        cur_test += 1
        write_log('{:0>4d}: '.format(cur_test), end='', file=log_file_name)

        for suf in ['in', 'out', 'ans']:
            if os.path.exists(pjoin('tmp', 'problem.' + suf)):
                os.remove(pjoin('tmp', 'problem.' + suf))

        res = os.system('{:s} 2 "{}" 1> {}'.format(gen_ex, random.randint(0, 10 ** 18),
                                                   pjoin('tmp', 'problem.in')))
        if not res == 0:
            raise Exception('Generator error')

        try:
            with open(pjoin('tmp', 'problem.in'), 'r') as inf, open(pjoin('tmp', 'problem.ans'), 'w') as ans:
                res = subprocess.call(m_sol_ex.split(), stdin=inf, stdout=ans, timeout=mtl)
        except subprocess.TimeoutExpired:
            write_log('Time-limit error at model solution ({} s.)'.format(tl), file=log_file_name)
            shutil.copy(pjoin('tmp', 'problem.in'), pjoin('stress_tests', '{:0>3d}'.format(cur_test)))
            shutil.copy(pjoin('tmp', 'problem.ans'), pjoin('stress_tests', '{:0>3d}.a'.format(cur_test)))
            continue

        if not res == 0:
            write_log('Run-time error at model solution [{}]'.format(res), file=log_file_name)
            shutil.copy(pjoin('tmp', 'problem.in'), pjoin('stress_tests', '{:0>3d}'.format(cur_test)))
            shutil.copy(pjoin('tmp', 'problem.ans'), pjoin('stress_tests', '{:0>3d}.a'.format(cur_test)))
            continue

        try:
            with open(pjoin('tmp', 'problem.in'), 'r') as inf, open(pjoin('tmp', 'problem.out'), 'w') as ans:
                res = subprocess.call(u_sol_ex.split(), stdin=inf, stdout=ans, timeout=tl)
        except subprocess.TimeoutExpired:
            write_log('Time-limit error ({} s.)'.format(tl), file=log_file_name)
            shutil.copy(pjoin('tmp', 'problem.in'), pjoin('stress_tests', '{:0>3d}'.format(cur_test)))
            shutil.copy(pjoin('tmp', 'problem.ans'), pjoin('stress_tests', '{:0>3d}.a'.format(cur_test)))
            shutil.copy(pjoin('tmp', 'problem.out'), pjoin('stress_tests', '{:0>3d}.out'.format(cur_test)))
            continue

        if not res == 0:
            write_log('Run-time error [{}]'.format(res), file=log_file_name)
            shutil.copy(pjoin('tmp', 'problem.in'), pjoin('stress_tests', '{:0>3d}'.format(cur_test)))
            shutil.copy(pjoin('tmp', 'problem.ans'), pjoin('stress_tests', '{:0>3d}.a'.format(cur_test)))
            shutil.copy(pjoin('tmp', 'problem.out'), pjoin('stress_tests', '{:0>3d}.out'.format(cur_test)))
            continue

        process = subprocess.Popen([check_ex,
                                    pjoin('tmp', 'problem.in'),
                                    pjoin('tmp', 'problem.out'),
                                    pjoin('tmp', 'problem.ans')],
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
            shutil.copy(pjoin('tmp', 'problem.in'), pjoin('stress_tests', '{:0>3d}'.format(cur_test)))
            shutil.copy(pjoin('tmp', 'problem.ans'), pjoin('stress_tests', '{:0>3d}.a'.format(cur_test)))
            shutil.copy(pjoin('tmp', 'problem.out'), pjoin('stress_tests', '{:0>3d}.out'.format(cur_test)))

    write_log('passed {:d} from {:d}'.format(ok_count, n), end='\n\n', file=log_file_name)

    return [ok_count, n]


def build_st(args):
    with open(pjoin('statement', cfg.get_problem_param('short name') + '.tex')) as fin:
        with open(pjoin('statement', 'statement.xml'), 'w') as fout:
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
            checker_path = cfg.get_problem_param('checker', True) or 'checker.cpp'
            checker_path = os.path.normpath(checker_path)
            with open(checker_path, 'rb') as f:
                ftp.storbinary('STOR checker.cpp', f)

        if args['validator']:
            print('Uploading validator')
            validator_path = cfg.get_problem_param('validator', True) or 'validator.cpp'
            validator_path = os.path.normpath(validator_path)
            with open(validator_path, 'rb') as f:
                ftp.storbinary('STOR validator.cpp', f)

        if args['testlib']:
            print('Uploading testlib')
            with open('../../lib/testlib.h', 'rb') as f:
                ftp.storbinary('STOR testlib.h', f)

        if args['tests']:
            print('Uploading tests')
            for t in Test.test_gen('tests'):
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
    problem_path = pjoin(contest_root, 'problems', problem_name)

    if os.path.exists(problem_name):
        raise ValueError('folder with the same name ({0}) exists'.format(problem_name))

    os.mkdir(problem_path)
    os.mkdir(pjoin(problem_path, 'solutions'))
    os.mkdir(pjoin(problem_path, 'statement'))

    files = [
        #(source, destination, extract variables),
        ('checker.cpp', 'checker.cpp', False),
        ('gen.cpp', 'gen.cpp', False),
        ('validator.cpp', 'validator.cpp', False),
        ('sol.cpp', 'solutions/{0}.cpp'.format(problem_name), False),
        ('problem.conf', 'problem.conf', True),
        ('st.tex', 'statement/{0}.tex'.format(problem_name), False),
        ('valuer.cfg', 'valuer.cfg', False),
    ]

    for src, dst, ext in files:
        with open(os.path.join(problem_path, dst), 'w') as f:
            data = str(pkgutil.get_data('build_scripts', os.path.join('data', 'bootstrap', src)), 'utf-8')
            if ext:
                data = data.format(problem_name)
            f.write(data)


def add_contest(args):
    name = args['name']
    if os.path.exists(name):
        raise ValueError('folder with the same name ({0}) exists'.format(name))

    os.mkdir(name)
    os.mkdir(pjoin(name, 'statements'))
    os.mkdir(pjoin(name, 'problems'))
    os.mkdir(pjoin(name, 'lib'))

    files = [
        #(source, destination),
        ('problems.tex', 'statements/problems.tex'),
        ('olymp.sty', 'statements/olymp.sty'),
        ('contest.conf', 'contest.conf'),
        ('import.sty', 'statements/import.sty'.format(name)),
        ('clean.sh', 'statements/clean.sh'.format(name)),
        ('r.sh', 'statements/r.sh'.format(name)),
        ('r.cmd', 'statements/r.cmd'.format(name)),
    ]

    for src, dst in files:
        with open(os.path.join(name, dst), 'w') as f:
            data = str(pkgutil.get_data('build_scripts', os.path.join('data', 'bootstrap', src)), 'utf-8')
            f.write(data)

    with open(pjoin(name, 'lib', 'testlib.h'), 'w') as f:
        data = str(pkgutil.get_data('build_scripts', pjoin('data', 'testlib.h')), 'utf-8')
        f.write(data)

        for file in ('r.sh', 'r.cmd', 'clean.sh'):
            os.chmod(os.path.join(name, 'statements', file), stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)


def main():
    global cfg
    cfg = misc.Config()

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(help='sub-command help')

    # (build) build tests
    parser_build = subparsers.add_parser('build', help='build tests and gen answers')
    parser_build.add_argument('main_solution', nargs='?', help='model solution for answers')
    parser_build.set_defaults(func=build_tests)

    # (check) check solution
    parser_check = subparsers.add_parser('check', help='Check solution on tests')
    parser_check.add_argument('solution', nargs='?', help='path to solution for check')
    parser_check.set_defaults(func=check_solution)

    # (check_all) check all solutions
    parser_check_all = subparsers.add_parser('check_all', help='check all solutions')
    parser_check_all.set_defaults(func=check_all_solutions)

    # (validate )validate tests
    parser_validate = subparsers.add_parser('validate', help='validate tests')
    parser_validate.set_defaults(func=validate_tests)

    # (stress) stress testing of solution
    parser_stress = subparsers.add_parser('stress', help='stress testing')
    parser_stress.add_argument('solution', help='path to solution for check')
    parser_stress.add_argument('model_solution', nargs='?', help='model solution for answers')
    parser_stress.add_argument('-n', '--num', type=int, help='number of tests')
    parser_stress.add_argument('--MTL', type=float, help='Time limit for model solution')
    parser_stress.add_argument('--TL', type=float, help='Time limit for user solution')
    parser_stress.set_defaults(func=stress_test)

    # (build_st) build statement.xml
    parser_build_st = subparsers.add_parser('build_st', help='build statement.xml from .tex statement')
    parser_build_st.set_defaults(func=build_st)

    # (upload) upload files to server
    parser_upload = subparsers.add_parser('upload', help='upload data on contest server')
    parser_upload.add_argument('-t', '--tests', action='store_true', help='upload tests')
    parser_upload.add_argument('-c', '--checker', action='store_true', help='upload checker sources')
    parser_upload.add_argument('-v', '--validator', action='store_true', help='upload validator sources')
    parser_upload.add_argument('-l', '--testlib', action='store_true', help='upload testlib.h')
    parser_upload.add_argument('-s', '--statement', action='store_true', help='upload statement.xml')
    parser_upload.add_argument('-g', '--gvaluer', action='store_true', help='upload valuer.cfg')
    parser_upload.set_defaults(func=upload)

    # (clean) clean tmp files
    parser_clean = subparsers.add_parser('clean', help='clean')
    parser_clean.set_defaults(func=clean)

    # (add) add new problem
    parser_add = subparsers.add_parser('add', help='add problem')
    parser_add.add_argument('name', help='problem name')
    parser_add.set_defaults(func=add)

    # (add_contest) add new contest
    parser_add_contest = subparsers.add_parser('add_contest', help='create new contest')
    parser_add_contest.add_argument('name', help='contest name')
    parser_add_contest.set_defaults(func=add_contest)

    in_args = parser.parse_args()
    if in_args.__contains__('func'):
        in_args.func(vars(in_args))
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
