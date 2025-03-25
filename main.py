# https://kivy.org/doc/stable/guide/packaging-windows.html
# https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#embedding-yt-dlp

# TODO: setup dependabot to auto-update and auto-release when a new version of yt_dlp comes out
# TODO: auto-upload .exe release

import os
from kivy.app import App

from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.textinput import TextInput

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout

from plyer import filechooser

from yt_dlp import YoutubeDL


class App(App):

    def __init__(self):
        super(App, self).__init__()
        self.location = self.get_download_path()

    def get_download_path(self):
        if os.name == "nt":
            import winreg

            sub_key = (
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                location = winreg.QueryValueEx(key, downloads_guid)[0]
            return location
        else:
            return os.path.join(os.path.expanduser("~"), "Downloads")

    def pick_download_folder(self, _btn):
        path = filechooser.choose_dir()
        self.location = path

    def build(self):
        root_layout = BoxLayout(orientation="vertical", spacing=50, padding=30)

        # setup url/download sublayout
        url_download_layout = BoxLayout(
            orientation="horizontal", spacing=20, size_hint_y=0.2
        )
        url_input = TextInput(size_hint_x=0.8)
        download_button = Button(size_hint_x=0.2)

        # setup location/options sublayout
        location_options_layout = BoxLayout(
            orientation="horizontal", spacing=20, size_hint_y=0.2
        )

        ### setup location button
        location_button = Button(size_hint_x=0.5, text=self.location)
        location_button.bind(on_release=lambda btn: self.pick_download_folder(btn))
        ### setup dropdown
        options_dropdown = DropDown()
        for format in [".mp3", ".webm", ".mp4", ".mkv"]:
            btn = Button(text=format, size_hint_y=None, height=24)
            btn.bind(on_release=lambda btn: options_dropdown.select(btn.text))
            options_dropdown.add_widget(btn)
        options_dropdown.bind(
            on_select=lambda instance, x: setattr(options_button, "text", x)
        )
        options_button = Button(text="Select format...", size_hint_x=0.5)
        options_button.bind(on_release=options_dropdown.open)

        # add widgets to layouts
        url_download_layout.add_widget(url_input)
        url_download_layout.add_widget(download_button)
        location_options_layout.add_widget(location_button)
        location_options_layout.add_widget(options_button)

        root_layout.add_widget(url_download_layout)
        root_layout.add_widget(location_options_layout)

        return root_layout


if __name__ == "__main__":
    App().run()
