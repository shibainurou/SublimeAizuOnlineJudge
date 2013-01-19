#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.dom.minidom
import urllib
import os
import sys
import re
import textwrap

import time
import datetime
from datetime import datetime as dt

import sublime
import sublime_plugin


def syntax_name(view):
    syntax = os.path.basename(view.settings().get('syntax'))
    syntax = os.path.splitext(syntax)[0]
    return syntax


class JudgeRequest():
    """docstring for ResultData"""
    data = ""
    user_id = ""
    run_id = ""
    user_id = ""
    problem_id = ""
    submission_date = ""
    submission_date_str = ""
    status = ""
    language = ""
    cputime = ""
    memory = ""
    code_size = ""

    time_limit = ''
    memory_limit = ''

    uri = ''
    path_submit = ''
    path_result = ''
    path_problem = ''

    # Error check OK
    # comlipe error, wrong anser, accepted
    status_msg = {
    'CompileError': u'提出されたプログラムのコンパイルに失敗しました。',
    'WrongAnswer': u'不正解です。\n提出されたプログラムは審判データと異なる出力データを生成しました。',
    'TimeLimitExceeded': u'制限時間を超えました。不正解です。\n問題に指定された制限時間内にプログラムが終了しませんでした。',
    'MemoryLimitExceeded': u'制限メモリ使用量を超えました。不正解です。\n提出されたプログラムは、問題に指定された以上のメモリを使用しました。',
    'Accepted': u'正解です。',
    'OutputLimitExceeded': u'提出されたプログラムは、制限を越えたサイズの出力を行いました。',
    'RuntimeError': u'提出されたプログラムの実行中にエラーが発生しました。\n不正なメモリアクセス、スタックオーバーフロー、ゼロによる割り算など多くの原因が考えられます。また、main 関数は必ず 0 を返すようにして下さい。',
    'WA:PresentationError': u'出力の形式が誤っています。\n提出されたプログラムは、正しい計算結果を出力していますが、余計な空白や改行を行っていたり、あるいは必要な空白や改行を出力していません。'
    }

    def __init__(self, view):
        self.uri = view.settings.get('uri')
        self.path_submit = view.settings.get('path_submit')
        self.path_result = view.settings.get('path_result')
        self.path_problem = view.settings.get('path_problem')

    def submit(self, data):
        res = self.post(self.path_submit, data)
        return res

    def submit_result(self, query):
        res = self.get(self.path_result, query)
        self.data = res.read()
        data = self.data
        data = re.sub('\s', '', data)
        self.run_id = re.compile(self.extract('run_id')).search(data).group(1)
        self.user_id = re.compile(self.extract('user_id')).search(data).group(1)
        self.problem_id = re.compile(self.extract('problem_id')).search(data).group(1)
        self.submission_date = re.compile(self.extract('submission_date')).search(data).group(1)
        self.submission_date = dt.fromtimestamp(int(self.submission_date) / 1000)
        self.submission_date_str = re.compile(self.extract('submission_date_str')).search(data).group(1)
        self.status = re.compile(self.extract('status')).search(data).group(1)
        self.language = re.compile(self.extract('language')).search(data).group(1)
        self.cputime = re.compile(self.extract('cputime')).search(data).group(1)
        self.memory = re.compile(self.extract('memory')).search(data).group(1)
        self.code_size = re.compile(self.extract('code_size')).search(data).group(1)

    def create_problem_info(self, view, problem_no):
        volume = ''
        if len(problem_no) == 5:
            volume = '100'
        else:
            volume = problem_no[0:2]

        post_map ={
        'volume': volume
        }

        problem_list_xml = self.get(self.path_problem, urllib.urlencode(post_map)).read()      
        dom = xml.dom.minidom.parseString(problem_list_xml)

        for problem in dom.getElementsByTagName('problem'):
            id = problem.getElementsByTagName('id').item(0).childNodes[0].data.strip()
            if id == problem_no:
                self.time_limit = problem.getElementsByTagName('problemtimelimit').item(0).childNodes[0].data.strip()
                self.memory_limit = problem.getElementsByTagName('problemmemorylimit').item(0).childNodes[0].data.strip()
                break

    def post(self, send_path, data):
        res = urllib.urlopen(self.uri + send_path, data)
        return res

    def get(self, send_path, query):
        res = urllib.urlopen(self.uri + send_path + '?' + query)
        return res

    def extract(self, target):
        return '<' + target + '>' + '([^<]+)' + '<\/' + target + '>'


class PromptSubmitCommand(sublime_plugin.WindowCommand):
    def run(self):
        v = sublime.active_window().active_view()
        v.settings = sublime.load_settings('AizuOnlineJudge.sublime-settings')
        last_problem_no = v.settings.get('last_exec_problem_no')
        sublime.active_window().show_input_panel('Program Id:', last_problem_no, self.on_done, None, None)
        pass

    def on_done(self, text):
        try:
            problem_no = text
            if self.window.active_view():
                self.window.active_view().run_command('submit', {'problem_no': problem_no})
        except ValueError:
            pass


class SubmitCommand(sublime_plugin.TextCommand):
    RETRY_COUNT = 5
    problem_no = None

    def run(self, edit, problem_no):
        # file名から取る場合はself.problem_no = None
        self.problem_no = problem_no

        view = sublime.active_window().active_view()
        view.settings = sublime.load_settings('AizuOnlineJudge.sublime-settings')

        aoj_request = JudgeRequest(view)

        # submit
        res = aoj_request.submit(self.create_submit_query(view))
        res_body = res.read().replace('\n', '')
        res_body = re.sub(re.compile('<[^>]+>'), '', res_body)
        res_body = res_body.strip()

        if res_body:
            sublime.error_message(res_body)
            return

        # wait result of server
        aoj_request.create_problem_info(view, self.get_problem_no())

        sleep_time = 0.5
        sleep_total_time = 0
        for x in xrange(self.RETRY_COUNT):
            time.sleep(sleep_time)

            aoj_request.submit_result(self.get_status_query(view))
            # 最大で+10秒まで実行される
            exec_time = datetime.timedelta(seconds=10)

            # 今回submitしたものが取得できているかチェック
            if (not (aoj_request.language == self.get_language(view) and
                 dt.now() < aoj_request.submission_date + exec_time)):

                if int(aoj_request.time_limit) + 1 < sleep_total_time:
                    break
                
                sleep_time += 1
                sleep_total_time += sleep_time
                if sleep_total_time > 10:
                    sleep_time = sleep_total_time - 10
                continue

            # submitしたものが取れた
            break

        if int(aoj_request.time_limit) + 1 < sleep_total_time:
            sublime.message_dialog('TimeLimitExceeded' + '\n' +
                                   aoj_request.status_msg['TimeLimitExceeded'] + '\n' + 
                                   u'limit time : ' + aoj_request.time_limit + u' sec')

        else:
            cpu_sec = int(aoj_request.cputime) / 100
            sublime.message_dialog((aoj_request.status + '\n' + 
                                   aoj_request.status_msg[aoj_request.status] + '\n' +
                                   u'cputime : ' + unicode(cpu_sec).encode('utf-8') + u' sec\n' +
                                   u'memory : ' + aoj_request.memory + u' Kbytes' + '\n'
                                   u'code size :' + aoj_request.code_size + u' bytes'))

        # save last problem no
        view.settings.set('last_exec_problem_no', aoj_request.problem_id)
        view.settings.set('last_exec_language', aoj_request.language)
        sublime.save_settings('AizuOnlineJudge.sublime-settings')

    def get_status_query(self, view):
        status_user_data_map = {
          'user_id':    self.get_userId(view),
          'problem_id': self.get_problem_no(),
          'limit':      '1'
        }
        return urllib.urlencode(status_user_data_map)

    def create_submit_query(self, view):
        post_map = {
          'userID':     self.get_userId(view),
          'password':   self.get_password(view),
          'problemNO':  self.get_problem_no(),
          'language':   self.get_language(view),
          'sourceCode': self.get_source_code()
        }
        return urllib.urlencode(post_map)

    def get_problem_no(self):
        if self.problem_no == 'None':

            problem_no = os.path.basename(self.view.file_name())
            problem_no = re.compile('[0-9]{4,}').search(problem_no).group(0)

            if problem_no.isdigit() == False:
                sublime.error_message(u"Program No が不正です")

        else:
            problem_no = self.problem_no

        return problem_no

    def get_language(self, view):
        isFind = False
        for available_syntax in view.settings.get('available_syntax'):
            if syntax_name(self.view).upper() == available_syntax.upper():
                isFind = True
                break

        if isFind == False:
            sublime.error_message(u'この言語は使用できません。')
            sys.exit()

        return available_syntax

    def get_userId(self, view):
        return view.settings.get('user_name')

    def get_password(self, view):
        return view.settings.get('password')

    def get_source_code(self):
        sourceCode = self.view.substr(sublime.Region(0, self.view.size()))
        return sourceCode.encode('shift-jis')


class CreateFileCommand(sublime_plugin.WindowCommand):

    def run(self):
        # v = sublime.active_window().active_view()
        s = sublime.load_settings('AizuOnlineJudge.sublime-settings')
        language = s.get('last_exec_language')
        sublime.active_window().show_input_panel('language:', language, self.on_done, None, None)

    def on_done(self, text):
        try:
            new_file_view = sublime.Window.new_file(sublime.active_window())
            new_file_view.run_command('create_file_core', {'language': text})
        except ValueError:
            pass


class CreateFileCoreCommand(sublime_plugin.TextCommand):
    EXTNAME_LANGUAGES_MAP = {
      'C': '.c',
      'C++': '.cpp',
      'JAVA': '.java',
      'C#': '.cs',
      'D': '.d',
      'RUBY': '.rb',
      'PYTHON': '.py',
      'PHP': '.php',
      'JAVASCRIPT': '.js'
    }
    LANGUAGES_MAP = {
      'C': 'C',
      'C++': 'C++',
      'JAVA': 'Java',
      'C#': 'C#',
      'D': 'D',
      'RUBY': 'Ruby',
      'PYTHON': 'Python',
      'PHP': 'PHP',
      'JAVASCRIPT': 'JavaScript',
    }

    def run(self, edit, language):
        language = self.LANGUAGES_MAP[language.upper()]
        extname = self.EXTNAME_LANGUAGES_MAP[language.upper()]
        template_file_name = 'template' + extname
        template_path = sublime.packages_path() + '\\SublimeAizuOnlineJudge\\template'

        new_file_view = sublime.active_window().active_view()
        new_file_view.set_syntax_file('Packages/' + language + '/' + language + '.tmLanguage')

        if not os.path.exists(template_path +  '\\' + template_file_name):
            return

        f = open(template_path + '\\' + template_file_name)
        template = f.read()
        f.close()

        new_file_view.insert(edit, 0, template)
        

