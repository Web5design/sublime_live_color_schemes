
import re
import json
import os.path

import sublime
import sublime_plugin

from .sublime_live import UpdateLiveViewCommand, LiveEventListener
from .sublime_live import LiveView, LiveRegion
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
        super().__init__(name='Live Color Scheme')

        color_schemes = []

        self.run_command('update_live_view', {'data': '%s\n' % (' ' * 85), 'start': self.size()})
        self.add_regions('horizontal_rule', [sublime.Region(self.size() - 86, self.size() - 1)],
                                            scope='horizontal_rule', flags=sublime.DRAW_NO_OUTLINE)

        user_prefs_path = os.path.join(
                                sublime.packages_path(), 'User', 'Preferences.sublime-settings')
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
                    text = '   %s%s\n' % (text, ' ' * (82 - len(text)))
                    self.run_command('update_live_view', {'data': text, 'start': self.size()})
                    live_region = LiveRegion(
                                    self.size() + 2 - len(text), self.size() - 3, process=process)
                    regions = self.get_regions('horizontal_rule')
                    regions.extend(
                        [
                            sublime.Region(self.size() - 86, self.size() - 84),
                            sublime.Region(self.size() - 3, self.size() - 1)
                        ]
                    )
                    self.add_regions('horizontal_rule', regions, scope='horizontal_rule',
                                                                    flags=sublime.DRAW_NO_OUTLINE)
                    self.add_regions(text.strip(), [live_region], scope=scope, flags=flags)
                self.run_command('update_live_view',
                                            {'data': '%s\n' % (' ' * 85), 'start': self.size()})
                regions = self.get_regions('horizontal_rule')
                regions.append(sublime.Region(self.size() - 86, self.size() - 1))
                self.add_regions('horizontal_rule', regions, scope='horizontal_rule',
                                                                    flags=sublime.DRAW_NO_OUTLINE)

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
            read_only=True
        )


class LiveColorSchemesCommand(sublime_plugin.WindowCommand):
    """
    window.run_command('live_color_schemes')
    """
    def run(self):
        LiveColorSchemes()
