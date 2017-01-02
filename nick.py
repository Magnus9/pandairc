
'''
    Nick objects are used to describe both the nickname,
    and the status of the nickname. They are used in
    conjunction with the gtk.ListStore object to show
    the nicknames in the correct order and with the correct
    status.

    Status precedence: op, voice, none.
'''
class Nick:
    def __init__(self, nick, op=False, voice=False):
        self.nick = nick
        self.op = op
        self.voice = voice

    def set_nick(self, nick):
        self.nick = nick

    def get_nick(self):
        return self.nick

    def set_op(self, op):
        self.op = op

    def get_op(self):
        return self.op

    def set_voice(self, voice):
        self.voice = voice

    def get_voice(self):
        return self.voice