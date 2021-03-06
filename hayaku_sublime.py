# -*- coding: utf-8 -*-
import os
import functools
import re

import sublime
import sublime_plugin

def import_dir(name, fromlist=()):
    PACKAGE_EXT = '.sublime-package'
    dirname = os.path.basename(os.path.dirname(os.path.realpath(__file__)))
    if dirname.endswith(PACKAGE_EXT):
        dirname = dirname[:-len(PACKAGE_EXT)]
    return __import__('{0}.{1}'.format(dirname, name), fromlist=fromlist)


try:
    make_template = import_dir('hayaku_templates', ('make_template',)).make_template
except ImportError:
    from hayaku_templates import make_template

try:
    get_hayaku_options = import_dir('hayaku_sublime_get_options', ('hayaku_sublime_get_options',)).get_hayaku_options
except ImportError:
    from hayaku_sublime_get_options import get_hayaku_options

try:
    get_merged_dict = import_dir('hayaku_sublime_get_merged_dict', ('hayaku_sublime_get_merged_dict',)).get_merged_dict
except ImportError:
    from hayaku_sublime_get_merged_dict import get_merged_dict

# The maximum size of a single propery to limit the lookbehind
MAX_SIZE_CSS = len('-webkit-transition-timing-function')

ABBR_REGEX = re.compile(r'[\s|;|{]([\.:%#a-z-,\d\$\@\+]+!?)$', re.IGNORECASE)

class HayakuCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        self.edit = edit
        self.hayaku = {}

        self.retrieve_abbr()
        if self.hayaku.get('abbr') is None:
            return

        self.expand_abbr_to_snippet()
        if self.snippet is None:
            return

        self.insert_snippet()

    def expand_abbr_to_snippet(self):
        self.get_options()
        self.get_clipboard()
        self.get_merged_dict()
        self.snippet = make_template(self.hayaku)

    def get_options(self):
        self.hayaku['options'] = get_hayaku_options(self)

    def get_clipboard(self):
        self.hayaku['clipboard'] = sublime.get_clipboard()

    def get_merged_dict(self):
        self.hayaku['dict'], self.hayaku['aliases'] = get_merged_dict(self.view.settings(), self.hayaku['options'].get('CSS_preprocessor', None))

    def retrieve_abbr(self):
        cur_pos = self.view.sel()[0].begin()
        start_pos = cur_pos - MAX_SIZE_CSS
        if start_pos < 0:
            start_pos = 0
        # TODO: Move this to the contexts, it's not needed here
        probably_abbr = self.view.substr(sublime.Region(start_pos, cur_pos))
        match = ABBR_REGEX.search(probably_abbr)
        if match is None:
            self.view.insert(self.edit, cur_pos, '\t')
            return

        self.hayaku['abbr'] = match.group(1)

    def insert_snippet(self):
        cur_pos = self.view.sel()[0].begin()
        new_cur_pos = cur_pos - len(self.hayaku.get('abbr'))
        assert cur_pos - len(self.hayaku.get('abbr')) >= 0
        self.view.erase(self.edit, sublime.Region(new_cur_pos, cur_pos))
        self.view.run_command("insert_snippet", {"contents": self.snippet})
