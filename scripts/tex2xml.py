#!/usr/bin/python3.3

import re

import sys


__author__ = 'ksg'


def convert(fin=sys.stdin, fout=sys.stdout, pack='', src='', pdf_link=''):
    line = fin.readline()
    while not line.startswith(r'\begin{problem}'):
        line = fin.readline()

    title = line[16: line.find('}', 15)]

    parts = {
        r'\None': 'description',
        r'\InputFile': 'input_format',
        r'\OutputFile': 'output_format',
        r'\Examples': 'examples',
        r'\Explanations': 'explanations',
        r'\Note': 'note',
    }

    cur_part = 'description'

    content = dict([(x, []) for x in parts.values()])

    line = fin.readline()
    while not line.startswith(r'\end{problem}'):
        if line.strip() in parts.keys():
            cur_part = parts[line.strip()]
        else:
            content[cur_part].append(line.strip())
        line = fin.readline()

    data = {
        'title': title,
        'pack': pack,
        'src': src,
        'pdf_link': pdf_link,
        'description': process_part(content['description']),
        'input_format': process_part(content['input_format']),
        'output_format': process_part(content['output_format']),
        'examples': process_examples(content['examples']),
        'explanations': process_part(content['explanations']),
        'note': process_part(content['note']),
    }

    if data['explanations'] and data['note']:
        data['explanations'] += '\n<br /><br />\n'
    data['note'] = data['explanations'] + data['note']

    build_xml(data, fout)


def build_xml(data, fout):
    fout.write('''\
<?xml version="1.0" encoding="utf-8" ?>
<problem
package="{pack}"
id="{title}"
type="standard">
<statement language="ru_RU">
<title>{title}</title>

<description>
<p style="font-size:12px">
{description}
</p>
</description>

<input_format>
<p style="font-size:12px">
{input_format}
</p>
</input_format>

<output_format>
<p style="font-size:12px">
{output_format}
</p>
</output_format>
'''.format_map(data))

    fout.write('''\
<notes>
<p style="font-size:12px">
{note}
'''.format_map(data))

    if data['src']:
        fout.write('''<br />Источник: <i>{}</i><br />\n'''.format(data['src']))
    if data['pdf_link']:
        fout.write('''<br />Условие в pdf можно взять <a href="{}">здесь</a>\n'''.format(data['pdf_link']))

    fout.write('''\
</p>
</notes>
</statement>
''')

    fout.write('''  <examples>\n''')
    for inf, ouf in data['examples']:
        fout.write('''\
<example>
<input>
{}
</input>
<output>
{}
</output>
</example>
'''.format(inf, ouf))
    fout.write('''</examples>\n''')
    fout.write('''</problem>\n''')


def process_part(text):
    out = []

    while not len(text) == 0 and text[0] == '':
        text.pop(0)
    while not len(text) == 0 and text[-1] == '':
        text.pop(-1)

    cur_stat = 'normal'

    for line in text:
        if line == '':
            out.append(r'<br />')

        elif line == r'\begin{itemize}':
            cur_stat = 'itemize'
            out.append(r'<ul>')
        elif line[:5] == r'\item':
            if cur_stat == 'itemize':
                out.append(r'<li style="font-size:12px;">')
                out.append(process_line(line[5:].strip()))
                out.append(r'</li>')
            else:
                raise Exception('Unexpected token \\item. Current status is "{}",'
                                ' but should be "itemize"'.format(cur_stat))
        elif line == r'\end{itemize}':
            cur_stat = 'normal'
            out.append(r'</ul>')

        elif line[0] == '%':
            continue

        else:  # Normal line
            out.append(process_line(line))

    return '\n'.join(out)


def process_examples(text):
    examples = []

    part = '\n'.join(text)

    cur_pos = 0
    while not part.find(r'\exmp', cur_pos) == -1:
        cur_pos = part.find(r'\exmp', cur_pos) + len(r'\exmp')
        inf_start = part.find('{', cur_pos) + 1  # example shouldn't contain braces
        inf_end = part.find('}', inf_start)
        ouf_start = part.find('{', inf_end) + 1
        ouf_end = part.find('}', ouf_start)
        examples.append([
            part[inf_start:inf_end].strip(),
            part[ouf_start:ouf_end].strip()
        ])
        cur_pos = ouf_end

    return examples


def process_line(line):
    tex_token_specs = [
        ('MATH', r'\$([^$]+)\$', 1),  # math formula
        ('NBSP', r'~', 0),
        ('NDASH', r'--(?!-)', 0),
        ('MDASH', r'---', 0),
        ('MONOSP', r'\\t{([^}]*)}', 1),
        ('MONOSP_Q', r'\\w{([^}]*)}', 1),
        ('LT', r'<(?!<)', 1),
        ('GT', r'>(?!>)', 1),
        ('LAQUO', '<<'),
        ('RAQUO', '>>'),
        ('TEXT', r'[^<>\\$~\-\w]+'),
        ('WSP', r'\w+'),
        ('MINUS', r'-(?!-)'),
    ]

    html_token_specs = {
        'MATH': ('<i>', '</i>'),
        'NBSP': '&nbsp;',
        'MDASH': '&mdash;',
        'MONOSP': ('<tt style="font-size:12px">', '</tt>'),
        'MONOSP_Q': ('<tt style="font-size:12px">&ldquo;', '&rdquo;</tt>'),
        'LT': '&lt;',
        'GT': '&gt;',
        'LAQUO': '&laquo;',
        'RAQUO': '&raquo;',
    }

    tok_regex = '|'.join('(?P<%s>%s)' % (pair[0], pair[1]) for pair in tex_token_specs)
    get_token = re.compile(tok_regex).match

    res = ''

    pos = 0
    mo = get_token(line)
    while mo is not None:
        typ = mo.lastgroup
        if typ == 'MATH':
            rpos = pos + 1
            while not line[rpos] == '$':
                rpos += 1
            res += html_token_specs[typ][0] + process_math_formula(line[pos + 1:rpos]) + html_token_specs[typ][1]
            pos = rpos + 1

        elif typ == 'MONOSP' or typ == 'MONOSP_Q':
            rpos = pos + 2  # TODO recognize inner braces
            while not line[rpos] == '}':
                rpos += 1
            res += html_token_specs[typ][0] + process_line(line[pos + 3:rpos]) + html_token_specs[typ][1]
            pos = rpos + 1

        elif typ == 'TEXT' or typ == 'WSP' or typ == 'MINUS':
            rpos = mo.end()
            res += line[pos:rpos]
            pos = rpos

        else:  # NBSP, MDASH, etc...
            res += html_token_specs[typ]
            pos = mo.end()

        mo = get_token(line, pos)
    return res


def process_math_formula(line: str):
    res = ''
    pos = 0

    token_map = {
        '^': ('<sup>', '</sup>'),
        '_': ('<sub>', '</sub>'),
        '<': '&lt;',
        '>': '&gt;',
        r'\le': '&le;',
        r'\leq': '&le;',
        r'\ge': '&ge;',
        r'\geq': '&ge;',
        r'\ldots': '&hellip;',
        r'\cdot': '&thinsp;&#8901;&thinsp;',
        '-': '&thinsp;&minus;&thinsp;',
        '+': '&thinsp;+&thinsp;',
    }

    while pos < len(line):
        if line[pos].isalnum() or line[pos].isspace():
            res += line[pos]
            pos += 1

        elif line[pos] == '^' or line[pos] == '_':
            if line[pos + 1] == '{':
                rpos = pos + 1
                cnt = 1
                while cnt is not 0:
                    rpos += 1
                    if line[rpos] == '{':
                        cnt += 1
                    elif line[rpos] == '}':
                        cnt -= 1
                cont = process_math_formula(line[pos + 2: rpos])

            else:
                cont = line[pos + 1]
                rpos = pos + 1

            res += token_map[line[pos]][0] + cont + token_map[line[pos]][1]
            pos = rpos + 1

        elif line[pos] == '\\':
            if line[pos + 1] in '{}':  # just { or } character
                res += line[pos + 1]
                pos += 2
            else:
                rpos = pos
                while rpos < len(line) and not line[rpos].isspace() and not line[rpos] in '.,;':
                    rpos += 1

                if line[pos:rpos] in [r'\cdot']:  # TODO fix spaces around operators
                    if res[-1] == ' ':
                        res = res[:-1]

                res += token_map.get(line[pos:rpos], '&' + line[pos + 1:rpos] + ';')

                if line[pos:rpos] in [r'\cdot']:  # TODO fix spaces around operators
                    if line[rpos] == ' ':
                        rpos += 1

                pos = rpos

        else:  # if line[pos] in token_map:
            rpos = pos + 1

            if line[pos] in ['-', '+']:  # TODO fix spaces around operators
                if res[-1] == ' ':
                    res = res[:-1]
                if line[rpos] == ' ':
                    rpos += 1

            res += token_map.get(line[pos], line[pos])
            pos = rpos

            #else:
            # raise Exception('Unknown token ("{}")'.format(line[pos]))

    return res