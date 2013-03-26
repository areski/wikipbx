import datetime
import os
import shutil
import subprocess
import string
import sys
import time
from django.conf import settings
from hashlib import md5
from pytz import timezone


def make_tts_file(tts_string, tts_voice=None, cache=True):
    static_tts_engine = get_static_tts_engine()
    hexdigest = md5(tts_string.encode('utf-8')).hexdigest()
    tts_dest = os.path.join(settings.TEMP_DIR, "wikipbx", "tts")
    if not os.path.exists(tts_dest):
        os.makedirs(tts_dest)
    file2write = os.path.join(tts_dest, "%s-%s.wav" % (hexdigest, tts_voice))
    if cache and os.path.exists(file2write):
        return file2write

    if static_tts_engine == "festival":
        if make_tts_file_festival(tts_string, file2write):
            return file2write
        else:
            raise Exception(
                "Error calling festival. File2write: %s" % file2write)
    else:
        if tts_voice:
            cmd = ["swift", "-n", tts_voice, tts_string, "-o", file2write]
        else:
            cmd = ["swift", tts_string, "-o", file2write]

    subprocess.check_call(cmd)

    # was the file created?
    if not os.path.exists(file2write):
        raise Exception("Failed to create tts audio file")
    
    return file2write

def make_tts_file_festival(tts_string, file2write):
    cmd = "text2wave -scale 2 -o %s" % (file2write)
    fd = os.popen(cmd, 'w')
    fd.write(tts_string)
    exit_code = fd.close()
    if exit_code is not None and exit_code != 0:
        raise Exception("Command failed: %s" % cmd)
    return samplefreq8k( file2write )

def runCommand(command, reqSuccess=True, showDebug=False):
    if showDebug:
        print command
    returncode = os.system(command)
    if reqSuccess:
        if returncode is not None and returncode != 0:
            raise "Error, command %s failed" % command

def samplefreq8k(origwav):
    """
    Converts the given wave file to have a sample frequency of 8 kHZ.
    """
    # copy orig to temp
    tempWavFile = tempfile.NamedTemporaryFile(suffix=".wav", dir=settings.TEMP_DIR)
    shutil.copy(origwav, tempWavFile.name)

    # convert temp to be 8kz, and overwrite orig
    cmd = "sox %s -r 8000 %s" % (tempWavFile, origwav)
    runCommand(cmd)

    # delete temp
    tempWavFile.close()
    
    return origwav

def get_static_tts_engine():
    """
    check settings.py and see if there is a variable set.
    if so, return it.  otherwise return default (cepstral)
    """
    if settings.__dict__.has_key("STATIC_TTS_ENGINE"):
        return settings.STATIC_TTS_ENGINE
    else:
        return "cepstral"

