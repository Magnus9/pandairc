
from pandasocket import PandaSocket
from irctab import IRCTab
import re
import gtk
import gtk.keysyms
gtk.gdk.threads_init()

'''
    The pattern that is to be compiled into a
    match object. To be changed (buggy).
'''
p = (
  "(?:/([^\s]+)"
    "("
      "(?:"
        "\s#[^\s]*"
      ")+"
    ")?"
    "("
      "(?:"
        "\s[^:\s][^\s]*"
      ")+"
    ")?"
    "(?:"
      "\s(:.*)"
    ")?"
  ")?"
)

'''
    These defines below are to be used in
    conjunction with the regular expression
    match object.
'''
COMMAND  = 0
CHANNELS = 1
PARAMS   = 2
MESSAGE  = 3

class PandaUI:
    QUIT_MESSAGE = "Panda irc"

    def __init__(self, port, nick, srv):
        self.expr = re.compile(p)
        self.sock = PandaSocket(self, port, nick, srv)
        self.init_cbs()
        self.init_gtk()

    '''
        Initialize the main gtk window and build
        the ui by delegating the task to self.init_ui.
        Lastly start the event loop.
    '''
    def init_gtk(self):
        self.window = gtk.Window()
        self.window.set_default_size(750, 450)
        self.window.set_title("Panda IRC Client")
        self.window.set_position(gtk.WIN_POS_CENTER)
        self.window.connect("destroy", self.quit)
        self.window.connect("key-press-event",
                            self.change_irctab)
        self.init_ui()
        self.window.add(self.vbox)
        self.window.show_all()
        gtk.gdk.threads_enter()
        gtk.main()
        gtk.gdk.threads_leave()

    '''
        Build the ui and set up callbacks and everything
        else.
    '''
    def init_ui(self):
        self.init_boxs()
        self.init_menu()
        self.init_toolbar()
        self.init_tag_table()
        self.init_tabs()
        self.init_images()

    '''
        Initialize all the box containers that are to be
        used by the ui elements.
    '''
    def init_boxs(self):
        self.vbox = gtk.VBox()

    def init_menu_file(self):
        menu_item_file = gtk.MenuItem("File")
        menu = gtk.Menu()
        
        menu_item_connect = gtk.MenuItem("Connect")
        menu.append(menu_item_connect)

        menu_item_quit = gtk.MenuItem("Quit")
        menu_item_quit.connect("activate", self.quit)
        menu.append(menu_item_quit)
        menu_item_file.set_submenu(menu)
        self.menu_bar.append(menu_item_file)

    def init_menu_edit(self):
        menu_item_edit = gtk.MenuItem("Edit")
        self.menu_bar.append(menu_item_edit)

    def init_menu_help(self):
        menu_item_help = gtk.MenuItem("Help")
        self.menu_bar.append(menu_item_help)

    def init_menu_nick(self):
        self.menu_nick = gtk.Menu()
        self.menu_item_whois = gtk.MenuItem("Whois")
        self.menu_item_whois.connect("activate", self.menu_nick_item,
                                     "whois")
        self.menu_nick.append(self.menu_item_whois)

        self.menu_item_op = gtk.MenuItem("Op")
        self.menu_item_op.connect("activate", self.menu_nick_item,
                                  "op")
        self.menu_nick.append(self.menu_item_op)

        self.menu_item_deop = gtk.MenuItem("Deop")
        self.menu_item_deop.connect("activate", self.menu_nick_item,
                                    "deop")
        self.menu_nick.append(self.menu_item_deop)

        self.menu_item_voice = gtk.MenuItem("Voice")
        self.menu_item_voice.connect("activate", self.menu_nick_item,
                                     "voice")
        self.menu_nick.append(self.menu_item_voice)

        self.menu_item_devoice = gtk.MenuItem("Devoice")
        self.menu_item_devoice.connect("activate", self.menu_nick_item,
                                       "devoice")
        self.menu_nick.append(self.menu_item_devoice)

        self.menu_item_ban = gtk.MenuItem("Ban")
        self.menu_item_ban.connect("activate", self.menu_nick_item,
                                   "ban")
        self.menu_nick.append(self.menu_item_ban)

        self.menu_item_kick = gtk.MenuItem("Kick")
        self.menu_item_kick.connect("activate", self.menu_nick_item,
                                    "kick")
        self.menu_nick.append(self.menu_item_kick)
        self.menu_nick.show_all()

    def init_menu(self):
        self.menu_bar = gtk.MenuBar()
        self.init_menu_file()
        self.init_menu_edit()
        self.init_menu_help()
        self.init_menu_nick()
        self.vbox.pack_start(self.menu_bar, False)

    def init_toolbar(self):
        self.toolbar = gtk.Toolbar()
        self.vbox.pack_start(self.toolbar, False)

    '''
        Initialize a GtkTextTagTable which is used to contain
        all the tags. This tag table is used by every IRCTab.
    '''
    def init_tag_table(self):
        self.tag_table = gtk.TextTagTable()
        
        tag = gtk.TextTag("generic")
        tag.set_property("foreground", "#000000")
        self.tag_table.add(tag)

        tag = gtk.TextTag("green")
        tag.set_property("foreground", "#419b69")
        self.tag_table.add(tag)

        tag = gtk.TextTag("red")
        tag.set_property("foreground", "#700404")
        self.tag_table.add(tag)

    def init_tabs(self):
        self.tabs = gtk.Notebook()
        self.tabs.set_can_focus(False)
        self.tabs.set_scrollable(True)
        self.tabs.connect("switch-page", self.uncolorize_irctab_label)
        self.tabs.connect("page-reordered", self.page_reordered)
        '''
            A tabbed page consists of a GtkTextView,
            GtkEntry and a GtkTreeView. The GtkTextView
            and the GtkTreeView is wrapped in a horizontal box,
            while the latter and the GtkEntry is wrapped in a
            vertical box. Set up the status window.
        '''
        irctab = self.create_irctab("Status")
        self.tabs.set_tab_reorderable(irctab, False)
        self.vbox.pack_start(self.tabs)

    def init_images(self):
        self.img_op = gtk.gdk.pixbuf_new_from_file("images/op.png")
        self.img_voice = gtk.gdk.pixbuf_new_from_file("images/voice.png")

    def get_images(self):
        return (self.img_op, self.img_voice)

    def get_tag_table(self):
        return self.tag_table

    def create_tablabel(self, ident, irctab):
        hbox = gtk.HBox()

        label = gtk.Label(ident)
        hbox.pack_start(label)

        button = gtk.Button()
        button.set_relief(gtk.RELIEF_NONE)
        close_img = gtk.image_new_from_stock(gtk.STOCK_CLOSE,
                                             gtk.ICON_SIZE_MENU)
        button.add(close_img)
        button.connect("clicked", self.del_irctab_ui, irctab)
        hbox.pack_start(button, False, False)
        hbox.show_all()

        return hbox

    def get_irctab(self, ident):
        for i in range(self.tabs.get_n_pages()):
            irctab = self.tabs.get_nth_page(i)
            if irctab.get_ident() == ident.lower():
                return irctab
        return None

    def get_active_irctab(self):
        page_num = self.tabs.get_current_page()

        return self.tabs.get_nth_page(page_num)

    def get_irctabs(self):
        return self.tabs

    def create_irctab(self, ident, treeview=False):
        irctab = IRCTab(self, ident.lower(), treeview)
        tab_label = self.create_tablabel(ident, irctab)
        self.tabs.append_page(irctab, tab_label)
        self.tabs.set_tab_reorderable(irctab, True)
        self.tabs.set_current_page(-1)

        return irctab

    def del_irctab(self, ident):
        for i in range(1, self.tabs.get_n_pages()):
            irctab = self.tabs.get_nth_page(i)
            if irctab.get_ident() == ident:
                break
        self.tabs.remove_page(i)

    def close_irctabs(self):
        num_pages = self.tabs.get_n_pages()
        while num_pages > 0:
            self.tabs.remove_page(num_pages)
            num_pages -= 1

    def colorize_irctab_label(self, irctab):
        page_num = self.tabs.page_num(irctab)
        if page_num == self.tabs.get_current_page():
            return
        tab_label = self.tabs.get_tab_label(irctab)
        tab_label.get_children()[0].modify_fg(
            gtk.STATE_ACTIVE, gtk.gdk.color_parse("#700404"))

    def menu_nick_set_sensitive(self, flag):
        if self.menu_item_op.get_sensitive() == flag:
            return
        self.menu_item_op.set_sensitive(flag)
        self.menu_item_deop.set_sensitive(flag)
        self.menu_item_voice.set_sensitive(flag)
        self.menu_item_devoice.set_sensitive(flag)
        self.menu_item_ban.set_sensitive(flag)
        self.menu_item_kick.set_sensitive(flag)

    '''
        GTK Callback area
    '''
    def uncolorize_irctab_label(self, widget, page,
                                page_num):
        irctab = widget.get_nth_page(page_num)
        tab_label = widget.get_tab_label(irctab)

        tab_label.get_children()[0].modify_fg(
            gtk.STATE_ACTIVE, gtk.gdk.color_parse("#000000"))
        irctab.get_entry().grab_focus()

    def page_reordered(self, widget, child, page_num):
        if not page_num:
            widget.reorder_child(child, 1)

    def change_irctab(self, widget, event):
        if event.state != gtk.gdk.MOD1_MASK:
            return False
        if event.keyval >= 49 and event.keyval <= 57:
            num = int(chr(event.keyval)) - 1
            if num < self.tabs.get_n_pages():
                self.tabs.set_current_page(num)
                irctab = self.tabs.get_nth_page(num)
                irctab.get_entry().grab_focus()

        return False

    def handle_input(self, widget, irctab):
        buf = widget.get_text()
        if buf[0] == "/":
            data = self.expr.match(buf).groups()
            command = data[COMMAND].lower()
            if command in self.cbs:
                self.cbs[command](data)
            else:
                self.get_irctab("Status").append_data(
                    "No such command")
        else:
            if irctab.get_ident() != "status":
                irctab.append_data("%s: %s" % (self.sock.get_nick(), buf))
                self.sock.write("PRIVMSG %s :%s" % (irctab.get_ident(), buf))
        widget.set_text("")

    def scroll_textview(self, widget, event, scroll):
        adj = scroll.get_vadjustment()
        adj.set_value(adj.upper - adj.page_size)

    def row_activated(self, tree, p, column, list_store):
        nick = list_store.get_value(list_store.get_iter(p),
                                    1)
        irctab = self.get_irctab(nick)
        if not irctab:
            irctab = self.create_irctab(nick)
        else:
            self.tabs.set_current_page(self.tabs.page_num(irctab))

    def del_irctab_ui(self, widget, irctab):
        page_num = self.tabs.page_num(irctab)
        if not page_num:
            return
        if not irctab.is_channel():
            self.tabs.remove_page(page_num)
        else:
            self.sock.write("PART %s" % irctab.get_ident())

    def quit(self, widget):
        if self.sock.is_connected():
            self.sock.write("QUIT :%s" % "Pandairc")
        self.window.destroy()
        gtk.main_quit()

    def menu_nicknames(self, widget, event, irctab):
        if event.button != 3:
            return False
        nick = irctab.nick_get_obj(self.sock.get_nick())
        if nick.get_op():
            self.menu_nick_set_sensitive(True)
        else:
            self.menu_nick_set_sensitive(False)
        self.menu_nick.popup(None, None, None, 3,
                                event.get_time())
        return False

    def menu_nick_item(self, widget, cmd):
        irctab = self.get_active_irctab()
        selection = irctab.tree.get_selection()
        list_store, it = selection.get_selected()

        self.cbs[cmd]((cmd, irctab.get_ident(),
                          list_store.get_value(it, 1),
                          None))

    '''
        Callbacks for the commands.
    '''
    def cmd_whois(self, data):
        if not self.sock.is_connected():
            self.get_irctab("Status").append_data(
                "You are not connected to any server")
            return
        if not data[PARAMS]:
            self.get_irctab("Status").append_data(
                "Not enough parameters")
            return
        for i in data[PARAMS].split():
            self.sock.write("WHOIS %s%s" % (data[CHANNELS].split()[0][1:] + " " \
                            if data[CHANNELS] else "", i))

    def cmd_join(self, data):
        if not self.sock.is_connected():
            self.get_irctab("Status").append_data(
                "You are not connected to any server")
            return
        if not data[CHANNELS]:
            self.get_irctab("Status").append_data(
                "Specify a channel")
            return
        for i in data[CHANNELS].split():
            irctab = self.get_irctab(i)
            if irctab:
                page_num = self.tabs.page_num(irctab)
                self.tabs.set_current_page(page_num)
            else:
                self.sock.write("JOIN %s" % i)

    def cmd_part(self, data):
        if not self.sock.is_connected():
            self.get_irctab("Status").append_data(
                "You are not connected to any server")
            return
        if not data[CHANNELS]:
            self.get_irctab("Status").append_data(
                "Specify a channel")
            return
        for i in data[CHANNELS].split():
            self.sock.write("PART %s%s" % (i, " " + data[MESSAGE] if \
                             data[MESSAGE] else ""))

    def cmd_kick(self, data):
        if not self.sock.is_connected():
            self.get_irctab("Status").append_data(
                "You are not connected to any server")
            return
        if not data[CHANNELS]:
            channel = self.get_active_irctab().get_ident()
            if channel == "Status":
                return
        else:
            channel = data[CHANNELS].split()[0]
        if not data[PARAMS]:
            self.get_irctab("Status").append_data(
                "Missing one or more nicks")
        for i in data[PARAMS].split():
            self.sock.write("KICK %s %s%s" % (channel, i,
                            " " + data[MESSAGE] if data[MESSAGE] else ""))

    def cmd_topic(self, data):
        if not self.sock.is_connected():
            self.get_irctab("Status").append_data(
                "You are not connected to any server")
            return
        if not data[CHANNELS]:
            channel = self.get_active_irctab().get_ident()
            if channel == "Status":
                return
        else:
            channel = data[CHANNELS].split()[0]
        self.sock.write("TOPIC %s%s" % (channel,
                        " :" + data[PARAMS][1:] if data[PARAMS] \
                        else ""))

    def cmd_nick(self, data):
        if not self.sock.is_connected():
            self.get_irctab("Status").append_data(
                "You are not connected to any server")
            return
        if not data[PARAMS]:
            self.get_irctab("Status").append_data(
                "Your nickname is %s" % self.sock.get_nick())
            return
        self.sock.write("NICK %s" % data[PARAMS].split()[0])

    def cmd_msg(self, data):
        if not self.sock.is_connected():
            self.get_irctab("Status").append_data(
                "You are not connected to any server")
            return
        if not data[PARAMS]:
            self.get_irctab("Status").append_data(
                "Not enough parameters")
            return
        if data[CHANNELS]:
            channel = data[CHANNELS].split()[0]
            self.sock.write("PRIVMSG %s :%s" % (channel,
                             data[PARAMS][1:]))
            irctab = self.get_irctab(channel)
            if irctab:
                page_num = self.tabs.page_num(irctab)
                self.tabs.set_current_page(page_num)
                irctab.append_data("%s: %s" % (self.sock.get_nick(),
                                   data[PARAMS][1:]))
        else:
            params = data[PARAMS].split()
            irctab = self.get_irctab(params[0])
            if not irctab:
                irctab = self.create_irctab(params[0])
            else:
                page_num = self.tabs.page_num(irctab)
                self.tabs.set_current_page(page_num)
            irctab.append_data("%s: %s" % (self.sock.get_nick(),
                               data[PARAMS][len(params[0]) + 2:]))
            self.sock.write("PRIVMSG %s :%s" % (params[0],
                             data[PARAMS][len(params[0]) + 2:]))

    def cmd_op(self, data):
        self.cmd_mode(data, "+o")

    def cmd_deop(self, data):
        self.cmd_mode(data, "-o")

    def cmd_voice(self, data):
        self.cmd_mode(data, "+v")

    def cmd_devoice(self, data):
        self.cmd_mode(data, "-v")

    def cmd_ban(self, data):
        self.cmd_mode(data, "+b")

    def cmd_unban(self, data):
        self.cmd_mode(data, "-b")

    def cmd_mode(self, data, mode):
        if not self.sock.is_connected():
            self.get_irctab("Status").append_data(
                "You are not connected to any server")
        if not data[CHANNELS]:
            channel = self.get_active_irctab().get_ident()
            if channel == "status":
                return
        else:
            channel = data[CHANNELS].split()[0]
        if not data[PARAMS]:
            self.get_irctab("Status").append_data(
                "Missing one or more nicks")
        else:
            for i in data[PARAMS].split():
                self.sock.write("MODE %s %s %s" % (channel, mode, i))

    def cmd_connect(self, data):
        if self.sock.is_connected():
            self.get_irctab("Status").append_data(
                "A connection is already initiated")
            return
        if not data[PARAMS]:
            self.get_irctab("Status").append_data(
                "Not enough parameters")
            return
        params = data[PARAMS].split()
        port = int(params[1]) if len(params) > 2 else 6667
        self.sock.start_thread(port, params[0])

    def cmd_quit(self, data):
        if not self.sock.is_connected():
            self.get_irctab("Status").append_data(
                "You are not connected to any server")
            return
        self.sock.write("QUIT :%s" % (data[1] if len(data) > 1 \
                         else PandaUI.QUIT_MESSAGE))

    '''
        Subroutine declares the callback dict
        and fills it out.
    '''
    def init_cbs(self):
        self.cbs = {
            "whois"  : self.cmd_whois,
            "join"   : self.cmd_join,
            "part"   : self.cmd_part,
            "nick"   : self.cmd_nick,
            "topic"  : self.cmd_topic,
            "msg"    : self.cmd_msg,
            "op"     : self.cmd_op,
            "deop"   : self.cmd_deop,
            "voice"  : self.cmd_voice,
            "devoice": self.cmd_devoice,
            "kick"   : self.cmd_kick,
            "ban"    : self.cmd_ban,
            "unban"  : self.cmd_unban,
            "quit"   : self.cmd_quit,
            "connect": self.cmd_connect
        }