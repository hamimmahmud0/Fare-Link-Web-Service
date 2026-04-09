from blinker import Namespace
from endpoints_util import announce_utils

# Create a namespace for your app's events
event_manager = Namespace()
announced = event_manager.signal('announced')

# 1. The Subscriber (Listener)
@announced.connect
def handle_new_announce(sender, **kwargs):

    contact = announce_utils.DEFAULT_CONTACT

    for key in announce_utils.REQUIRED_FIELDS:
        contact[key] = kwargs.get(key)
    for key in announce_utils.OPTIONAL_FIELDS:
        if key in kwargs:
            contact[key] = kwargs.get(key)

    # add it to database
    # broadcast to all connected service

    

    

