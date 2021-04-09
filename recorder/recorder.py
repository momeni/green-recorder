# -*- coding: utf-8 -*-

# FOSS Project <https://foss-project.com>, 2017, 2018.
# Green Recorder is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Green Recorder is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Green Recorder.  If not, see <http://www.gnu.org/licenses/>.

import os
import time
from .prefix import prefix
from .__about__ import __version__, __copyright__

# Force GDK backend to be X11 because Wayland applications are not allowed to
# know their window positions, which we need for selecting an area to record!
os.environ['GDK_BACKEND'] = 'x11'

import gi

gi.require_version('AppIndicator3', '0.1')
gi.require_version('Gtk', '3.0')

from gi.repository import Gtk, Gdk, GLib, AppIndicator3 as appindicator
from pydbus import SessionBus
import subprocess
import signal
import threading
import datetime
import gettext
import locale
import sys

# long story short, "configparser" Python 2 backport RPM package is no good because it strips init py
try:
    # Python 3
    from configparser import ConfigParser
except ImportError:
    # Python 2
    from ConfigParser import SafeConfigParser as ConfigParser

try:
    # Python 3
    from urllib.parse import unquote
except ImportError:
    # Python 2
    from urllib import unquote

# Configuration
confDir = os.path.join(GLib.get_user_config_dir(), 'green-recorder/')
confFile = os.path.join(confDir + "config.ini")
config = ConfigParser()

from timeit import default_timer as timer

recording_time_start = None

if not os.path.exists(confDir):
    os.makedirs(confDir)

VideosFolder = GLib.get_user_special_dir(GLib.USER_DIRECTORY_VIDEOS)
if VideosFolder is None:
    VideosFolder = os.environ['HOME']

if os.path.isfile(confFile):
    config.read(confFile)
if not config.has_section('Options'):
    config.add_section('Options')

# Localization.
locale.setlocale(locale.LC_ALL, '')
extra_locale_dirs = [
    os.path.join(os.getcwd(), "locale"),
]

# this binds system translation
gettext.bindtextdomain('green-recorder')
gettext.textdomain('green-recorder')
gettext.install("green-recorder")

# if there is a translation in the current directory, use it
for locale_dir in extra_locale_dirs:
    if os.path.exists:
        locale.bindtextdomain('green-recorder', locale_dir)
        gettext.bindtextdomain('green-recorder', locale_dir)
        gettext.install("green-recorder", locale_dir)

# Define a loop and connect to the session bus. This is for Wayland recording under GNOME Shell.
loop = GLib.MainLoop()
bus = SessionBus()

# Get the current name of the Videos folder
RecorderDisplay = subprocess.check_output("xdpyinfo | grep 'dimensions:'|awk '{print $2}'",
                                          shell=True)[:-1]
DISPLAY = os.environ["DISPLAY"]

DisplayServer = os.getenv('XDG_SESSION_TYPE', 'xorg')

print("You are recording on: " + str(DisplayServer))

if "wayland" in DisplayServer:
    DisplayServer = "gnomewayland"
    global GNOMEScreencast
    GNOMEScreencast = bus.get('org.gnome.Shell.Screencast', '/org/gnome/Shell/Screencast')
else:
    DisplayServer = "xorg"

# Import the glade file and its widgets.
builder = Gtk.Builder()  # type: Gtk.Builder
install_prefix = prefix()
possible_ui_file_locations = []
app_indicator_icon = ''
if os.getenv('VIRTUAL_ENV'):
    possible_ui_file_locations.append(
        os.path.join(os.path.dirname(os.getenv('VIRTUAL_ENV')), "ui", "ui.glade"))
    app_indicator_icon = os.path.join(os.path.dirname(os.getenv('VIRTUAL_ENV')), "data", "green-recorder.png")
elif install_prefix:
    possible_ui_file_locations.append(install_prefix + "/share/green-recorder/ui.glade")
    app_indicator_icon = install_prefix + "/share/green-recorder/green-recorder.png"

for filename in possible_ui_file_locations:
    if os.path.exists(filename):
        builder.add_from_file(filename)
        break
else:
    sys.exit("Did not find ui.glade.  Tried\n  %s"
             % "\n  ".join(possible_ui_file_locations))

def send_notification(text, time):
    notifications = bus.get('.Notifications')
    notifications.Notify('GreenRecorder', 0, 'green-recorder', "Green Recorder", text, [], {},
                         time * 1000)


def check_status():
    os.system("sleep 3")
    if not os.path.isfile(RecorderAbsPathName):
        window.present()
        send_notification(_(
            "There seems to be a problem in recording. Try running 'green-recorder' from the "
            "command line to see the issue."),
            4)


def recorder_indicator():
    # Create the app indicator widget.
    global indicator
    try:
        s = subprocess.check_output("ps -cat|grep mate-panel", shell=True)
    except:
        indicator = appindicator.Indicator.new(
            "Green Recorder",
            app_indicator_icon,
            appindicator.IndicatorCategory.APPLICATION_STATUS)
        pass
    else:
        indicator = appindicator.Indicator.new("Green Recorder", 'green-recorder',
                                               appindicator.IndicatorCategory.APPLICATION_STATUS)
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)

    menu = Gtk.Menu()
    stoprecordingbutton = Gtk.MenuItem(label=_('Stop Recording'))
    stoprecordingbutton.connect('activate', stop_recording)
    menu.append(stoprecordingbutton)
    menu.show_all()

    indicator.set_menu(menu)
    indicator.set_secondary_activate_target(stoprecordingbutton)


def record_xorg():
    global DISPLAY, RecorderDisplay
    try:
        areaaxis
    except:
        pass  # Ok, cause it means user didn't select an area.
    else:
        RecorderDisplay = str(WindowWidth) + "x" + str(WindowHeight)
        DISPLAY = DISPLAY + "+" + str(WindowXAxis) + "," + str(WindowYAxis)

    RecorderCommand = ["ffmpeg"]

    if videoswitch.get_active():
        RecorderCommand.append("-video_size")
        RecorderCommand.append(RecorderDisplay)

        if mouseswitch.get_active():
            RecorderCommand.append("-draw_mouse")
            RecorderCommand.append("1")

        if followmouseswitch.get_active():
            RecorderCommand.append("-follow_mouse")
            RecorderCommand.append("centered")

        RecorderCommand.append("-framerate")
        RecorderCommand.append(RecorderFrames)
        RecorderCommand.append("-f")
        RecorderCommand.append("x11grab")
        RecorderCommand.append("-i")
        RecorderCommand.append(DISPLAY)

    if audioswitch.get_active():
        RecorderCommand.append("-f")
        RecorderCommand.append("pulse")
        RecorderCommand.append("-i")
        RecorderCommand.append(audiosource.get_active_id())
        RecorderCommand.append("-strict")
        RecorderCommand.append("-2")

    # Pre format auditing.
    if formatchooser.get_active_id() == "gif":
        RecorderCommand.append("-codec:v")
        RecorderCommand.append("pam")
        RecorderCommand.append("-f")
        RecorderCommand.append("rawvideo")

    RecorderCommand.append("-q")
    RecorderCommand.append("1")
    RecorderCommand.append(RecorderFullPathName)
    RecorderCommand.append("-y")

    global RecorderProcess
    RecorderProcess = subprocess.Popen(RecorderCommand)

    window.iconify()
    Gdk.flush()
    recorder_indicator()

    t = threading.Thread(target=check_status)
    t.daemon = True
    t.start()


def record_gnome():
    AudioRecording = []

    global RecorderPipeline

    if formatchooser.get_active_id() == "webm":
        RecorderPipeline = "vp8enc min_quantizer=10 max_quantizer=50 cq_level=13 cpu-used=5 " \
                           "deadline=1000000 threads=%T ! queue ! webmmux"
    elif formatchooser.get_active_id() == "mp4":
        RecorderPipeline = "x264enc pass=qual quantizer=0 speed-preset=ultrafast ! queue ! mp4mux"
    global AudioProcess
    if audioswitch.get_active():
        AudioRecording.append("ffmpeg")
        AudioRecording.append("-f")
        AudioRecording.append("pulse")
        AudioRecording.append("-i")
        AudioRecording.append(audiosource.get_active_id())
        AudioRecording.append("/tmp/Green-recorder-tmp.mkv")
        AudioRecording.append("-y")

        AudioProcess = subprocess.Popen(AudioRecording)
    else:
        AudioProcess = None

    if videoswitch.get_active():
        try:
            areaaxis

        except NameError:
            GNOMEScreencast.Screencast(RecorderAbsPathName,
                                       {'framerate': GLib.Variant('i', int(RecorderFrames)),
                                        'draw-cursor': GLib.Variant('b', mouseswitch.get_active()),
                                        'pipeline': GLib.Variant('s', RecorderPipeline)})

        else:
            GNOMEScreencast.ScreencastArea(WindowXAxis, WindowYAxis, WindowWidth, WindowHeight,
                                           RecorderAbsPathName,
                                           {'framerate': GLib.Variant('i', int(RecorderFrames)),
                                            'draw-cursor': GLib.Variant('b',
                                                                        mouseswitch.get_active()),
                                            'pipeline': GLib.Variant('s', RecorderPipeline)})

    window.iconify()
    Gdk.flush()
    traythread = threading.RLock()
    with traythread:
        recorder_indicator()

    t = threading.Thread(target=check_status)
    t.daemon = True
    t.start()


def stop_recording(_):
    # nothing to play and nothing to stop
    stopbutton.set_sensitive(False)
    time.sleep(1)  # Wait ffmpeg.
    recordbutton.set_sensitive(True)
    window.present()

    discard = False
    global recording_time_start, discard_adjustment

    if not recording_time_start:
        print('We were not recording...')

    recording_time = timer() - recording_time_start

    if recording_time < discard_adjustment.get_value():
        print('Shorter than ' + str(discard_adjustment.get_value()) + ' secs, discarding')
        discard = True
    else:
        print('Recording time ' + str(recording_time) + ' secs. Not too short, saved')
        # TODO save indicator and make sensitive on save only
        playbutton.set_sensitive(True)
        delete_button.set_sensitive(True)
    recording_time_start = None

    try:
        global areaaxis, WindowXAxis, WindowYAxis, WindowWidth, WindowHeight
        del areaaxis, WindowXAxis, WindowYAxis, WindowWidth, WindowHeight
    except NameError:
        pass  # Ok, cause it means user didn't select a window/area.

    if "xorg" in DisplayServer:
        time.sleep(1)
        RecorderProcess.terminate()
        indicator.set_status(appindicator.IndicatorStatus.PASSIVE)
    elif "gnomewayland" in DisplayServer:
        time.sleep(1)
        indicator.set_status(appindicator.IndicatorStatus.PASSIVE)

        try:
            GNOMEScreencast.StopScreencast()
            if AudioProcess:
                AudioProcess.terminate()
        except Exception as e:
            print(e)

        if discard:
            if videoswitch.get_active():
                os.remove(RecorderAbsPathName)
            if audioswitch.get_active():
                os.remove("/tmp/Green-recorder-tmp.mkv")
            return window.present()

        if videoswitch.get_active() and audioswitch.get_active():
            m = subprocess.call(
                ["ffmpeg", "-i", RecorderFullPathName, "-i", "/tmp/Green-recorder-tmp.mkv", "-c",
                 "copy", "/tmp/Green-Recorder-Final." + formatchooser.get_active_id(), "-y"])
            k = subprocess.Popen(
                ["mv", "/tmp/Green-Recorder-Final." + formatchooser.get_active_id(),
                 RecorderAbsPathName])
        elif not videoswitch.get_active() and audioswitch.get_active():
            k = subprocess.Popen(["mv", "/tmp/Green-recorder-tmp.mkv", RecorderAbsPathName])

    if formatchooser.get_active_id() == "gif":
        send_notification(_(
            "Your GIF image is currently being processed, this may take a while according to your"
            " PC's resources."),
            5)

        subprocess.call(["mv", RecorderAbsPathName, RecorderAbsPathName + ".tmp"])
        subprocess.call(
            ["convert", "-layers", "Optimize", RecorderAbsPathName + ".tmp", RecorderAbsPathName])
        os.remove(RecorderAbsPathName + ".tmp")

    window.present()

    CommandToRun = command.get_text().replace('$1', RecorderAbsPathName)
    subprocess.Popen([CommandToRun], shell=True)


def record():
    global RecorderFullPathName  # grab the path
    global recording_time_start
    recording_time_start = timer()
    RecorderFullPathName = unquote(
        folderchooser.get_uri() + '/' + filename.get_text() + '.' + formatchooser.get_active_id())

    abs_path = RecorderFullPathName.replace("file://", '')
    if os.path.exists(abs_path) and filename.get_text() is not "":
        dialog = Gtk.Dialog(
            _("File already exists!"),
            None,
            Gtk.DialogFlags.MODAL,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
             Gtk.STOCK_OK, Gtk.ResponseType.OK,)
        )
        dialog.set_transient_for(window)
        dialog.set_default_size(150, 100)
        label = Gtk.Label(_("Would you like to overwrite this file?"))
        box = dialog.get_content_area()
        box.add(label)
        dialog.show_all()
        response = dialog.run()
        dialog.destroy()
        if response == Gtk.ResponseType.OK:
            dialog.destroy()
        elif response == Gtk.ResponseType.CANCEL:
            return

    # Get the given values from the input fields.
    # global RecorderFullPathName
    global RecorderAbsPathName
    global RecorderDelay
    global RecorderFrames

    RecorderDelay = str(delay.get_value_as_int())
    RecorderFrames = str(frames.get_value_as_int())

    if len(filename.get_text()) < 1:
        RecorderFullPathName = unquote(folderchooser.get_uri() + '/' + str(
            datetime.datetime.now()) + '.' + formatchooser.get_active_id())
    else:
        RecorderFullPathName = unquote(
            folderchooser.get_uri() + '/' + filename.get_text() + '.' +
            formatchooser.get_active_id())

    RecorderAbsPathName = RecorderFullPathName.replace("file://", "")

    subprocess.call(["sleep", RecorderDelay])
    stopbutton.set_sensitive(True)
    recordbutton.set_sensitive(False)

    if "xorg" in DisplayServer:
        record_xorg()

    # This is for GNOME compositor with Wayland.
    elif "gnomewayland" in DisplayServer:
        record_gnome()

    else:
        send_notification(_("Sorry Jim, looks like you are using something we don't support"), 3)
        window.present()


def hide_on_delete(widget, event):
    widget.hide()
    return True


# Create pointers.
window = builder.get_object("main_window")
areachooser = builder.get_object("window2")
aboutdialog = builder.get_object("aboutdialog")
folderchooser = builder.get_object("filechooser")
filename = builder.get_object("filename")
command = builder.get_object("command")
formatchooser = builder.get_object("comboboxtext1")  # type: object
audiosource = builder.get_object("audiosource")
recordbutton = builder.get_object("recordbutton")
stopbutton = builder.get_object("stopbutton")
windowgrabbutton = builder.get_object("button4")
areagrabbutton = builder.get_object("button5")
frames = builder.get_object("frames")
delay = builder.get_object("delay")
delay_adjustment = builder.get_object("delay_adjustment")
framesadjustment = builder.get_object("adjustment2")
delayprefadjustment = builder.get_object("adjustment3")
discard_adjustment = builder.get_object("discard_adjustment")
playbutton = builder.get_object("playbutton")
delete_button = builder.get_object("delete_button")
videoswitch = builder.get_object("videoswitch")
audioswitch = builder.get_object("audioswitch")
mouseswitch = builder.get_object("mouseswitch")
followmouseswitch = builder.get_object("followmouseswitch")

# Assign the texts to the interface
window.set_title(_("Green Recorder"))
areachooser.set_name("AreaChooser")

window.connect("delete-event", Gtk.main_quit)
formatchooser.set_active(0)
aboutdialog.set_version(__version__)
aboutdialog.set_copyright(__copyright__)
aboutdialog.set_authors(
    ['M.Hanny Sabbagh <mhsabbagh@outlook.com>', 'Alessandro Toia <gort818@gmail.com>',
     'Patreon Supporters: Ahmad Gharib, Medium,\nWilliam Grunow, Alex Benishek.'])
aboutdialog.set_artists(['Mustapha Assabar'])
areachooser.connect("delete-event", hide_on_delete)
frames.set_value(config.getint('Options', 'frames', fallback=30))
delay.set_value(config.getint('Options', 'delay', fallback=0))
discard_adjustment.set_value(config.getint('Options', 'discard', fallback=10))
filename.set_text(config.get('Options', 'filename', fallback=''))
folderchooser.set_uri(config.get('Options', 'folder', fallback="file://" + VideosFolder))
videoswitch.set_active(config.getboolean('Options', 'videocheck', fallback=True))
audioswitch.set_active(config.getboolean('Options', 'audiocheck', fallback=True))
mouseswitch.set_active(config.getboolean('Options', 'mousecheck', fallback=False))
followmouseswitch.set_active(config.getboolean('Options', 'followmousecheck', fallback=False))
command.set_text(config.get('Options', 'command', fallback=''))

# Audio input sources
audiosource.append("default", _("Default PulseAudio Input Source"))
try:
    audiosourcesnames = subprocess.check_output("pacmd list-sources | grep -e device.description",
                                                shell=True)
    audiosourcesids = subprocess.check_output("pacmd list-sources | grep -e device.string",
                                              shell=True)
except Exception as e:
    print(e)
audiosourcesnames = audiosourcesnames.split(b"\n")[:-1]

for i in range(len(audiosourcesnames)):
    audiosourcesnames[i] = audiosourcesnames[i].replace(b"\t\tdevice.description = ", b"")
    audiosourcesnames[i] = audiosourcesnames[i].replace(b'"', b"")

    audiosource.append(str(i), audiosourcesnames[i].decode('UTF-8', 'replace'))

audiosource.set_active(0)

# Disable unavailable functions under Wayland.
if "wayland" in DisplayServer:
    windowgrabbutton.set_sensitive(False)
    followmouseswitch.set_sensitive(False)
    formatchooser.remove_all()

    formatchooser.append("webm", "WebM (The Open WebM Format)")
    formatchooser.append("mp4", "MP4 (MPEG-4 Part 14)")
    formatchooser.set_active(0)


class Handler:

    def __init__(self):
        pass


    def show_about(self, GtkButton):
        aboutdialog.run()
        aboutdialog.hide()


    def recordclicked(self, GtkButton):
        record()


    def selectwindow(self, GtkButton):
        output = subprocess.check_output(["xwininfo | grep -e Width -e Height -e Absolute"],
                                         shell=True)[:-1]

        global areaaxis
        areaaxis = [int(l.split(':')[1]) for l in output.decode('UTF-8', 'ignore').split('\n')]

        global WindowXAxis, WindowYAxis, WindowWidth, WindowHeight
        WindowXAxis = areaaxis[0]
        WindowYAxis = areaaxis[1]
        WindowWidth = areaaxis[2]
        WindowHeight = areaaxis[3]

        send_notification(_("Your window position has been saved!"), 3)


    def selectarea(self, GtkButton):
        areachooser.show()


    def stoprecordingclicked(self, GtkButton):
        stop_recording(_)


    def playbuttonclicked(self, GtkButton):
        subprocess.call(["xdg-open", unquote(RecorderAbsPathName)])


    def delete_button_clicked_cb(self, GtkButton):
        os.remove(RecorderAbsPathName)
        playbutton.set_sensitive(False)
        delete_button.set_sensitive(False)


    def areasettings(self, GtkButton):
        output = subprocess.check_output(
            ["xwininfo -name \"Area Chooser\" | grep -e Width -e Height -e Absolute"], shell=True)[
                 :-1]

        global areaaxis
        areaaxis = [int(l.split(':')[1]) for l in output.decode('UTF-8', 'ignore').split('\n')]

        global WindowXAxis, WindowYAxis, WindowWidth, WindowHeight
        WindowXAxis = areaaxis[0] + 12
        WindowYAxis = areaaxis[1] + 48
        WindowWidth = areaaxis[2] - 24
        WindowHeight = areaaxis[3] - 80

        areachooser.hide()
        send_notification(_("Your area position has been saved!"), 3)


    def frameschanged(self, GtkSpinButton):
        config.set('Options', 'frames', str(int(float(frames.get_value()))))
        global confFile
        with open(confFile, 'w+') as newconfFile:
            config.write(newconfFile)


    def delaychanged(self, GtkSpinButton):
        config.set('Options', 'delay', str(int(float(delay.get_value()))))
        global confFile
        with open(confFile, 'w+') as newconfFile:
            config.write(newconfFile)


    def discard_changed(self, GtkSpinButton):
        config.set('Options', 'discard', str(int(float(discard_adjustment.get_value()))))
        global confFile
        with open(confFile, 'w+') as newconfFile:
            config.write(newconfFile)


    def filenamechanged(self, GtkEntry):
        config.set('Options', 'filename', unquote(filename.get_text()))
        global confFile
        with open(confFile, 'w+') as newconfFile:
            config.write(newconfFile)


    def folderchosen(self, GtkFileChooserButton):
        config.set('Options', 'folder', unquote(folderchooser.get_uri()))
        global confFile
        with open(confFile, 'w+') as newconfFile:
            config.write(newconfFile)


    def commandchanged(self, GtkEntry):
        config.set('Options', 'command', command.get_text())
        global confFile
        with open(confFile, 'w+') as newconfFile:
            config.write(newconfFile)


    def videoswitchchanged(self, GtkSwitch):
        config.set('Options', 'videocheck', str(videoswitch.get_active()))
        global confFile
        with open(confFile, 'w+') as newconfFile:
            config.write(newconfFile)


    def audioswitchchanged(self, GtkSwitch):
        config.set('Options', 'audiocheck', str(audioswitch.get_active()))
        global confFile
        with open(confFile, 'w+') as newconfFile:
            config.write(newconfFile)


    def mouseswitchchanged(self, GtkSwitch):
        config.set('Options', 'mousecheck', str(mouseswitch.get_active()))
        global confFile
        with open(confFile, 'w+') as newconfFile:
            config.write(newconfFile)


    def followmouseswitchchanged(self, GtkSwitch):
        config.set('Options', 'followmousecheck', str(followmouseswitch.get_active()))
        global confFile
        with open(confFile, 'w+') as newconfFile:
            config.write(newconfFile)


# Connect the handler to the glade file's objects.
builder.connect_signals(Handler())

# Load CSS for Area Chooser.
style_provider = Gtk.CssProvider()
css = b"""
#AreaChooser {
    background-color: rgba(255, 255, 255, 0);
    border: 1px solid red;
}
"""
style_provider.load_from_data(css)
Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), style_provider,
                                         Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)


def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    window.show_all()
    Gtk.main()


# The End of all things.
if __name__ == "__main__":
    main()
