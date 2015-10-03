#!/usr/bin/python3
import os
import csv

__author__ = 'ksg'


class User:
    def __init__(self):
        self.data = {}
        self.results = {}  # prob -> score, attempts

    def add_data(self, new_data):
        try:
            self.data['login'] = new_data[1]
            self.data['Email'] = new_data[3]
            self.data['Имя'] = new_data[11]
            self.data['Отчество'] = new_data[12]
            self.data['Фамилия'] = new_data[13]
            self.data['класс'] = new_data[14]
            self.data['Email2'] = new_data[15]
            self.data['телефон'] = new_data[16]
            self.data['Школа'] = new_data[17]
            self.data['как узнал'] = new_data[18]
        except IndexError:
            pass

    def add_submit(self, prob, score):
        cur_score, cur_attempts = self.results.get(prob, (0, 0))

        if score - cur_attempts > cur_score:
            cur_score = score - cur_attempts

        self.results[prob] = cur_score, cur_attempts + 1

    def get_row(self, data_header, problems):
        data = [self.data.get(x, '') for x in data_header]

        s = 0
        for x in problems:
            data += self.results.get(x, (0, 0))
            s += self.results.get(x, (0, 0))[0]

        data.append(s)

        return data


runs_files = input('runs.csv files: ').split()
users_files = input('users.csv files ').split()

users = {}  # uid -> users data
header = ''
for users_file in users_files:
    print(os.path.expandvars(users_file))
    with open(os.path.normpath(os.path.expandvars(users_file)), newline='') as users_f:
        users_reader = csv.reader(users_f, delimiter=';')
        header = users_reader.__next__()

        uid_ind = header.index('Id')

        for user in users_reader:
            if user:
                users.setdefault(user[uid_ind], User()).add_data(user)

problems = set()

for i, runs_file in enumerate(runs_files, start=1):
    with open(os.path.normpath(os.path.expandvars(runs_file)), newline='') as runs_f:
        runs_reader = csv.reader(runs_f, delimiter=';', quotechar='"')
        r_header = runs_reader.__next__()

        uid_ind = r_header.index('User_Id')
        prob_ind = r_header.index('Prob')
        score_ind = r_header.index('Score')
        status_ind = r_header.index('Stat_Short')

        for run in runs_reader:
            uid = run[uid_ind]
            prob = 'c{}_{}'.format(i, run[prob_ind])
            prob_att = prob + '_attempts'
            score = int(run[score_ind])
            status = run[status_ind]

            problems.add(prob)

            if status == 'OK':
                score = 100

            if status != 'CE':
                users[uid].add_submit(prob, score)

header = ['login', 'Email', 'Email2', 'Имя', 'Отчество', 'Фамилия', 'класс', 'телефон', 'Школа', 'как узнал']
with open('out.csv', 'w', newline='') as f:
    writer = csv.writer(f, delimiter=';', quotechar='"')

    csv_header = header[:]
    for i in sorted(problems):
        csv_header += [i, i + '_attempts']
    csv_header += ('sum', )
    writer.writerow(csv_header)

    for user in sorted(users):
        writer.writerow(users[user].get_row(header, sorted(problems)))
