class UserCompare(object):

    def _compare(self, other, method):
        try:
            return method(self._cmpkey(), other._cmpkey())
        except (AttributeError, TypeError):
            # _cmpkey not implemented, or return different type,
            # so I can't compare with "other".
            return NotImplemented

    def __repr__(self):
        return "[%s, %d, %s, %s, %s]" % (self.username, self.userId,
                                         self.toprole, self.mod,
                                         self.admin)

    def __bool__(self):
        return False

    def __str__(self):
        return "%s( username: %s, userid: %d, role: %s, mod: %s, admin: %s)" % (
            "User", self.username, self.userId, self.toprole,
            self.mod, self.admin)

    def __lt__(self, other):
        return self._compare(other, lambda s, o: s < o)

    def __le__(self, other):
        return self._compare(other, lambda s, o: s <= o)

    def __eq__(self, other):
        return self._compare(other, lambda s, o: s == o)

    def __ne__(self, other):
        return self._compare(other, lambda s, o: s != o)

    def __gt__(self, other):
        return self._compare(other, lambda s, o: s > o)

    def __ge__(self, other):
        return self._compare(other, lambda s, o: s >= o)

    def __hash__(self):
        return hash(
            (self.username, self.userId, self.topRole, self.mod, self.admin))


class User(UserCompare):
    def __init__(self, username="", userId=0, toprole="user", mod=False,
                 admin=False, value=None):
        self.username = username
        self.userId = userId
        self.toprole = toprole
        self.mod = mod
        self.admin = admin
        self.value = value

    def _cmpkey(self):
        return self.value
