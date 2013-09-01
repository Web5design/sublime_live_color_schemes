Sublime Text 3 : Live Color Schemes
==========================

A [sublime live](https://github.com/sligodave/sublime_live) view that lists all available color schemes in your installed plugins.
Color schemes can be applied by clicking.

## Install:

You'll need Sublime Text 3

Clone this repository into your Sublime Text *Packages* directory.

	OSX:
	    ~/Library/Application Support/Sublime Text 3
	Linux:
        ~/.config/sublime-text-3/Packages
    Windows:
        %APPDATA%\Sublime Text 3\Packages

    git clone https://github.com/sligodave/sublime_live_color_schemes.git LiveColorSchemes
    cd LiveColorSchemes
    git submodule init
    git submodule update

Open Sublime Text 3

Open Sublime Text 3's Python Prompt and run the todo load command:

	CTRL + `
	Type: window.run_command('live_color_schemes')

You can of course also create a key mapping to load the live color schemes page.

## Issues / Suggestions:

Send on any suggestions or issues.

## Copyright and license
Copyright 2013 David Higgins

[MIT License](LICENSE)
