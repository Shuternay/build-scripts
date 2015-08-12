# !/usr/bin/python3
import argparse
import datetime
import ftplib
import netrc
import pkgutil
import subprocess

import os
import random
import shutil
import stat

from build_scripts import tex2xml
from build_scripts import misc
from build_scripts.misc import write_log
from build_scripts.executable import Executable
import build_scripts.polygon

pjoin = os.path.join

__author__ = 'ksg'
DEFAULT_TL = 3.0
DEFAULT_ML = 512
DEFAULT_TEST_NUM_WIDTH = 2


class CheckException(Exception):
    def __init__(self, msg: str=''):
        self.msg = msg


class Test:
    """iterator that returns tests in specified folder"""

    def __init__(self, folder, test_num):
        self.folder = folder
        self.test_num = test_num
        if not os.path.exists(folder):
            raise Exception('Folder with tests does not exists')
        name_width = cfg.get_problem_param('test_num_width') or str(DEFAULT_TEST_NUM_WIDTH)
        self.str_format = '{:0>' + str(name_width) + 'd}'  # '{:0>2d}'

    def exists(self):
        return os.path.exists(pjoin(self.folder, self.str_format.format(self.test_num)))

    def test_num_as_str(self):
        return self.str_format.format(self.test_num)

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


def validate_single_test(test, validator_ex):
    try:
        with test.open_inf() as inf:
            res = validator_ex.execute(stdin=inf, stderr=subprocess.PIPE)

        if res.returncode == 0:
            score = 1
            msg = 'OK' + (' ({0})'.format(res.stderr) if res.stderr else '')
            status = 'OK'
        else:
            score = 0
            msg = '{0} [{1}]'.format(res.stderr, res.returncode)
            status = 'FL'

    except KeyboardInterrupt:
        score = 0
        msg = 'Interrupted'
        status = 'IR'

    return score, status, msg


def validate_tests(args=None):
    validator_path = cfg.get_problem_param('validator', True) or 'validator.cpp'
    validator_path = os.path.normpath(validator_path)

    validator_ex = Executable(validator_path, 'validator', True)

    if not os.path.exists(pjoin('tmp', 'log')):
        os.mkdir(pjoin('tmp', 'log'))
    log_file_name = pjoin('tmp', 'log', '{}.log'.format(os.path.basename(validator_path)))
    write_log('\nValidating tests ({0})...'.format(datetime.datetime.today()), file=log_file_name)

    ok_count = 0

    for t in Test.test_gen('tests'):
        score, status, msg = validate_single_test(t, validator_ex)

        if status == 'IR':
            break

        ok_count += score
        write_log('test {0}: {1}'.format(t.test_num_as_str(), msg))

    write_log('correct {0} from {1}'.format(ok_count, Test.test_len('tests')), file=log_file_name)
    print('Validating complete\n')

    return [ok_count, Test.test_len('tests')]


def build_tests(args):
    if cfg.get_problem_param('use_doall', True):
        print('using doall script for tests building\n')
        os.system(cfg.get_problem_param('doall_cmd', True) or 'sh doall.sh')
        return

    gen_path = cfg.get_problem_param('gen', True) or 'gen.cpp'
    gen_path = os.path.normpath(gen_path) or '.'
    gen_work_dir = cfg.get_problem_param('gen_work_dir', True)
    gen_ex = Executable(gen_path, 'gen', True, work_dir=gen_work_dir)

    ml = args['ml'] or cfg.get_problem_param('ml', True) or DEFAULT_ML
    ml = int(ml)  # because cfg.get_problem_param() returns string or None

    main_solution = args['main_solution'] or cfg.get_main_solution()
    solution_ex = Executable(main_solution, 'main_solution', ml=ml)

    if not os.path.exists(pjoin('tmp', 'log')):
        os.mkdir(pjoin('tmp', 'log'))
    log_file_name = pjoin('tmp', 'log', 'gen_{}.log'.format(os.path.basename(main_solution)))
    write_log('\nGenerating tests ({})...'.format(datetime.datetime.today()), file=log_file_name)

    if os.path.exists('tests'):
        shutil.rmtree('tests')
    os.mkdir('tests')

    res = gen_ex.execute(args='0')
    if res.returncode != 0:
        raise Exception('Generator error')

    validate_tests()

    solution_ex.finish_compilation()

    write_log('\nGenerating answers...', file=log_file_name)

    for t in Test.test_gen('tests'):
        write_log(('test ' + t.str_format + ': ').format(t.test_num), end="", file=log_file_name)

        with t.open_inf('r') as inf, t.open_ans('w') as ans:
            res = solution_ex.execute(stdin=inf, stdout=ans)

        if not res.returncode == 0:
            write_log("Run-time error [{}]".format(res.returncode), file=log_file_name)
            continue
        else:
            write_log("Generated, time = {0:.2f}".format(res.exec_time), file=log_file_name)

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
    tl = args['tl'] or cfg.get_problem_param('tl', True) or DEFAULT_TL
    tl = float(tl)  # because cfg.get_problem_param() returns string or None

    ml = args['ml'] or cfg.get_problem_param('ml', True) or DEFAULT_ML
    ml = int(ml)  # because cfg.get_problem_param() returns string or None

    solution = args['solution'] or cfg.get_main_solution()
    sol_ex = Executable(solution, 'solution', ml=ml)

    checker_path = cfg.get_problem_param('checker', True) or 'check.cpp'
    checker_path = os.path.normpath(checker_path)
    check_ex = Executable(checker_path, 'checker', True)

    sol_ex.finish_compilation()
    check_ex.finish_compilation()

    if not os.path.exists(pjoin('tmp', 'log')):
        os.mkdir(pjoin('tmp', 'log'))
    log_file_name = pjoin('tmp', 'log', '{}.log'.format(os.path.basename(solution)))
    write_log('\nChecking solution {0} ({1})...'.format(solution, datetime.datetime.today()), file=log_file_name)

    ok_count = 0
    for t in Test.test_gen('tests'):
        try:
            time = 0
            try:
                with t.open_inf('r') as inf, open(pjoin('tmp', 'problem.out'), 'w') as ouf:
                    res = sol_ex.execute(stdin=inf, stdout=ouf, tl=tl)
                    time = res.exec_time
            except subprocess.TimeoutExpired:
                raise CheckException('Time-limit error ({} s.)'.format(tl))

            if res.returncode != 0:
                raise CheckException('Run-time error [{}]'.format(res.returncode))

            res = check_ex.execute(args=' '.join((t.inf_path(), pjoin('tmp', 'problem.out'), t.ans_path())),
                                   stderr=subprocess.PIPE)

            if res.returncode != 0:
                raise CheckException('{} [{}]'.format(res.stderr, res.returncode))

            os.remove(pjoin('tmp', 'problem.out'))

        except KeyboardInterrupt:
            msg = 'Interrupted'
            break

        except CheckException as ce:
            msg = ce.msg
        else:
            msg = '{}'.format(res.stderr) if res.stderr else 'OK'
            ok_count += 1
        finally:
            if os.path.exists(pjoin('tmp', 'problem.out')):
                os.remove(pjoin('tmp', 'problem.out'))
            write_log('test {0}: time = {2:.2f}, {1}'.format(t.test_num_as_str(), msg, time))

    write_log('passed {:d} from {:d}'.format(ok_count, Test.test_len('tests')), end='\n\n', file=log_file_name)

    return [ok_count, Test.test_len('tests')]


def check_all_solutions(args):
    solutions = cfg.get_solutions()

    results = []
    for sol in solutions:
        args.update({'solution': sol[1]})
        results.append(check_solution(args))

    for sol, res in zip(solutions, results):
        print('{} ({}): [{} / {}]'.format(sol[0], sol[1], res[0], res[1]))


def stress_test(args):
    mtl = args['mtl'] or 5
    tl = args['tl'] or cfg.get_problem_param('tl', True) or DEFAULT_TL
    tl = float(tl)  # because cfg.get_problem_param returns string or None

    ml = args['ml'] or cfg.get_problem_param('ml', True) or DEFAULT_ML
    ml = int(ml)  # because cfg.get_problem_param() returns string or None

    model_solution_path = args['model_solution'] or cfg.get_main_solution()
    user_solution_path = args['solution']

    gen_path = cfg.get_problem_param('gen', True) or 'gen.cpp'
    gen_path = os.path.normpath(gen_path)

    checker_path = cfg.get_problem_param('checker', True) or 'check.cpp'
    checker_path = os.path.normpath(checker_path)

    gen_ex = Executable(gen_path, 'gen', True)
    check_ex = Executable(checker_path, 'checker', True)
    m_sol_ex = Executable(model_solution_path, 'model_solution', ml=ml)
    u_sol_ex = Executable(user_solution_path, 'user_solution', ml=ml)

    gen_ex.finish_compilation()
    check_ex.finish_compilation()
    m_sol_ex.finish_compilation()
    u_sol_ex.finish_compilation()

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

        for suf in ['in', 'out', 'ans']:
            if os.path.exists(pjoin('tmp', 'problem.' + suf)):
                os.remove(pjoin('tmp', 'problem.' + suf))

        files = {'inf': pjoin('tmp', 'problem.in')}

        with open(files['inf'], 'w') as inf:
            res = gen_ex.execute(args='2 "{}"'.format(random.randint(0, 10 ** 18)), stdout=inf)
        if not res.returncode == 0:
            raise Exception('Generator error')

        try:
            files['ans'] = pjoin('tmp', 'problem.ans')
            m_time = u_time = 0
            try:
                with open(files['inf'], 'r') as inf, open(files['ans'], 'w') as ans:
                    res = m_sol_ex.execute(stdin=inf, stdout=ans, tl=mtl)
                    m_time = res.exec_time
            except subprocess.TimeoutExpired:
                raise CheckException('Time-limit error at model solution ({} s.)'.format(mtl))

            if res.returncode != 0:
                raise CheckException('Run-time error at model solution [{}]'.format(res.returncode))

            files['out'] = pjoin('tmp', 'problem.out')

            try:
                with open(files['inf'], 'r') as inf, open(files['out'], 'w') as ans:
                    res = u_sol_ex.execute(stdin=inf, stdout=ans, tl=tl)
                    u_time = res.exec_time
            except subprocess.TimeoutExpired:
                raise CheckException('Time-limit error ({} s.)'.format(tl))

            if res.returncode != 0:
                raise CheckException('Run-time error [{}]'.format(res.returncode))

            res = check_ex.execute(args=' '.join([files['inf'], files['out'], files['ans']]),
                                   stderr=subprocess.PIPE)

            if res.returncode != 0:
                raise CheckException('{} [{}]'.format(res.stderr, res.returncode))

        except KeyboardInterrupt:
            msg = 'Interrupted'
            break

        except CheckException as ce:
            msg = ce.msg
            for name, suf in (('inf', ''), ('out', '.out'), ('ans', '.a')):
                if name in files and os.path.exists(files[name]):
                    shutil.copy2(files[name], pjoin('stress_tests', '{0:0>4d}{1}'.format(cur_test, suf)))
        else:
            msg = '{}'.format(res.stderr) if res.stderr else 'OK'
            ok_count += 1
        finally:
            for file in files.values():
                os.remove(file)
            write_log('test {0:0>4d}: m_time = {2:.2f}, u_time = {3:.2f}, {1}'.format(cur_test, msg, m_time, u_time))

    write_log('passed {:d} from {:d}'.format(ok_count, n), end='\n\n', file=log_file_name)

    return [ok_count, n]


def build_st(args):
    with open(pjoin('statement',
                    (cfg.get_problem_param('short name') or cfg.get_problem_param('short_name')) + '.tex')) as fin:
        with open(pjoin('statement', 'statement.xml'), 'w') as fout:
            if cfg.get_problem_param('statement_text', True):
                tex2xml.build_empty(cfg.get_problem_param('statement_text'),
                                    cfg.get_problem_param('title'),
                                    cfg.get_problem_param('system name') or cfg.get_problem_param('system_name'),
                                    fout)
            else:
                tex2xml.convert(fin, fout,
                                cfg.get_problem_param('system name') or cfg.get_problem_param('system_name'),
                                cfg.get_problem_param('source', True),
                                cfg.get_problem_param('pdf link', True) or cfg.get_problem_param('pdf_link', True))


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
        ftp.cwd(cfg.get_server_contest_path() + 'problems/' + (
        cfg.get_problem_param('system name') or cfg.get_problem_param('system_name')))

        if args['checker']:
            print('Uploading checker')
            checker_path = cfg.get_problem_param('checker', True) or 'check.cpp'
            checker_path = os.path.normpath(checker_path)
            checker_name = os.path.basename(checker_path)

            with open(checker_path, 'rb') as f:
                ftp.storbinary('STOR {0}'.format(checker_name), f)

        if args['validator']:
            print('Uploading validator')
            validator_path = cfg.get_problem_param('validator', True) or 'validator.cpp'
            validator_path = os.path.normpath(validator_path)
            validator_name = os.path.basename(validator_path)
            with open(validator_path, 'rb') as f:
                ftp.storbinary('STOR {0}'.format(validator_name), f)

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
    if cfg.has_problem_param('use_wipe'):
        print('using wipe script for cleaning\n')
        os.system(cfg.get_problem_param('wipe cmd', True) or 'sh wipe.sh')
        return

    for folder in ('tests', 'stress_tests', 'tmp'):
        if os.path.exists(folder):
            shutil.rmtree(folder)


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
        ('checker.cpp', 'check.cpp', False),
        ('gen.cpp', 'gen.cpp', False),
        ('validator.cpp', 'validator.cpp', False),
        ('sol.cpp', 'solutions/{0}.cpp'.format(problem_name), False),
        ('problem.json', 'problem.json', True),
        ('st.tex', 'statement/{0}.tex'.format(problem_name), False),
        ('valuer.cfg', 'valuer.cfg', False),
    ]

    for src, dst, ext in files:
        with open(os.path.join(problem_path, dst), 'w') as f:
            data = str(pkgutil.get_data('build_scripts', os.path.join('data', 'bootstrap', src)), 'utf-8')
            if ext:
                data = data.replace('{0}', problem_name)
            f.write(data)


def import_polygon_problem(args):
    problem_name = args['name'] or os.path.basename(args['path'])
    if args['name'] is None and problem_name.endswith('.zip'):
        problem_name = problem_name[:-len('.zip')]

    problem_path = os.path.join(misc.get_contest_root(), 'problems', problem_name)

    if os.path.exists(problem_path):
        raise ValueError('folder with the same name ({0}) exists'.format(problem_path))

    os.mkdir(problem_path)

    build_scripts.polygon.import_problem(args['path'], problem_path)


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
        ('contest.json', 'contest.json'),
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
    parser_build.add_argument('--ml', type=float, help='Memory limit for solution')
    parser_build.set_defaults(func=build_tests)

    # (check) check solution
    parser_check = subparsers.add_parser('check', help='Check solution on tests')
    parser_check.add_argument('solution', nargs='?', help='path to solution for check')
    parser_check.add_argument('--tl', type=float, help='Time limit for solution')
    parser_check.add_argument('--ml', type=float, help='Memory limit for solution')
    parser_check.set_defaults(func=check_solution)

    # (check_all) check all solutions
    parser_check_all = subparsers.add_parser('check_all', help='check all solutions')
    parser_check_all.add_argument('--tl', type=float, help='Time limit for solution')
    parser_check_all.add_argument('--ml', type=float, help='Memory limit for solution')
    parser_check_all.set_defaults(func=check_all_solutions)

    # (validate )validate tests
    parser_validate = subparsers.add_parser('validate', help='validate tests')
    parser_validate.set_defaults(func=validate_tests)

    # (stress) stress testing of solution
    parser_stress = subparsers.add_parser('stress', help='stress testing')
    parser_stress.add_argument('solution', help='path to solution for check')
    parser_stress.add_argument('model_solution', nargs='?', help='model solution for answers')
    parser_stress.add_argument('-n', '--num', type=int, help='number of tests')
    parser_stress.add_argument('--mtl', type=float, help='Time limit for model solution')
    parser_stress.add_argument('--tl', type=float, help='Time limit for user solution')
    parser_stress.add_argument('--ml', type=int, help='Memory limit for solutions')
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

    # (import) import new problem from polygon archive
    parser_import = subparsers.add_parser('import', help='import problem from polygon archive')
    parser_import.add_argument('path', help='archive or folder path')
    parser_import.add_argument('name', nargs='?', help='problem name')
    parser_import.set_defaults(func=import_polygon_problem)

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
