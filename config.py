""" config file for omxplayer """


OMXPLAYER = '/usr/bin/omxplayer -o both'
DB = '/run/omxplayer-flask/db.txt'
KILL_PLAYER_CMD = '/usr/bin/pkill omxplayer'

try:
    # try to overwrite these values with a secret file
    import secret
    PATH = secret.PATH
    PATHS = secret.PATHS
    MUSIC_PATH = secret.MUSIC_PATH
except ImportError:
    PATH = ''
    MUSIC_PATH = ''
    PATHS = {}
