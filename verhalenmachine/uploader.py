import datetime
import logging, logging.handlers
# import mpd
import os
import psutil
import re
import RPi.GPIO as GPIO
# import serial
import signal
import sys
import subprocess
import tempfile
import time
# import pdb
import ConfigParser
import soundcloud
from socketIO_client import SocketIO, LoggingNamespace
from threading import Thread

# TODO: cleanup imports

import logging
logger = logging.getLogger('root')

HOME_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
config = ConfigParser.ConfigParser()
config.read(os.path.join(HOME_DIR, "verhalenmachine.cfg"))

class Uploader:
    # TODO: Maybe implement uploading to several playlists again (settings or ip or wlan name or ...)
    # TODO: Upload to playlist
    def __init__(self):
        # self.client = soundcloud.Client(client_id="2afa000b9c16670dd62c83700567487f", client_secret="dbf7e4b8b8140f142b62c8e93b4d0ab8", username="erwin@uptous.nl", password="ell82SOU!")
        self.client = soundcloud.Client(
            client_id = config.get("uploader", "client_id"),
            client_secret = config.get("uploader", "client_secret"),
            username = config.get("uploader", "username"),
            password = config.get("uploader", "password"),
        )
        logger.debug("SOUNDCLOUD connected to %s " % self.client.get('/me').username)

        self.RECORDING_DIR = config.get("uploader", "recording_dir")

    def clean_directory(self, directory=""):
        if directory == "":
            directory = self.RECORDING_DIR
        for root, dirs, files in os.walk(directory):
            for filename in files:
                # logger.debug("FILESIZE %s %s" % (filename, os.path.getsize(os.path.join(root, filename))))
                # Remove 0 byte files
                # TODO: Maybe add max size, i.e. Remove bigger than x GB? (x 1000 000 000 bytes)
                if filename.lower().endswith(('.aiff', '.wav', '.flac', '.alac', '.ogg', '.mp2', '.mp3', '.aac', '.amr', '.wma')) and not filename.startswith('.'):
                    if os.path.getsize(os.path.join(root, filename)) <= 50: # or os.path.getsize(filename) > xxxx
                        path_to_file = os.path.join(root, filename)
                        logger.debug("REMOVING %s %s" % (filename, os.path.getsize(os.path.join(root, filename))))
                        os.remove(path_to_file)
                        not_uploaded_file = os.path.splitext(path_to_file)[0]+".notuploaded"
                        os.remove(not_uploaded_file)

    def upload_directory(self, directory=""):
        if directory == "":
            directory = self.RECORDING_DIR
        # walk through all files in recording directory
        logger.debug("Checking contents of %s", directory)
        count = 0 # TODO: Remove and just us uploaded_track_list.length()
        uploaded_track_list=[]
        # TODO: Replace with counter object
        for root, dirs, files in os.walk(directory):
            for filename in files:
                # check whether it is a music file that can be uploaded to soundcloud
                # http://uploadandmanage.help.soundcloud.com/customer/portal/articles/2162441-uploading-requirements
                # AIFF, WAVE (WAV), FLAC, ALAC, OGG, MP2, MP3, AAC, AMR, and WMA
                # and ignore hidden files
                if filename.lower().endswith(('.aiff', '.wav', '.flac', '.alac', '.ogg', '.mp2', '.mp3', '.aac', '.amr', '.wma')) and not filename.startswith('.'):
                    path_to_file = os.path.join(root, filename)
                    logger.debug(path_to_file)
                    not_uploaded_file = os.path.splitext(path_to_file)[0]+".notuploaded"
                    if os.path.isfile(not_uploaded_file):
                        uploaded_track = self.upload_track(path_to_file)
                        count = count+1
                        # TODO: Keep list of uploaded tracks
                        # uploaded_track_list.append(uploaded_track.id)

        # TODO: Create or appenn to playlist
        logger.debug("UPLOADED %s files" % count)

    def upload_track(self, path_to_file):
        # get playlist
        # set_id = os.path.basename(os.path.normpath(os.path.dirname(path_to_file)))
        # logger.debug("Set id: %s", set_id)
        # playlist = client.get("/playlists/"+set_id)
        # logger.debug("Playlist: %s", playlist)
        track_dict = {
            # TODO: Set more track data, get input somewhere
            'title': unicode(os.path.splitext(path_to_file)[0]),
            'asset_data': open(path_to_file, 'rb'),
            'description': u'Dit verhaal is opgenomen met de verhalenmachine op %s om %s.' % (datetime.datetime.now().__format__("%e-%m-%Y"), datetime.datetime.now().__format__("%T")),
            'track_type': 'spoken',
            'license': "cc-by-nc",
            'sharing': "private",
            # 'purchase_url': "http://wijzijnjimmys.nl/verhalen/",
            # 'tag_list': "jimmys verhalen"
            # 'genre': 'Electronic',
        }
        # if os.path.isfile(img_file):
        #     track_dict['artwork_data'] = open(img_file, 'rb')
        #
        try:
            uploaded_track = self.client.post('/tracks', track=track_dict)
            logger.debug("Uploaded %s to Soundcloud: %s (%s).", path_to_file, uploaded_track.permalink_url, uploaded_track.id)
            not_uploaded_file = os.path.splitext(path_to_file)[0]+".notuploaded"
            os.remove(not_uploaded_file)
            return uploaded_track
        except:
            logger.debug("Error uploading to Soundcloud")
            logger.debug(sys.exc_info()[0])
            return None


        #
        # # add soundcloud id to filename
        # filename_with_soundcloud_id = "%s.%s%s" % (os.path.splitext(path_to_file)[0], uploaded_track.id, os.path.splitext(path_to_file)[1])
        # os.rename(path_to_file, filename_with_soundcloud_id)
        #
        # # Add Track to right Set
        # # f = open(soundcloud_set_file)
        # # set_id = f.readline().strip().split("&", 1)[0].replace("id=", "")
        # # f.close()
        # if uploaded_track:
        # UPDATE_TRACKLIST

        # count +=1

    def create_playlist(self, name):
        # TODO: Implement
        # # create an array of track ids
        # tracks = map(lambda id: dict(id=id), [290, 291, 292])
        #
        # # create the playlist
        # client.post('/playlists', playlist={
        #     'title': name,
        #     'sharing': 'public',
        #     'tracks': tracks
        # })
        ## return created_playlist
        pass

    def update_playlist(self, tracklist):
        # TODO: Implement
        # playlist = client.get("/playlists/"+set_id)
        #     # generate tracklist of current playlist
        #     track_id_list = []
        #     for track in playlist.tracks:
        #         track_id_list.append(track['id'])
        #     logger.debug("%s, %s", playlist.title, track_id_list)
        #
        #     # add uploaded track to list
        #     track_id_list.append(uploaded_track.id)
        #
        #     updated_playlist = client.put("/playlists/"+set_id, playlist={
        #         'tracks': map(lambda id: dict(id=id), track_id_list)
        #     })
        #     logger.debug("%s, %s", updated_playlist.title, track_id_list)
        ## return updated_playlist
        pass
