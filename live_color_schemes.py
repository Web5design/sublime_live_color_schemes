
import re
import json
import os.path

import sublime
import sublime_plugin

from .sublime_live import UpdateLiveViewCommand, LiveEventListener
from .sublime_live import LiveView, LiveRegion, del_live_view, LIVE_VIEWS
from .sublime_utils import find_all_packages


base_tmTheme = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN"
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict><key>name</key><string>Color Schemes Theme</string>
<key>settings</key><array><dict><key>settings</key><dict><key>background</key>
<string>#ffffff</string><key>caret</key><string>#ffffff</string><key>foreground</key>
<string>#000000</string></dict></dict><dict><key>name</key><string>button</string>
<key>scope</key><string>button</string><key>settings</key><dict><key>background</key>
<string>#bbbbbb</string><key>foreground</key><string>#000000</string><key>caret</key>
<string>#bbbbbb</string></dict></dict>
<dict><key>name</key><string>horizontal_rule</string>
<key>scope</key><string>horizontal_rule</string><key>settings</key><dict><key>background</key>
<string>#cccccc</string><key>foreground</key><string>#cccccd</string><key>caret</key>
<string>#cccccc</string></dict></dict>%s</array><key>uuid</key>
<string>905FEC5A-2E43-934F-EC9C-A3982DFDED3F</string></dict></plist>"""

base_color = """<dict><key>name</key><string>%s</string><key>scope</key>
<string>%s</string><key>settings</key><dict><key>background</key>
<string>%s</string><key>foreground</key><string>%s</string>
<key>caret</key><string>%s</string></dict></dict>"""


class LiveColorSchemes(LiveView):
    def __init__(self):
        window = sublime.active_window()
        self.active_view = window.active_view()
        self.orig_layout = window.get_layout()
        self.active_views = []
        self.views_in_groups = []
        for group in range(window.num_groups()):
            self.views_in_groups.append(window.views_in_group(group))
            self.active_views.append(window.active_view_in_group(group))

        super().__init__(name='Live Color Scheme', window=window)

        window = self.window()

        user_prefs_path = os.path.join(
                                sublime.packages_path(), 'User', 'Preferences.sublime-settings')

        # Get original scheme
        orig_color_scheme = self.settings().get('color_scheme', None)

        window.set_layout({
            "cols": [0.0, 1.0],
            "rows": [0.0, 1.0],
            "cells": [[0, 0, 1, 1]]
            })

        window.set_layout({
            "cols": [0.0, 0.8, 1.0],
            "rows": [0.0, 1.0],
            "cells": [[0, 0, 1, 1], [1, 0, 2, 1]]
            })

        window.run_command('move_to_group', args={'group': 1})

        color_schemes = []

        self.run_command('update_live_view', {'data': '\n Close and Restore Layout \n Restore Color Scheme \n\n'})
        def process(live_region):
            live_region.live_view.window().run_command('live_color_schemes_close')
        live_region = LiveRegion(1, 27, process=process)
        self.add_regions('restore_layout', [live_region], scope='button', flags=sublime.DRAW_OUTLINED)

        def process(live_region):
            if orig_color_scheme:
                with open(user_prefs_path, 'r') as user_prefs_file:
                    user_prefs = json.load(user_prefs_file)
                user_prefs['color_scheme'] = orig_color_scheme
                with open(user_prefs_path, 'w') as user_prefs_file:
                    json.dump(user_prefs, user_prefs_file, indent='\t')

        live_region = LiveRegion(28, 50, process=process)
        self.add_regions('restore_color_scheme', [live_region], scope='button', flags=sublime.DRAW_OUTLINED)

        packages = find_all_packages(contents=True, extensions='.tmTheme')
        for package_name, package in packages.items():
            for file_name in package['files']:
                if not file_name.endswith('.tmTheme') or file_name == 'live_color_schemes.tmTheme':
                    continue

                content = package['contents'][file_name]
                start = re.search('<dict>\s*<key>settings</key>', content)
                scope = 'button'
                flags = sublime.DRAW_NO_OUTLINE
                if start:
                    start = start.start()
                    background_color = '#bbbbbb'
                    background = re.search(
                        '<key>background</key>\s*<string>([^<]+)</string>', content[start:])
                    if background:
                        background_color = background.group(1)
                        if background_color.lower() == '#ffffff':
                            background_color = '#fffffe'
                    foreground_color = '#000000'
                    foreground = re.search(
                        '<key>foreground</key>\s*<string>([^<]+)</string>', content[start:])
                    if foreground:
                        foreground_color = foreground.group(1)
                    caret_color = '#bbbbbb'
                    caret = re.search(
                        '<key>caret</key>\s*<string>([^<]+)</string>', content[start:])
                    if caret:
                        caret_color = caret.group(1)
                    scope = file_name[:-8]
                    color_schemes.append(base_color % (
                        file_name[:-8], scope, background_color, foreground_color, caret_color))

                def process(package_name, color_scheme_name):
                    def process(live_region):
                        if not os.path.exists(user_prefs_path):
                            user_prefs = {}
                        else:
                            with open(user_prefs_path, 'r') as user_prefs_file:
                                user_prefs = json.load(user_prefs_file)
                        user_prefs['color_scheme'] = 'Packages/%s/%s' % (
                                                                package_name, color_scheme_name)
                        with open(user_prefs_path, 'w') as user_prefs_file:
                            json.dump(user_prefs, user_prefs_file, indent='\t')
                    return process
                process = process(package_name, file_name)

                for text in ['Package : ' + package_name, 'Scheme  : ' + file_name[:-8]]:
                    text = ' %s \n' % (text)
                    self.run_command('update_live_view', {'data': text, 'start': self.size()})
                    live_region = LiveRegion(
                                    self.size() - len(text), self.size() - 1, process=process)
                    self.add_regions(text.strip(), [live_region], scope=scope, flags=flags)
                    if text.startswith(' Scheme'):
                        self.run_command('update_live_view',
                                            {'data': '%s\n' % ('-' * (len(text) - 1)), 'start': self.size()})

        color_scheme = base_tmTheme % ''.join(color_schemes)
        color_scheme_path = os.path.join(sublime.packages_path(), 'User',
                                                                    'live_color_schemes.tmTheme')
        with open(color_scheme_path, 'w') as color_scheme_file:
            color_scheme_file.write(color_scheme)

        self.apply_settings(
            {
                "color_scheme": 'Packages/User/live_color_schemes.tmTheme',
                "draw_centered": True,
                "line_padding_top": 5,
                "line_padding_bottom": 5
            },
            read_only=True,
            scratch=True
        )


class LiveColorSchemesCloseCommand(sublime_plugin.WindowCommand):
    """
    window.run_command('live_color_schemes_close')
    """
    def run(self):
        for view_id, live_view in LIVE_VIEWS.items():
            if isinstance(live_view, LiveColorSchemes):
                window = live_view.window()
                window.set_layout(live_view.orig_layout)
                for g, views in enumerate(live_view.views_in_groups):
                    for view in views:
                        window.focus_view(view)
                        window.run_command('move_to_group', args={'group': g})
                    window.focus_view(live_view.active_views[g])
                window.focus_view(live_view)
                window.run_command('close')
                window.focus_view(live_view.active_view)
                del_live_view(live_view)
                break


class LiveColorSchemesOpenCommand(sublime_plugin.WindowCommand):
    """
    window.run_command('live_color_schemes_open')
    """
    def run(self):
        for view_id, live_view in LIVE_VIEWS.items():
            if isinstance(live_view, LiveColorSchemes):
                self.window.focus_view(live_view)
                break
        else:
            LiveColorSchemes()


class LiveColorSchemesToggleCommand(sublime_plugin.WindowCommand):
    """
    window.run_command('live_color_schemes_toggle')
    """
    def run(self):
        for view_id, live_view in LIVE_VIEWS.items():
            if isinstance(live_view, LiveColorSchemes):
                self.window.focus_view(live_view)
                self.window.run_command('live_color_schemes_close')
                break
        else:
            LiveColorSchemes()
