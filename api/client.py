import pprint
import json
import urllib
import urllib2
import json
'''
Docket Alarm Python API Client


Example Usage:
    token = call_api("login", "POST", username="user@example.com", 
                                        password="pass")
    token = token['login_token']
    result = call_api("searchpacer", "GET", login_token=token, 
                        client_matter='new search', party_name="Microsoft",
                        nature_of_suit="830")
'''

################################################################################
# Global API Setings

api = "/api/v1/"
DEBUG = True                    # View additional debug information
TESTING = False                 # Automatically turn on testing for all calls.

# Helpful for command line interaction
PRESS_KEY_BEFORE_CALL = False   # Wait for input before making url fetch
PRESS_KEY_AFTER_CALL = False    # Wait for input before going to the next step

USE_LOCAL = False				 # For internal development purposes only

################################################################################
# The Main API call
def call(call, method="GET", **kwargs):
    if method not in ["GET", "POST"]:
        raise Exception("Expecting a GET or POST request, not: %s"%method)
    
    
    if PRESS_KEY_BEFORE_CALL:
        raw_input("(press enter to continue)")
    
    # Prepare the URL and arguments
    if USE_LOCAL:
        base_url = "http://localhost:8000"
    else:
        base_url = "https://www.docketalarm.com"
    url = base_url + api + call + "/"
    if TESTING:
        urlargs['test'] = True
    urlargs = urllib.urlencode(kwargs, doseq=True)
    if method == "GET":
        url = url + "?" + urlargs
    
    # Allow for debug printing
    if DEBUG:
        print("%s: %s"%(method, url))
        if method == "POST":
            print("ARGUMENTS: %s"%pprint.pformat(urlargs))
        
    # Make the call
    if method == "GET":
        response = urllib.urlopen(url)
    else:
        response = urllib.urlopen(url, urlargs)
    
    out = response.read()
    
    try:
        out = json.loads(out)
    except:
        raise Exception("Not JSON: " + out)    
    
    if DEBUG and out and out.get('error'):
        print "Error: %s"%out['error']
    
    if PRESS_KEY_AFTER_CALL:
        raw_input("API Call Complete (press enter to continue)")
        print("")
    
    return out

	
################################################################################
#		Utilities and Time Saving Helper Functions
import time, logging
from Queue import Empty
from multiprocessing import Process
from multiprocessing import Pool as MultiProcessPool
from multiprocessing import Semaphore as ProcessSemaphore
from multiprocessing import Queue as ProcessQueue

def _dl_worker(username, password, client_matter, dlqueue, docketqueue):
	'''
	A Download worker used by get_dockets to download dockets in parallel
	'''
	# Generic login function
	login = lambda: call(call="login", method="POST", 
				username=username, password=password)['login_token']
	
	token, tries = None, 0
	while True:
		try:
			court, docket = dlqueue.get_nowait()
		except Empty:
			logging.info("Download Queue Done.")
			return
		except (KeyboardInterrupt, Exception) as e:
			logging.info("Worker exception: %s"%e)
			return
		# Retry handler
		for i in range(0, 2):
			# Try logging in every so often
			if not token or tries % 25 == 0:
				token = login()
			result = call(call="getdocket", method="GET", 
							court=court, docket=docket,login_token=token,
							client_matter=client_matter)
			tries += 1
			if result and not result.get('success'):
				continue
			break
		# Save the results
		docketqueue.put({
			'court':court,
			'docket':docket,
			'result':result,
		})
	
def getdocket_parallel(username, password, client_matter, docket_list, 
						num_workers = 15):
	'''
	Download a list of dockets in parallel by launching many processes.
	
	docket_list:		A list of (court, docket) tuples
	num_workers:		How many parallel processes to start
	'''
	# Put all of the tuples into a processing queue
	dlqueue = ProcessQueue()
	for court, docket in docket_list:
		dlqueue.put((court, docket))
	
	# The processes will put their results into the docketqueue
	docketqueue = ProcessQueue()
	# The main thread removes them from docketqueue and puts them into a list.
	dockets = []
	
	# Start up the parallel processes
	pool = MultiProcessPool(processes=num_workers, initializer=_dl_worker, 
				initargs=[username, password, client_matter,
							dlqueue, docketqueue])
	
	try:
		# Continue until the processing queue is empty
		while not dlqueue.empty():
			# It takes about 15 seconds to download a docket, so wait that long.
			time.sleep(13.0 / num_workers)
			got = 0
			while True:
				try:
					dockets.append(docketqueue.get_nowait())
					got += 1
				except Empty:
					logging.info("Got %d, %d total dockets. Waiting again."%(
							got, len(dockets)))
					break
				except Exception as e:
					logging.info("Main thread loop exception: %s"%e)
					break
				
	except KeyboardInterrupt as e:
		logging.info("Main thread exception: %s"%e)
		dlqueue.close()
		docketqueue.close()
		pool.close()
		pool.terminate()
		# Return what we have even if there was an exception.
		return dockets
	return dockets