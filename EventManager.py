from blinker import Namespace
from endpoints_util import contact_utils
from db import *
# Create a namespace for your app's events
event_manager = Namespace()

# Contact signals
contact_announce = event_manager.signal('contact_announce')
contact_search = event_manager.signal('contact_search')
contact_broadcast_new = event_manager.signal('broadcast_new_contact')

# 1. The Subscriber (Listener)
@contact_announce.connect
def handle_contact_announce(sender, **kwargs):

    contact = contact_utils.DEFAULT_CONTACT

    for key in contact_utils.REQUIRED_FIELDS:
        contact[key] = kwargs['data'].get(key)
    for key in contact_utils.OPTIONAL_FIELDS:
        if key in kwargs['data']:
            contact[key] = kwargs['data'].get(key)

    # add it to database

    add_contact(contact)
    # broadcast to all connected service
    contact_broadcast_new.send('event_manager',data=contact)

    

@contact_search.connect
def handle_contact_search(sender, **kwargs):
    return search_contact(kwargs['data']['user-id'])    

