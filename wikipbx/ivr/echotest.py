import os
from freeswitch import *
from django.conf import settings

"""
play a welcome audio and then start the echo test
if you installed wikipbx to a different directory,
change the path accordingly

For this to work, the wikipbx directory will need to be
in the PTYHONPATH environment variable when starting
freeswitch:

export PYTHONPATH=$PYTHONPATH:/usr/src/wikipbx
./freeswitch -nc -hp

"""

def handler(session, args):

    session.answer()

    path = os.path.join(settings.INSTALL_ROOT,
                        "soundclips",
                        "welcome_echo.wav")
    session.streamFile(path)        

    session.execute("echo")
