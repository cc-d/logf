import re
import random as ran
import string as s


ID_CHARS = s.ascii_letters + s.digits + '_-'
ID_LEN = 6  # 68719476736 possible combinations
FUNC_RE = r'^([^ ]+())'


def add_identifier(msg: str) -> str:
    """Adds a random identifier to the log message."""
    _id = ''.join(ran.choices(ID_CHARS, k=ID_LEN))
    fstr = re.search(FUNC_RE, msg).group(0)
    msg = msg.lstrip(fstr)
    return fstr.replace('()', f'({_id})') + msg
