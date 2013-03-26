""" 
WikiPBX web GUI front-end for FreeSWITCH <www.freeswitch.org>
Copyright (C) 2007, Branch Cut <www.branchcut.com>
License Version: MPL 1.1
"""

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'wikipbx.settings'

from freeswitch import console_log
from django.conf import settings
from wikipbx.wikipbxweb import models
import wikipbx.ivr.baseivr
reload(wikipbx.ivr.baseivr)
from wikipbx.ivr.baseivr import BaseIvr


class SoundclipRecorder(BaseIvr):
    """
    Soundclip recorder IVR.

    It looks for soundclip name and optional description in session variables.
    """

    def __init__(self, session):
        super(SoundclipRecorder, self).__init__(session)        
        self.tts_voice = settings.TTS_DEFAULT_VOICE
        self.session.set_tts_parms("cepstral", self.tts_voice)

    def main(self):
        """
        Main entry point.
        """
        if self.empty("name"):
            console_log("error", "Soundclip recorder did not receive name")
            self.session.speak(
                "Sorry, the soundclip recorder had an error. Missing name or "
                "description variables. Error code 103.")
            return
        
        soundclip_name = self.session.getVariable("name")
        soundclip_desc = (
            "" if self.empty('desc') else
            self.session.getVariable("desc"))

        soundclip, _created = models.Soundclip.objects.get_or_create(
            name=soundclip_name, account=self.account)
        soundclip.desc = soundclip_desc
        soundclip.save()

        # Play beep.
        self.session.answer()
        self.playbeep()

        # Sleep, otherwise we hear the beep in the recording.
        self.session.execute("sleep", "500")

        # Path to recorded file.
        soundclip_path = soundclip.get_path()

        # Allow user to interrupt the recording
        self.session.setInputCallback(input_callback)

        max_len = 360
        silence_threshold = 500
        silence_secs = 5
        self.session.recordFile(
            soundclip_path.encode('utf-8'), max_len, silence_threshold,
            silence_secs)

        self.session.speak("Your sound clip has been recorded. Goodbye")


def input_callback(session, what, obj):
    """
    Callback function. 
    It checks for dialed DTMF and interrupt the recording on '#' or '*'.
    """
               
    if (what == "dtmf"):
        if obj.digit == "*" or obj.digit == "#":
            # Stop recording
            return "false"
    # Keep recording        
    return "true"


def handler(session, _args):
    screcorder = SoundclipRecorder(session)
    screcorder.main()
