# python-mpd2


# from mpd import MPDClient
# client = MPDClient()
# # #to connect to MPD you need to know the IP address and port
# client.connect("localhost", 6600)

# #set the volume between 0 and 100
# client.setvol(100)
#
# #play song at certain position
# client.play(1)
#
# #pause and resume playback
# client.pause(0)
# client.pause(1)
#
# #skip to the next or previous track
# client.next()
# client.previous()
#
# #clear current playlist and load a new one
# client.playlistclear()
# client.load("nameofyourplaylist")


# class Employee:
#    'Common base class for all employees'
#    empCount = 0
#
#    def __init__(self, name, salary):
#       self.name = name
#       self.salary = salary
#       Employee.empCount += 1
#
#    def displayCount(self):
#      print "Total Employee %d" % Employee.empCount
#
#    def displayEmployee(self):
#       print "Name : ", self.name,  ", Salary: ", self.salary

class Player:
    'Player'
    # empCount = 0
    playing = False

    def __init__(self):
        pass
        # from mpd import MPDClient
        # self.client = MPDClient()
        # self.client.connect("localhost", 6600)


    # def is_playing(self):
    #     pass
    #
    # def is_paused(self):
    #     pass

    def play(self):
        # RESEARCH: how to control meter with audio input
        pass

    def pause(self):
        pass

    def next(self):
        pass

    def stop(self):
        pass

    def set_volume(self, volume):
        # RESEARCH: how to control volume
        # RESEARCH: how to check slider value
        pass

    def load_playlist(self):
        pass

    # def update_playlist(self):
    #     pass

class Recorder:
    'Recorder'
    recording = False
    last_recording_starttime = ""

    def __init__(self):
        pass

    # def is_recording(self):
    #     pass

    def record(self):
    # RESEARCH: how to control meter with mic input
        pass

    def stop(self):
        pass

class Buttons:
    #TODO: set button numbers?

    def __init__(self):
        pass

    def check_pressed(self, number):
        pass

    def turn_light_on(self, number):
        pass

    def turn_light_off(self, number):
        pass

class Cleaner:
    def __init__(self):
        pass

    # what needs to be cleaned:
    # skip 0 byte wave files
    # Fixen als hij te lang opneemt wav-01, wav-02, wav-03
    # Te grote bestanden verwijderen apparaat
    # Opname stoppen na een uur?
    # Te grote files negeren

class Uploader:
    def __init__(self):
        pass

    def check_files_to_upload(self):
        pass

    def upload_track(self, track):
        pass

    def upload_tracklist(self, tracklist):
        pass
