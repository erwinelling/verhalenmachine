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

    # check things for what needs to be cleaned


class Uploader:
    def __init__(self):
        pass

    def check_files_to_upload(self):
        pass

    def upload_track(self, track):
        pass

    def upload_tracklist(self, tracklist):
        pass
