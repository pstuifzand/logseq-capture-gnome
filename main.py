import sys
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')
from gi.repository import Gtk, Adw, Gdk
import requests
import os


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.token = os.environ['LOGSEQ_TOKEN']

        self.box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.set_child(self.box1)

        self.textarea = Gtk.TextView()
        self.textarea.set_editable(True)
        self.textarea.set_cursor_visible(True)
        self.textarea.set_wrap_mode(Gtk.WrapMode.WORD)

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
        button.connect("clicked", self.on_button_clicked)
        self.box1.append(button)

    def on_button_clicked(self, event):
        buffer = self.textarea.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), True)

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
        page = logseqCommand(self.token, "logseq.DB.datascriptQuery", [query, ":today"])
        uuid = page[0][0]['uuid']
        logseqCommand(self.token, "logseq.Editor.insertBlock", [uuid, text])

        self.textarea.get_buffer().set_text("")
        self.close()


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
        self.win = MainWindow(application=app)
        self.win.set_title("Logseq Capture")
        self.win.set_default_size(400, 400)
        self.win.set_resizable(True)
        self.win.present()

app = MyApp(application_id="nl.peterstuifzand.logseq.capture")
app.run(sys.argv)
