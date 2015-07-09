# !/usr/bin/python3.3
import configparser

import os


__author__ = 'ksg'

pjoin = os.path.join


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
