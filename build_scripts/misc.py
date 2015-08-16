# !/usr/bin/python3
import configparser
import json

import jsoncomment
import os

__author__ = 'ksg'

pjoin = os.path.join


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def write_log(s: str, end='\n', file='', out=None, write_to_stdout=True, write_to_file=True, color=None):
    if write_to_stdout:
        if color:
            print(color + s + bcolors.ENDC, end=end)
        else:
            print(s, end=end)

    if write_to_file and (out or not file == ''):
        if not out:
            out = open(file, 'a')
        print(s, end=end, file=out)
        out.close()


class Config:
    def __init__(self):
        self.problem_cfg_is_json = None
        self.contest_cfg_is_json = None

        jsoncomment.package.comments.COMMENT_PREFIX = ('#', ';', '//')  # Dirty hack!!

        if get_problem_root():
            if os.path.exists(os.path.join(get_problem_root(), 'problem.json')):
                with open(os.path.join(get_problem_root(), 'problem.json')) as fp:
                    # self.problem_cfg = json.loads(jsmin(fp.read(), quote_chars="'\"`"))
                    self.problem_cfg = jsoncomment.JsonComment(json).load(fp)
                self.problem_cfg_is_json = True
            else:
                self.problem_cfg = configparser.ConfigParser(allow_no_value=True)
                self.problem_cfg.read(os.path.join(get_problem_root(), 'problem.conf'))
                self.problem_cfg_is_json = False

        if get_contest_root():
            if os.path.exists(os.path.join(get_contest_root(), 'contest.json')):
                with open(os.path.join(get_contest_root(), 'contest.json')) as fp:
                    self.contest_cfg = jsoncomment.JsonComment(json).load(fp)
                self.contest_cfg_is_json = True
            else:
                self.contest_cfg = configparser.ConfigParser()
                self.contest_cfg.read(os.path.join(get_contest_root(), 'contest.conf'))
                self.contest_cfg_is_json = False

    def get_main_solution(self):
        if self.problem_cfg_is_json:
            for solution in self.problem_cfg['solutions']:
                if solution.get('is_main', False):
                    return solution['path']
        else:
            return self.problem_cfg[self.problem_cfg['general']['main solution']]['path']

    def get_solutions(self):
        if self.problem_cfg_is_json:
            return [(x.get('name', os.path.basename(x['path'])), x['path']) for x in self.problem_cfg['solutions']]
        else:
            lst = self.problem_cfg.sections()[:]
            lst.remove('general')
            return [(x, self.problem_cfg[x]['path']) for x in lst]

    def get_problem_param(self, param, use_default=True):
        if use_default:
            if self.problem_cfg_is_json:
                return self.problem_cfg.get(param, None)
            else:
                return self.problem_cfg['general'].get(param, None)
        else:  # can raise KeyError
            if self.problem_cfg_is_json:
                return self.problem_cfg[param]
            else:
                return self.problem_cfg['general'][param]

    def has_problem_param(self, param):
        if self.problem_cfg_is_json:
            return param in self.problem_cfg
        else:
            return param in self.problem_cfg['general']

    def get_contest_host(self):
        if self.contest_cfg_is_json:
            return self.contest_cfg['server']
        else:
            return self.contest_cfg['default']['contest_host']

    def get_server_contest_path(self):
        if self.contest_cfg_is_json:
            return self.contest_cfg['server_path']
        else:
            return self.contest_cfg['default']['contest_path']


def get_contest_root():
    if os.path.exists('lib') and os.path.exists('problems') and \
            (os.path.exists('contest.conf') or os.path.exists('contest.json')):
        root = os.curdir
    elif os.path.exists('../lib') and os.path.exists('../problems') and \
            (os.path.exists('../contest.conf') or os.path.exists('../contest.json')):
        root = os.path.normpath(os.path.join('../', os.curdir))
    elif os.path.exists('../../lib') and os.path.exists('../../problems') and \
            (os.path.exists('../../contest.conf') or os.path.exists('../../contest.json')):
        root = os.path.normpath(os.path.join('../../', os.curdir))
    else:
        root = None
    return root


def get_problem_root():
    if os.path.exists('problem.conf') or os.path.exists('problem.json'):
        root = os.curdir
    elif os.path.exists('../problem.conf') or os.path.exists('../problem.json'):
        root = os.path.normpath(os.path.join('../', os.curdir))
    elif os.path.exists('../../problem.conf') or os.path.exists('../../problem.json'):
        root = os.path.normpath(os.path.join('../../', os.curdir))
    else:
        root = None
    return root
