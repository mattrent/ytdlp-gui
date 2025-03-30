# https://kivy.org/doc/stable/guide/packaging-windows.html
# https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#embedding-yt-dlp

# TODO: setup dependabot to auto-update and auto-release when a new version of yt_dlp comes out
# TODO: auto-upload .exe release
# TODO: download new version when opening app

import os
from threading import Thread
import validators

from kivy.config import Config

Config.set("graphics", "resizable", "0")
Config.set("graphics", "height", "360")

from kivymd.app import MDApp

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown

from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.progressbar import MDProgressBar

from plyer import filechooser

from yt_dlp import YoutubeDL


class App(MDApp):

    def __init__(self):
        super(App, self).__init__()
        self.location = self.get_download_path()
        self.title = "yt-dlp GUI"
        self.formats = {
            "mp3": {
                "postprocessors": [
                    {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}
                ],
                "outtmpl": {"default": "%(title)s.%(ext)s"},
                "noprogress": True,
                "quiet": True,
            },
            "mp4": {
                "format": "mp4",
                "outtmpl": {"default": "%(title)s.%(ext)s"},
                "noprogress": True,
                "quiet": True,
            },
        }

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

    def download_video(self, url):
        if validators.url(url):
            self.url_input.error = False
            self.url_input.disabled = True
            self.download_button.disabled = True
            self.options_button.disabled = True
            self.location_button.disabled = True
            thread = Thread(target=self.download_video_thread, args=(url,))
            thread.start()
        else:
            self.url_input.error = True

    def download_video_thread(self, url):
        try:
            ytdl_opts = self.formats[self.options_button.text]
            ytdl_opts["paths"] = {"home": self.location}
            ytdl_opts["progress_hooks"] = [self.progress_hook]
            with YoutubeDL(ytdl_opts) as ytdl:
                self.video_name_label.text = "Fetching..."
                ytdl.download([url])
        except:
            self.video_name_label.text = "Error :("

        self.url_input.disabled = False
        self.download_button.disabled = False
        self.options_button.disabled = False
        self.location_button.disabled = False

    def progress_hook(self, d):
        self.video_name_label.text = d["info_dict"]["title"]
        self.status_label.text = d["status"]
        self.percentage_label.text = f'{d["_percent"]:.1f}%'
        speed = d["speed"]
        if speed:
            speed /= 1024 * 1024
        else:
            speed = 0
        self.speed_label.text = f"{speed:.1f}MiB/s"
        self.progress_bar.value = int(float(d["_percent"]))

    def build(self):
        root_layout = BoxLayout(orientation="vertical", spacing=50, padding=30)

        # setup url/download sublayout
        url_download_layout = BoxLayout(
            orientation="horizontal", spacing=20, size_hint_y=0.2
        )
        self.url_input = MDTextField(
            size_hint_x=0.9,
            hint_text="URL",
            mode="rectangle",
            multiline=False,
            helper_text="Enter a valid URL",
        )
        self.download_button = MDIconButton(size_hint_x=0.1, icon="download")

        ### setup download button and URL input
        self.download_button.bind(
            on_release=lambda _: self.download_video(self.url_input.text)
        )

        self.video_name_label = MDLabel(
            text="", size_hint_x=1, size_hint_y=0.05, halign="center"
        )

        # setup location/options sublayout
        location_options_layout = BoxLayout(
            orientation="horizontal", spacing=20, size_hint_y=0.2
        )

        ### setup location button
        self.location_button = Button(size_hint_x=0.5, text=self.location)
        self.location_button.bind(on_release=lambda btn: self.pick_download_folder(btn))
        ### setup dropdown
        self.options_dropdown = DropDown()
        for format in self.formats:
            btn = Button(text=format, size_hint_y=None, height=32, font_size=16)
            btn.bind(on_release=lambda btn: self.options_dropdown.select(btn.text))
            self.options_dropdown.add_widget(btn)
        self.options_dropdown.bind(
            on_select=lambda _, x: setattr(self.options_button, "text", x)
        )
        self.options_button = Button(text="mp3", size_hint_x=0.5)
        self.options_button.bind(on_release=self.options_dropdown.open)

        # progress labels layout
        progress_labels_layout = BoxLayout(
            orientation="horizontal", spacing=20, size_hint_y=0.2
        )

        self.status_label = MDLabel(text="", halign="center")
        self.speed_label = MDLabel(text="", halign="center")
        self.percentage_label = MDLabel(text="", halign="center")

        self.progress_bar = MDProgressBar(max=100, value=0, size_hint_y=0.4)

        # add widgets to layouts
        url_download_layout.add_widget(self.url_input)
        url_download_layout.add_widget(self.download_button)
        location_options_layout.add_widget(self.location_button)
        location_options_layout.add_widget(self.options_button)
        progress_labels_layout.add_widget(self.status_label)
        progress_labels_layout.add_widget(self.speed_label)
        progress_labels_layout.add_widget(self.percentage_label)

        root_layout.add_widget(url_download_layout)
        root_layout.add_widget(self.video_name_label)
        root_layout.add_widget(location_options_layout)
        root_layout.add_widget(progress_labels_layout)
        root_layout.add_widget(self.progress_bar)

        return root_layout


if __name__ == "__main__":
    App().run()
