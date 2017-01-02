
from nick import Nick
import gtk
import gobject
import pango
import time

class IRCTab(gtk.VBox):
    '''
        The IRCTab class represents a tab that contains
        textural data. This can either be a private chat
        with a person, or a channel. Other than keeping track
        of the data within the tab, it also keeps track of the name
        of the tab and the mode (if the tab is a channel).
    '''
    def __init__(self, ui, ident, treeview=False):
        gtk.VBox.__init__(self)
        self.ui = ui
        self.ident = ident

        hpaned = gtk.HPaned()
        self.init_textview(hpaned)
        if treeview:
            self.init_treeview(hpaned)
        self.pack_start(hpaned)
        self.init_entry()
        self.show_all()

    def init_textview(self, hpaned):
        self.view = gtk.TextView(gtk.TextBuffer(self.ui.get_tag_table()))
        self.view.set_editable(False)
        self.view.set_cursor_visible(False)
        self.view.set_wrap_mode(gtk.WRAP_WORD | gtk.WRAP_CHAR)
        self.view.modify_font(pango.FontDescription("Monospace bold 11"))
        '''
            Pack it into a scrolled window.
        '''
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER,
                          gtk.POLICY_ALWAYS)
        scroll.set_size_request(200, 200)
        scroll.add(self.view)
        hpaned.pack1(scroll, True, False)
        self.view.connect("size-allocate", self.ui.scroll_textview,
                          scroll)

    def init_treeview(self, hpaned):
        self.tree = gtk.TreeView()
        image_column = gtk.TreeViewColumn(None, gtk.CellRendererPixbuf(),
                                          pixbuf=0)
        self.tree.append_column(image_column)
        text_column = gtk.TreeViewColumn(None, gtk.CellRendererText(),
                                         text=1)
        self.tree.append_column(text_column)
        self.tree.set_headers_visible(False)
        self.init_list_store()
        self.tree.connect("row-activated", self.ui.row_activated,
                          self.list_store)
        self.tree.connect("button-press-event", self.ui.menu_nicknames,
                          self)

        '''
            Pack it into a scrolled window.
        '''
        scroll = gtk.ScrolledWindow()
        scroll.set_policy(gtk.POLICY_NEVER,
                          gtk.POLICY_AUTOMATIC)
        scroll.set_size_request(100, 200)
        scroll.add(self.tree)
        hpaned.pack2(scroll, True, False)

    def init_entry(self):
        self.entry = gtk.Entry()
        self.entry.set_can_focus(True)
        self.entry.connect("activate", self.ui.handle_input,
                           self)
        self.pack_start(self.entry, False)

    def init_list_store(self):
        self.list_store = gtk.ListStore(gtk.gdk.Pixbuf,
                                        gobject.TYPE_STRING)
        self.tree.set_model(self.list_store)
        self.nicks = []

    def nick_add(self, nick):
        self.nicks.append(Nick(nick))
        self.nicks.sort(key=self.nick_sort)
        self.nick_add_row(self.nick_index(nick))

    def nick_add_list(self, nicks):
        for i in nicks:
            if i[0] == "@":
                self.nicks.append(Nick(i[1:], True))
            elif i[0] == "+":
                self.nicks.append(Nick(i[1:], voice=True))
            else:
                self.nicks.append(Nick(i))

    def nick_del(self, nick):
        index = self.nick_index(nick)
        self.nicks.pop(index)
        self.list_store.remove(self.nick_get_iter(index))

    def nick_update_nick(self, old_nick, new_nick):
        index = self.nick_index(old_nick)
        self.list_store.remove(self.nick_get_iter(index))
        self.nicks[index].set_nick(new_nick)
        self.nicks.sort(key=self.nick_sort)
        self.nick_add_row(self.nick_index(new_nick))

    def nick_set_mode(self, nick, mode):
        idx = self.nick_index(nick)
        obj = self.nicks[idx]
        if mode == "+o":
            if obj.get_op():
                return
            obj.set_op(True)
        elif mode == "-o":
            if not obj.get_op():
                return
            obj.set_op(False)
        elif mode == "+v":
            if obj.get_voice():
                return
            obj.set_voice(True)
        elif mode == "-v":
            if not obj.get_voice():
                return
            obj.set_voice(False)
        self.list_store.remove(self.nick_get_iter(idx))
        self.nicks.sort(key=self.nick_sort)
        self.nick_add_row(self.nick_index(nick))

    def nick_index(self, nick):
        for i in range(len(self.nicks)):
            if self.nicks[i].get_nick() == nick:
                return i
        return None

    def nick_get_iter(self, index):
        return self.list_store.get_iter_from_string(
            "%d" % index)

    def nick_add_row(self, index):
        nick = self.nicks[index]
        img_op, img_voice = self.ui.get_images()
        if nick.get_op():
            self.list_store.insert(index, [img_op, nick.get_nick()])
        elif nick.get_voice():
            self.list_store.insert(index, [img_voice, nick.get_nick()])
        else:
            self.list_store.insert(index, [None, nick.get_nick()])

    def nick_add_rows(self):
        self.nicks.sort(key=self.nick_sort)
        for i in range(len(self.nicks)):
            self.nick_add_row(i)

    def nick_get_obj(self, nick):
        return self.nicks[self.nick_index(nick)]

    def nick_sort(self, nick):
        if nick.get_op():
            return "0" + nick.get_nick()
        elif nick.get_voice():
            return "1" + nick.get_nick()
        else:
            return "2" + nick.get_nick()

    def get_topic(self, topic):
        return self.topic

    def set_topic(self, topic):
        self.topic = topic

    def set_topic_creator(self, creator):
        self.topic_creator = creator

    def set_topic_ts(self, ts):
        self.topic_ts = time.ctime(int(ts))

    def gen_topic_string(self):
        return "Topic for %s: %s\nTopic set by %s at %s" % \
                (self.ident, self.topic, self.topic_creator,
                 self.topic_ts)

    def set_mode(self, mode):
        self.mode = mode

    def get_mode(self, mode):
        return self.mode

    def get_ident(self):
        return self.ident

    def get_entry(self):
        return self.entry

    def is_channel(self):
        return True if hasattr(self, "tree") else False

    def append_data(self, data, tag="generic"):
        string = "%s %s\n" % (time.strftime("%H:%M"), data)
        buf = self.view.get_buffer()
        buf.insert_with_tags_by_name(buf.get_end_iter(), string,
                                     tag)
        self.ui.colorize_irctab_label(self)