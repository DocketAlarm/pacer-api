msg="""
*****************************************************************************
*                                                                           *
*                Welcome to the Docket Alarm API Sample Program             *
*                                                                           *
*****************************************************************************

This program guides you through some of the capabilities of the Docket Alarm 
API. It will show you how to search and download docket information and how to
read the output.

What you will need:
- A Docket Alarm user name and password. If you do not have one, you can sign 
  up at https://www.docketalarm.com. You will need to either enter your credit 
  card or enter your PACER credentials to get a valid login.
- A text editor, such as notepad++, will be helpful to read the python source 
  code corresponding to this program.

"""

import pprint
import os
import sys
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import logging

# This if statement is only really used internally or if you're using it in a 
# django environment. Most likely, you can delete or ignore.
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
	ROOT_PATH = os.path.dirname(__file__)
	sys.path.append(ROOT_PATH)
	sys.path.append(os.path.join(ROOT_PATH, '../'))
	sys.path.append(os.path.join(ROOT_PATH, '../libs/'))
	os.environ["DJANGO_SETTINGS_MODULE"] = "settings"

# The following two imports are necessary to use the Docket Alarm API
#import api
from api import client as api_client

# Turn on logging
logging.basicConfig(
	level = logging.DEBUG,
	format = '%(asctime)s %(levelname)s %(message)s',
)
pp = pprint.PrettyPrinter(indent=4)

# You can specify your credentials here rather than at the command prompt.
username, password = None, None

##################################
# API Client Options
# Set to True to just test. This will return fake data, but costs nothing.
api_client.TESTING = False
# Wait for input before making url fetch
api_client.PRESS_KEY_BEFORE_CALL = True
# Wait for input before going to the next step
api_client.PRESS_KEY_AFTER_CALL = True

# Development Flag, do not use
api_client.USE_LOCAL = False

def call_api(call, msg=None, get_args=None, post_args=None, error_expected=False):
    if msg:
        print("")
        print(msg)
        if error_expected:
            print("We are expecting this to return an error message.")
    
    if post_args:
        method = "POST"
        args = post_args
    else:
        method="GET"
        args = get_args
    
    out = api_client.call(call=call, method=method, **args)
    
    print("\nAPI Results:")
    pprint.pprint(out)
        
    if out.get('error') and not error_expected:
        raise Exception(out['error'])
    
    print("")
    
    return out

def do_print(out):
    return pp.pprint( out )

part_no = 1
def print_title(msg):
    global part_no
    print("\n\n---------------------------------")
    print(("Part %d: %s"%(part_no, msg)))
    part_no += 1

if __name__ == "__main__":
    print(msg)
    if not username or password:
        print("Enter your Docket Alarm username (your email) and password.")
        username = input("Username: ")
        password = input("Password: ")
        
    do_getdocket, do_search, do_track_test = True, True, False
    # do_getdocket, do_search, do_track_test = False, False, True
    
    ########
    print_title("Login")
    out = call_api("login", msg=
        "First, we'll try logging in with your username and password", 
        post_args = {'username':username, 'password':password})
    login_token = out['login_token']
    bad_court, bad_docket = 'Court of Nowhere district', '123-cv-01234'
    real_court, real_docket = 'Delaware District Court', '1:11-cv-00797'
    
    # ########
    if do_search:
        print_title("Searching for Cases")
        out = call_api("searchpacer", msg= "Now we'll search PACER for all cases in New York where Sony is a party.",
                get_args = {'login_token': login_token, "client_matter":'',
                        'party_name':"Sony", 'court_region' : "New York"})
        out = call_api("searchpacer", msg= "There were several pages returned in the previous call. Get the fourth.",
                get_args =  {'login_token': login_token, "client_matter":'',
                'party_name':"Sony", 'court_region' : "New York", 'page':4})
        
        out = call_api("searchpacer", msg= "Search PACER for all Sony cases with nature of suit codes 810 or 220.",
                    get_args={'login_token': login_token, "client_matter":'',
                            'party_name':"Sony", 'nature_of_suit' : [810, 220]})

        out = call_api("searchpacer", msg= "Search for docket number 2010-cr-00188 in any court.",
                    get_args={'login_token': login_token, "client_matter":'',
                            'docket_num':"2010-cr-00188"})

        out = call_api("searchpacer", msg= "Now search for a docket number in a bad format (20-ab-00188).",
                    get_args={'login_token': login_token, "client_matter":'',
                        'docket_num':"20-ab-00188"}, error_expected=True)

    # ########
    if do_getdocket:
        print_title("Getting a Cached Docket")
        out = call_api("getdocket", msg="Get the court docket for 4:2010-cr-00188, Arkansas Eastern District Court",
                 get_args = {'login_token': login_token, "client_matter":'',
            'court':"Arkansas Eastern District Court",
            'docket':'4:2010-cr-00188',
            'cached':True})
        
        print_title("Getting a Full Docket")
        out = call_api("getdocket", msg="Get the court docket for 4:2010-cr-00188, Arkansas Eastern District Court",
                 get_args = {'login_token': login_token, "client_matter":'',
            'court':"Arkansas Eastern District Court",
            'docket':'4:2010-cr-00188'})
    
    # ########
    
    print_title("Tracking Cases")
    print("Now we'll show you how to get automatic email updates whenever "\
            "there is a new entry to a court docket.")
    if do_track_test:
        out = call_api("track", msg="Test the API push call.",
                post_args =  {'login_token': login_token, 'test':'true'})
            
    out = call_api("track", msg="Set up weekly tracking for %s, %s."%(
                    real_docket, real_court),
                post_args =  {'login_token': login_token, 'client_matter':'foo',
            'docket':real_docket, 'court':real_court,
            'enable':True, 'frequency':'weekly'})
    
    out = call_api("track", msg="Now we'll try getting that same docket's "\
                    "tracking status. ", get_args = {'login_token':login_token,
                    'docket':real_docket, 'court':real_court})
    out = call_api("track", msg="Change it to daily updates.", post_args = 
            {'login_token': login_token, 'client_matter':'foo',
            'docket':real_docket, 'court':real_court,
            'enable':True, 'frequency':'twice_daily'})
    out = call_api("track", msg="Disable tracking altogether.", post_args = 
            {'login_token': login_token, 'client_matter':'foo',
            'docket':real_docket, 'court':real_court,
            'enable':False})
    out = call_api("track", msg="Lets get its status again.", 
            get_args = {'login_token':login_token, 
                'docket':real_docket, 'court':real_court})
            
    out = call_api("track", msg="Now we'll see what happens when something "\
        "goes wrong. We'll try querying the tracking status of a "\
            "docket that does not exist (%s %s)"%(bad_docket, bad_court), 
            get_args = {'login_token': login_token,  'docket':bad_docket, 
                        'court':bad_court}, error_expected=True)
    
    out = call_api("track", msg="And now we'll try tracking a docket that "\
                        "does not exist (%s %s)"%(bad_docket, bad_court), 
                    post_args =  {'login_token': login_token, 
                        'client_matter':'foo', 
                        'docket':bad_docket, 'court':bad_court, 
                        'enable':True, 'frequency':'weekly'}, 
                    error_expected=True)
    
    ########
    # Get Documents
    if False:
        print_title("Getting a Document")
        out = call_api("getdocket", post_args = 
            {'login_token': login_token, "client_matter":'test ' + 'api',
            'page_token':out['pages'][2]['page_token']})
    