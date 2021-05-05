from mycroft import MycroftSkill, intent_file_handler


class MycroftSoundcould(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('soundcould.mycroft.intent')
    def handle_soundcould_mycroft(self, message):
        self.speak_dialog('soundcould.mycroft')


def create_skill():
    return MycroftSoundcould()

