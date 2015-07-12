import json
import pkgutil
import zipfile
from xml.etree import ElementTree

import stat
import shutil
import os
import tempfile

__author__ = 'ksg'


def import_problem(src, dest):
    if not os.path.isdir(src):
        tempdir = tempfile.TemporaryDirectory()
        archive = zipfile.ZipFile(src)
        archive.extractall(tempdir.name)
        src = tempdir.name

    polygon_conf_tree = ElementTree.parse(os.path.join(src, 'problem.xml'))
    polygon_conf_root = polygon_conf_tree.getroot()

    conf = {}

    if polygon_conf_root.find('names'):
        conf['title'] = polygon_conf_root.find('names')[0].attrib['value']
    else:
        conf['title'] = ''

    conf['short_name'] = polygon_conf_root.attrib['short-name']
    conf['system_name'] = polygon_conf_root.attrib['short-name']

    import_statement(src, dest, polygon_conf_root, conf['short_name'])

    import_solutions(src, dest, polygon_conf_root, conf)

    conf['test_num_width'] = 2

    conf['samples_num'] = 0

    conf['tl'] = int(polygon_conf_root.find('judging')[0].find('time-limit').text) // 1000
    conf['ml'] = int(polygon_conf_root.find('judging')[0].find('memory-limit').text) // 2 ** 20

    import_validator(src, dest, polygon_conf_root, conf)
    import_checker(src, dest, polygon_conf_root, conf)

    conf['use_doall'] = True
    conf['doall_cmd'] = 'bash doall.sh'

    conf['use_wipe'] = True
    conf['wipe_cmd'] = 'bash wipe.sh'

    shutil.copytree(os.path.join(src, 'solutions'),
                    os.path.join(dest, 'solutions'))
    shutil.copytree(os.path.join(src, 'scripts'),
                    os.path.join(dest, 'scripts'))
    shutil.copytree(os.path.join(src, 'files'),
                    os.path.join(dest, 'files'))
    shutil.copytree(os.path.join(src, 'tests'),
                    os.path.join(dest, 'tests'))
    shutil.copy2(os.path.join(src, 'doall.sh'),
                 os.path.join(dest, 'doall.sh'))
    shutil.copy2(os.path.join(src, 'wipe.sh'),
                 os.path.join(dest, 'wipe.sh'))

    sh_files = ['doall.sh', 'wipe.sh']
    sh_files += [os.path.join('scripts', x) for x in os.listdir(os.path.join(src, 'scripts')) if x.endswith('.sh')]

    for file in sh_files:
        os.chmod(os.path.join(dest, file), os.stat(os.path.join(dest, file)).st_mode | stat.S_IXUSR)

    with open(os.path.join(dest, 'problem.json'), 'w') as fd:
        fd.write(json.dumps(conf, ensure_ascii=False, indent=4))


def import_statement(src, dest, polygon_conf_root, short_name):
    os.mkdir(os.path.join(dest, 'statements'))
    if polygon_conf_root.find('statements'):
        for statement in polygon_conf_root.find('statements'):
            if statement.attrib['language'] == 'russian' and statement.attrib['type'] == 'application/x-tex':
                shutil.copy2(os.path.join(src, statement.attrib['path']),
                             os.path.join(dest, 'statements', short_name + '.tex'))
    if not os.path.exists(os.path.join(dest, 'statements', short_name + '.tex')):
        statement = str(pkgutil.get_data('build_scripts', os.path.join('data', 'bootstrap', 'st.tex')), 'utf-8')
        with open(os.path.join(dest, 'statements', short_name + '.tex'), 'w') as f:
            f.write(statement)


def import_solutions(src, dest, polygon_conf_root, conf):
    conf['solutions'] = []
    for solution in polygon_conf_root.find('assets').find('solutions'):
        conf['solutions'].append({'path': solution.find('source').attrib['path'],
                                  'is_main': True if solution.attrib['tag'] == 'main' else False,
                                  'tag': solution.attrib['tag'],
                                  'type': solution.find('source').attrib['type']
                                  })


def import_validator(src, dest, polygon_conf_root, conf):
    if polygon_conf_root.find('assets').find('validators'):
        validator = polygon_conf_root.find('assets').find('validators')[0].find('source').attrib['path']
        shutil.copy2(os.path.join(src, validator),
                     os.path.join(dest, os.path.basename(validator)))
        conf['validator'] = os.path.basename(validator)
    else:
        statement = str(pkgutil.get_data('build_scripts', os.path.join('data', 'bootstrap', 'validator.cpp')), 'utf-8')
        with open(os.path.join(dest, 'validator.cpp'), 'w') as f:
            f.write(statement)
        conf['validator'] = os.path.basename('validator.cpp')


def import_checker(src, dest, polygon_conf_root, conf):
    if polygon_conf_root.find('assets').find('checker'):
        checker = polygon_conf_root.find('assets').find('checker').find('source').attrib['path']
        checker_ex = polygon_conf_root.find('assets').find('checker').find('binary').attrib['path']
        shutil.copy2(os.path.join(src, checker),
                     os.path.join(dest, os.path.basename(checker)))
        shutil.copy2(os.path.join(src, checker_ex),
                     os.path.join(dest, os.path.basename(checker_ex)))
        conf['checker'] = os.path.basename(checker)
    else:
        statement = str(pkgutil.get_data('build_scripts', os.path.join('data', 'bootstrap', 'checker.cpp')), 'utf-8')
        with open(os.path.join(dest, 'checker.cpp'), 'w') as f:
            f.write(statement)
        conf['checker'] = os.path.basename('checker.cpp')
