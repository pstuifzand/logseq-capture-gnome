import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk, Gio
import requests
import os
import datetime
import json

class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        with open(os.path.expanduser("~/.config/logseq-capture/config.json")) as f:
            try:
                config = json.load(f)
                self.token = config['LOGSEQ_TOKEN']
            except FileNotFoundError:
                print("Please create ~/.config/logseq-capture/config.json")
                sys.exit(1)
            except KeyError:
                print("Please set LOGSEQ_TOKEN")
                sys.exit(1)

        self.box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_child(self.box1)

        self.textarea = Gtk.TextView()
        self.textarea.set_editable(True)
        self.textarea.set_cursor_visible(True)
        self.textarea.set_wrap_mode(Gtk.WrapMode.WORD)
        # Set font size with css provider
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data("""
        textview {
            font-size: 20px;
        }
        """, -1)
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.box1.set_margin_top(10)
        self.box1.set_margin_bottom(10)
        self.box1.set_margin_start(10)
        self.box1.set_margin_end(10)

        scrolledwindow = Gtk.ScrolledWindow()
        scrolledwindow.set_hexpand(True)
        scrolledwindow.set_vexpand(True)
        scrolledwindow.set_child(self.textarea)
        self.box1.append(scrolledwindow)
        button = Gtk.Button(label="Capture")
        button.set_action_name("win.capture")
        self.box1.append(button)

        action = Gio.SimpleAction.new("capture")
        action.connect("activate", self.on_button_clicked)
        self.add_action(action)

        action = Gio.SimpleAction.new("close")
        action.connect("activate", self.on_escape_pressed_event)
        self.add_action(action)

    def on_escape_pressed_event(self, action, parameter):
        self.close()

    def on_button_clicked(self, event, parameter):
        buffer = self.textarea.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)

        # Find block on current journal page
        parent = "#Log"
        logseqBlock = logseqFindBlock(self.token, parent)
        if not logseqBlock:
            page = logseqJournal(self.token)
            result = logseqCommand(self.token, "logseq.Editor.appendBlockInPage", [page, parent])
            print(result)
            logseqBlock = result['uuid']
            
        now = datetime.datetime.now()
        text = f"**{now.strftime('%H:%M')}** #inbox {text}"
        logseqCommand(self.token, "logseq.Editor.insertBlock", [logseqBlock, text])

        self.textarea.get_buffer().set_text("")
        self.close()


def logseqJournal(token):
    # Find current journal page
    query = """
     [:find (pull ?p [*])
     :in $ ?start
     :where
     [?b :block/page ?p]
     [?p :block/journal? true]
     [?p :block/journal-day ?d]
     [(= ?d ?start)]]
    """
    page = logseqCommand(token, "logseq.DB.datascriptQuery", [query, ":today"])
    uuid = page[0][0]['uuid']
    return uuid


def logseqFindBlock(token, block):
    query = """
     [:find (pull ?b [*])
     :in $ ?start ?parentBlock
     :where
     [?b :block/page ?p]
     [?b :block/content ?parentBlock]
     [?p :block/journal? true]
     [?p :block/journal-day ?d]
     [(= ?d ?start)]]
     """
    page = logseqCommand(token, "logseq.DB.datascriptQuery", [query, ":today", '"' + block + '"'])
    try:
        uuid = page[0][0]['uuid']
        return uuid
    except IndexError:
        return False


def logseqCommand(token, method, args):
    url = "http://127.0.0.1:12315/api"
    data = {"method": method, "args": args}
    res = requests.post(url, json=data, headers={'Content-Type': 'application/json', 'Authorization': 'Bearer '+token})
    return res.json()


class MyApp(Adw.Application):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        app.set_accels_for_action("win.capture", ["<Control>Return"])
        app.set_accels_for_action("win.close", ["Escape"])

        self.win = MainWindow(application=app)
        self.win.set_title("Logseq Capture")
        self.win.set_default_size(800, 300)
        self.win.set_resizable(True)
        self.win.present()

app = MyApp(application_id="nl.peterstuifzand.logseq.capture")
app.run(sys.argv)
