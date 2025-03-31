# https://kivy.org/doc/stable/guide/packaging-windows.html
# https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#embedding-yt-dlp

# TODO: setup dependabot to auto-update and auto-release when a new version of yt_dlp comes out
# TODO: auto-upload .exe release
# TODO: download new version when opening app

import os
from shutil import which
from threading import Thread
import sys
import validators

import eel

from plyer import filechooser
from yt_dlp import YoutubeDL


video_label = ""
video_format = "mp3"
url = ""
dialog_closed = False

formats = {
    "mp3": {
        "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}],
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


def resource_path(relative_path):
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


@eel.expose
def get_default_download_path():
    if os.name == "nt":
        import winreg

        sub_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
        downloads_guid = "{374DE290-123F-4565-9164-39C4925E467B}"
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return os.path.join(os.path.expanduser("~"), "Downloads")


@eel.expose
def pick_download_folder():

    def inner():
        global location
        global dialog_closed
        path = filechooser.choose_dir(multiple=False)
        if path:
            location = path
            eel.update_download_path(path[0])()
        eel.set_controls_enabled(True)
        dialog_closed = True

    eel.set_controls_enabled(False)
    eel.spawn(inner)


@eel.expose
def download_video(url, format, location):
    if validators.url(url):
        eel.set_url_input_error(False)
        eel.set_controls_enabled(False)
        eel.spawn(download_video_thread, url=url, format=format, location=location)
    else:
        eel.set_url_input_error(True)


def download_video_thread(url, format, location):
    global video_label

    try:
        ytdl_opts = formats[format]
        ytdl_opts["paths"] = {"home": location}
        ytdl_opts["progress_hooks"] = [progress_hook]
        if not which("ffmpeg") and os.name == "nt":
            ytdl_opts["ffmpeg_location"] = resource_path(
                os.path.join(".", "ffmpeg", "ffmpeg.exe")
            )
        with YoutubeDL(ytdl_opts) as ytdl:
            video_label = "Fetching..."
            eel.update_video_label("Fetching...")
            ytdl.download([url])
    except Exception as e:
        print(e)
        video_label = "Error :("
        eel.update_video_label("Error :(")
    eel.set_controls_enabled(True)


def progress_hook(d):
    global video_label

    video_label = d["info_dict"]["title"]
    eel.update_video_label(d["info_dict"]["title"])
    eel.update_status(d["status"], d["speed"], d["_percent"])


@eel.expose
def get_state():
    state = {
        "url": url,
        "video_label": video_label,
        "location": location,
        "format": video_format,
    }
    return state


@eel.expose
def update_url(new_url):
    global url
    if new_url:
        url = new_url


@eel.expose
def update_format(new_format):
    global video_format
    if new_format:
        video_format = new_format


def close(page, sockets_still_open):
    global dialog_closed

    # only exit if main window was closed, not file picker
    if dialog_closed:
        dialog_closed = False
    else:
        os._exit(0)


if __name__ == "__main__":
    global location
    location = get_default_download_path()
    eel.init("web")
    try:
        eel.start(
            "main.html", port=0, size=(540, 360), block=False, close_callback=close
        )
        while True:
            eel.sleep(1.0)
    except OSError as e:
        if os.name == "nt":
            eel.start(
                "main.html",
                port=0,
                size=(540, 360),
                block=False,
                close_callback=close,
                mode="edge",
            )
            while True:
                eel.sleep(1.0)
        else:
            raise e
