from mycroft import MycroftSkill, intent_file_handler
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.skills.audioservice import AudioService
import mycroft.util.parse
from mycroft.util.parse import match_one

import requests
import json
import urllib
import re
import os
import subprocess
import signal
import shlex
import threading


track_dict = {
 'soundcloud': 'https://soundcloud.com/sideshowshottie/maribou-state-tongue-feat-holly-walker-drum-and-bass-remix'
}

class MycroftSoundcloud(CommonPlaySkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.spoken_name = "Sound Cloud"
        self.regexes = {}
        self.state = "stopped"

    def initialize(self):
        super().initialize()


        self.add_event('mycroft.audio.service.resume', self.resume)
        self.add_event('mycroft.audio.service.pause', self.pause)

        self.log.info("Checking if Soundcloud already running")
        try:
            if (self.settings["curl_pid"] != None and self.settings["player_pid"] != None):
                self.log.info("Running Player found")
                self.handle_stop()
        except:
            self.log.info("No Running Player found")


        self.create_intents

    def create_intents(self):
        self.register_intent_file('StopMusic.intent', self.handle_stop)



    def CPS_match_query_phrase(self, phrase):
        """ This method responds wether the skill can play the input phrase.

            The method is invoked by the PlayBackControlSkill.

            Returns: tuple (matched phrase(str),
                            match level(CPSMatchLevel),
                            optional data(dict))
                     or None if no match was found.
        """
        soundcloud_specified = 'soundcloud' in phrase
        bonus = 0.1 if soundcloud_specified else 0.0
        phrase = re.sub(self.translate_regex('on_soundcloud'), '', phrase,
                        re.IGNORECASE)



        confidence, data = self.query(phrase, bonus)

        if soundcloud_specified:
            # " play song on soundcloud'
            level = CPSMatchLevel.EXACT
            return ("soundcloud", level, {"track": "soundcloud"})
        else:
            return None

    def CPS_start(self, phrase, data):
        """ Starts playback.

            Called by the playback control skill to start playback if the
            skill is selected (has the best match level)
        """
        self.log.info("Starting Music")
        self.play_from_url("https://soundcloud.com/sideshowshottie/maribou-state-tongue-feat-holly-walker-drum-and-bass-remix")
        pass


    def query(self, phrase, bonus):
    """ Search the phrase on soundcloud in the following order:
        1.


    """

        return (1.0,
                {
                    'data': None,
                    'name': None,
                    'type': 'continue'}
                )



    def pause(self, message=None):
        """ Handler for playback control pause. """
        self.log.info("Pausing")
        if (self.settings.get('player_pid') != None):
            os.kill(self.settings.get('player_pid'), signal.SIGSTOP)
            self.state = "paused"

    def resume(self, message=None):
        """ Handler for playback control resume. """
        self.log.info("Resuming")
        # if authorized and playback was started by the skill
        if (self.settings.get('player_pid') != None):
            os.kill(self.settings.get('player_pid'), signal.SIGCONT)
            self.state = "playing"


    def handle_stop(self):
        self.log.info("Stopping Soundcloud Player")
        if (self.settings.get('curl_pid') != None):
            os.kill(self.settings.get('curl_pid'), signal.SIGHUP)
            os.kill(self.settings.get('curl_pid'), signal.SIGTERM)
        if (self.settings.get('player_pid') != None):
            os.kill(self.settings.get('player_pid'), signal.SIGHUP)
            os.kill(self.settings.get('player_pid'), signal.SIGTERM)

        self.settings["curl_pid"] = None
        self.settings["player_pid"] = None
        self.state = "stopped"

    def play_url(self, url):
        # play sound

        if(self.state == "playing"):
            self.handle_stop()

        args1 = shlex.split("curl \"" + url + "\"")
        args2 = shlex.split("mpg123 -q -")
        curl = subprocess.Popen(args1, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        player = subprocess.Popen(args2, stdin=curl.stdout)

        self.settings["curl_pid"] = curl.pid
        self.settings["player_pid"] = player.pid
        self.state = "playing"


    def trackID_from_url(self, url):
        web_url = requests.get(url)
        track_id = re.findall("[0-9]+" ,str(re.findall("api.soundcloud.com[/]tracks[/][0-9]+", str(web_url.content))))[0]
        print ("Track ID Found: " + track_id)
        return track_id

    def media_url_from_trackID(self, track_id):
        # some bs to find the audio tracks url
        track_url = requests.get("https://api-v2.soundcloud.com/tracks/" + track_id + "?client_id=" + self.settings.get('client_id'))
        json = track_url.json()
        track_url = json['media']['transcodings'][1]['url'] + "?client_id=" + self.settings.get('client_id')
        media_url = requests.get(track_url)
        media_url = media_url.json()['url']
        return media_url


    def play_from_trackID(self, track_id):
        self.play_url(self.media_url_from_trackID(track_id))


    def play_from_url(self, url):
        track_id = self.trackID_from_url(url)
        self.play_from_trackID(track_id)

    def song_finished(self):
        self.handle_stop()

    def translate_regex(self, regex):
        if regex not in self.regexes:
            path = self.find_resource(regex + '.regex')
            if path:
                with open(path) as f:
                    string = f.read().strip()
                self.regexes[regex] = string
        return self.regexes[regex]


def create_skill():
    return MycroftSoundcloud()



