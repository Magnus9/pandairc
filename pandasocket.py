
from socket import *
import threading
import gtk
import re

'''
    These defines below are to be used in
    conjunction with the regular expression
    match object.
'''
PREFIX  = 0
NICK    = 1
USER    = 2
HOST    = 3
COMMAND = 4
PARAMS  = 5
TRAILER = 6

'''
    The pattern that is to be compiled into a
    match object.
'''
p = (
  "(?::("
    "([^!\s]+)"
    "(?:"
      "(?:"
        "!([^@\s]+)"
      ")?"
      "@([^\s]+)"
    ")?"
  ")\s)?"
  "([^\s]+)"
  "("
    "(?:"
      "\s[^:\s][^\s]*"
    "){0,14}"
  ")"
  "(?:\s:(.*))?"
  "\r\n"
)

class PandaSocket:
    '''
        The socket handler for PandaIRC. It keeps a
        reference to the PandaUI instance for updating
        relevant UI elements on input. It is run as the second
        thread.
    '''
    def __init__(self, ui, port, nick, srv):
        self.ui = ui
        self.nick = nick
        self.init_cbs()
        self.init_mode_cbs()
        self.whois_buffer = ""
        '''
            Start the socket thread if srv != None.
        '''
        if srv:
            self.start_thread(port, srv)

    def start_thread(self, port, srv):
        tid = threading.Thread(target=self.connect,
                               args=(srv, port))
        tid.start()

    def is_connected(self):
        return True if hasattr(self, "sock") else False

    def connect(self, srv, port):
        self.sock = socket(AF_INET, SOCK_STREAM, 0)
        self.sock.settimeout(4)
        try:
            self.sock.connect((srv, port))
        except Exception:
            self.ui.get_irctab("Status").append_data(
                "Failed to connect to server")
            delattr(self, "sock")
            return
        self.sock.settimeout(None)
        self.write("NICK %s" % self.nick)
        self.write("USER %s 8 * :%s" % (self.nick, self.nick))
        self.handle_input()

    def handle_input(self):
        expr = re.compile(p)
        line = ""
        while True:
            c = self.sock.recv(1)
            if not c:
                self.ui.get_irctab("Status").append_data(
                    "Disconnected from server")
                break
            line += c
            if c == "\n":
                try:
                    data = expr.match(line).groups()
                except Exception as e:
                    print(e)
                    line = ""
                    continue
                if data[COMMAND] in self.cbs:
                    gtk.threads_enter()
                    try:
                        self.cbs[data[COMMAND]](data)
                    finally:
                        gtk.threads_leave()
                line = ""
        self.sock.close()
        delattr(self, "sock")
        self.ui.close_irctabs()

    def write(self, data):
        self.sock.send((data + "\r\n").encode("utf-8"))

    def cmd_welcome(self, data):
        self.ui.get_irctab("Status").append_data(
            data[TRAILER])

    def cmd_notice(self, data):
        self.ui.get_irctab("Status").append_data(
            data[TRAILER], "red")

    def cmd_namreply(self, data):
        irctab = self.ui.get_irctab(data[PARAMS].split()[2])
        irctab.nick_add_list(data[TRAILER].split())

    def cmd_endofnames(self, data):
        irctab = self.ui.get_irctab(data[PARAMS].split()[1])
        irctab.nick_add_rows()

    def cmd_ping(self, data):
        self.write("PONG :%s" % data[TRAILER])

    def cmd_join(self, data):
        if data[NICK] == self.nick:
            self.ui.create_irctab(data[PARAMS][1:], True)
            return
        string = "%s (%s) has joined the channel" % \
                  (data[NICK], data[PREFIX])
        irctab = self.ui.get_irctab(data[PARAMS][1:])
        irctab.append_data(string, "green")
        irctab.nick_add(data[NICK])

    def cmd_nosuchnick(self, data):
        irctab = self.ui.get_irctab(data[PARAMS].split()[1])
        if irctab:
            irctab.append_data(data[TRAILER])
        else:
            self.ui.get_irctab("Status").append_data(
                data[TRAILER])

    def cmd_nosuchchannel(self, data):
        self.ui.get_irctab("Status").append_data(
            "Cannot (join/part) channel %s (no such channel)" % \
             data[PARAMS].split()[1])

    def cmd_toomanychannels(self, data):
        self.ui.get_irctab("Status").append_data(
            "Cannot join channel %s (you have joined too many)" % \
             data[PARAMS].split()[1])

    def cmd_channelisfull(self, data):
        self.ui.get_irctab("Status").append_data(
            "Cannot join channel %s (channel is full)" % \
             data[PARAMS].split()[1])

    def cmd_inviteonlychan(self, data):
        self.ui.get_irctab("Status").append_data(
            "Cannot join channel %s (invite only)" % \
             data[PARAMS].split()[1])

    def cmd_bannedfromchan(self, data):
        self.ui.get_irctab("Status").append_data(
            "Cannot join channel %s (you are banned)" % \
             data[PARAMS].split()[1])

    def cmd_badchannelkey(self, data):
        self.ui.get_irctab("Status").append_data(
            "Cannot join channel %s (wrong channel key)" % \
             data[PARAMS].split()[1])

    def cmd_part(self, data):
        if data[NICK] == self.nick:
            self.ui.del_irctab(data[PARAMS][1:])
            return
        string = "%s (%s) has left the channel" % \
                  (data[NICK], data[PREFIX])
        irctab = self.ui.get_irctab(data[PARAMS][1:])
        irctab.append_data(string, "green")
        irctab.nick_del(data[NICK])

    def cmd_privmsg(self, data):
        string = "%s: %s" % (data[NICK], data[TRAILER])
        if data[PARAMS][1:] == self.nick:
            irctab = self.ui.get_irctab(data[NICK])
            if not irctab:
                irctab = self.ui.create_irctab(data[NICK])
        else:
            irctab = self.ui.get_irctab(data[PARAMS][1:])
        irctab.append_data(string)

    def cmd_kick(self, data):
        params = data[PARAMS].split()
        reason = data[TRAILER] if data[TRAILER] != params[1] \
                 else "No reason specified"
        if params[1] == self.nick:
            string = "You got kicked from channel %s by %s." \
                     " Reason: %s" % (params[0], data[NICK], reason)
            self.ui.get_irctab("Status").append_data(string)
            self.ui.del_irctab(params[0])
        else:
            string = "%s got kicked by %s. Reason: %s" % (params[1],
                      data[NICK], reason)
            irctab = self.ui.get_irctab(params[0])
            irctab.append_data(string, "red")
            irctab.nick_del(params[1])

    def cmd_quit(self, data):
        string = "%s (%s) has quit: %s" % (data[NICK],
                  data[PREFIX], data[TRAILER])
        irctabs = self.ui.get_irctabs()
        for i in range(1, irctabs.get_n_pages()):
            irctab = irctabs.get_nth_page(i)
            if irctab.nick_index(data[NICK]) != None:
                irctab.append_data(string, "red")
                irctab.nick_del(data[NICK])

    def cmd_nick(self, data):
        if data[NICK] == self.nick:
            string = "Your nickname has been changed to %s" % \
                      data[TRAILER]
            self.nick = data[TRAILER]
        else:
            string = "%s changed his nickname to %s" % (data[NICK],
                      data[TRAILER])
        irctabs = self.ui.get_irctabs()
        for i in range(1, irctabs.get_n_pages()):
            irctab = irctabs.get_nth_page(i)
            if irctab.nick_index(data[NICK]) != None:
                irctab.append_data(string)
                irctab.nick_update_nick(data[NICK], data[TRAILER])

    def cmd_nicknameinuse(self, data):
        self.ui.get_irctab("Status").append_data(
            "The nickname %s is already in use" % \
             data[PARAMS].split()[1])

    def cmd_erroneusnickname(self, data):
        self.ui.get_irctab("Status").append_data(
            "The nickname %s contains characters " \
            "that are not allowed" % data[PARAMS].split()[1])

    def cmd_nickcollision(self, data):
        self.ui.get_irctab("Status").append_data(
            data[TRAILER])

    def cmd_invite(self, data):
        self.ui.get_irctab("Status").append_data(
            "%s (%s) has invited you to join channel %s" % \
             (data[NICK], data[PREFIX], data[TRAILER]))

    def cmd_topic(self, data):
        irctab = self.ui.get_irctab(data[PARAMS][1:])
        irctab.append_data("%s changed the topic to: %s" % (data[NICK],
                            data[TRAILER]))

    def cmd_topic2(self, data):
        irctab = self.ui.get_irctab(data[PARAMS].split()[1])
        irctab.set_topic(data[TRAILER])

    def cmd_topic_creator(self, data):
        params = data[PARAMS].split()
        irctab = self.ui.get_irctab(params[1])
        irctab.set_topic_creator(params[2])
        irctab.set_topic_ts(params[3])
        irctab.append_data(irctab.gen_topic_string(), "green")

    def cmd_mode(self, data):
        params = data[PARAMS].split()
        if params[0] == self.nick:
            self.ui.get_irctab("Status").append_data(
                "New mode set (%s)" % data[TRAILER])
        else:
            if params[1][1] in self.mode_cbs:
                self.mode_cbs[params[1][1]](params, data[NICK])

    def get_nick(self):
        return self.nick

    '''
        Subroutine declares the callback dict
        and fills it out.
    '''
    def init_cbs(self):
        self.cbs = {
            "NOTICE" : self.cmd_notice,
            "001"    : self.cmd_welcome,
            "002"    : self.cmd_welcome,
            "003"    : self.cmd_welcome,
            "004"    : self.cmd_welcome,
            "005"    : self.cmd_welcome,
            "250"    : self.cmd_welcome,
            "251"    : self.cmd_welcome,
            "252"    : self.cmd_welcome,
            "253"    : self.cmd_welcome,
            "254"    : self.cmd_welcome,
            "255"    : self.cmd_welcome,
            "265"    : self.cmd_welcome,
            "266"    : self.cmd_welcome,
            "375"    : self.cmd_welcome,
            "372"    : self.cmd_welcome,
            "376"    : self.cmd_welcome,
            "MODE"   : self.cmd_mode,
            "353"    : self.cmd_namreply,
            "366"    : self.cmd_endofnames,
            "401"    : self.cmd_nosuchnick,
            "433"    : self.cmd_nicknameinuse,
            "432"    : self.cmd_erroneusnickname,
            "436"    : self.cmd_nickcollision,
            "403"    : self.cmd_nosuchchannel,
            "405"    : self.cmd_toomanychannels,
            "471"    : self.cmd_channelisfull,
            "473"    : self.cmd_inviteonlychan,
            "474"    : self.cmd_bannedfromchan,
            "475"    : self.cmd_badchannelkey,
            "PING"   : self.cmd_ping,
            "JOIN"   : self.cmd_join,
            "PART"   : self.cmd_part,
            "KICK"   : self.cmd_kick,
            "PRIVMSG": self.cmd_privmsg,
            "QUIT"   : self.cmd_quit,
            "NICK"   : self.cmd_nick,
            "INVITE" : self.cmd_invite,
            "TOPIC"  : self.cmd_topic,
            "332"    : self.cmd_topic2,
            "333"    : self.cmd_topic_creator,
            "311"    : self.cmd_whoisuser,
            "312"    : self.cmd_whoisserver,
            "318"    : self.cmd_endofwhois
        }

    def cmd_whoisuser(self, data):
        params = data[PARAMS].split()
        string = "%s (%s@%s)\n" % (params[1], params[2],
                  params[3])
        self.whois_buffer += string

    def cmd_whoisserver(self, data):
        params = data[PARAMS].split()
        string = " server : %s (%s)\n" % (params[2],
                  data[TRAILER])
        self.whois_buffer += string

    def cmd_endofwhois(self, data):
        self.whois_buffer += "End of WHOIS"
        irctab = self.ui.get_irctab(data[PARAMS].split()[1])
        if irctab:
            irctab.append_data(self.whois_buffer)
        else:
            self.ui.get_irctab("Status").append_data(
                self.whois_buffer)
        self.whois_buffer = ""

    def init_mode_cbs(self):
        self.mode_cbs = {
            "o" : self.cmd_mode_op,
            "v" : self.cmd_mode_voice,
            "b" : self.cmd_mode_ban
        }

    def cmd_mode_op(self, params, nick):
        if params[1] == "+o":
            string = "%s was given operator status by %s"
        else:
            string = "%s was taken away operator status by %s"
        string = string % (params[2], nick)
        irctab = self.ui.get_irctab(params[0])
        irctab.append_data(string, "green")
        irctab.nick_set_mode(params[2], params[1])

    def cmd_mode_voice(self, params, nick):
        if params[1] == "+v":
            string = "%s was given voice status by %s"
        else:
            string = "%s was taken away voice status by %s"
        string = string % (params[2], nick)
        irctab = self.ui.get_irctab(params[0])
        irctab.append_data(string, "green")
        irctab.nick_set_mode(params[2], params[1])

    def cmd_mode_ban(self, params, nick):
        if params[1] == "+b":
            string = "%s was banned by %s"
        else:
            string = "%s was unbanned by %s"
        string %= (params[2], nick)
        irctab = self.ui.get_irctab(params[0])
        irctab.append_data(string, "red")
