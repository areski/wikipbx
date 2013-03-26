import datetime
import os
import time
from freeswitch import *
from django.conf import settings
from pytz import timezone
from wikipbx import ttsutil
from wikipbx.wikipbxweb.models import *


class BaseIvr(object):

    def __init__(self, session):
        self.session=session
        self.tts_voice = settings.TTS_DEFAULT_VOICE
        self.session.set_tts_parms("cepstral", self.tts_voice)

        if not self.empty("account_id"):
            self.account_id = self.session.getVariable("account_id")
            self.account = Account.objects.get(pk=self.account_id)
        else:
            self.account = None
            self.account_id = None

    def empty(self, variable_name):
        """
        due to a bug in mod_python, when a variable is not defined,
        it returns the _string_ "None"
        """
        variable_value = self.session.getVariable(variable_name)        
        if not variable_value or variable_value == "None":        
            return True
        else:
            return False
        
    def playbeep(self):
        path = os.path.join(settings.INSTALL_ROOT,
                            "soundclips",
                            "beep.wav")
        self.session.streamFile(path)        

        
    def speak(self, tts_string, stream=False, cache=True):
        """
        @param text - the text to be spoken
        @param stream - stream the data directly by calling session.speak() or
                        make a temp file and stream contents of file
        @param cache - if stream=False, the this param tells whether to look
                       for a cached version of file or not.

        NOTE: if stream is false, you will need to have either
        cepstral or festival installed.  See ttsutil.py
        """
        if stream == True:
            self.session.speak(tts_string)
            return

        tts_file = self.make_tts_file(tts_string, cache=cache)
        self.session.streamFile(tts_file)

    def make_tts_file(self, tts_string, cache=True):
        return ttsutil.make_tts_file(tts_string,
                                     tts_voice=self.tts_voice,
                                     cache=cache)

