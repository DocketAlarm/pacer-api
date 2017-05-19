import pprint
import json
import urllib
import urllib2
import json
import shelve
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
_INTERNAL_TESTING = False		# Used internally

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
        base_url = "http://localhost:8080"
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
	if _INTERNAL_TESTING:
		out = _INTERNAL_TESTING(method, url, urlargs)
	else:
		response = urllib.urlopen(url) if method == "GET" else \
			urllib.urlopen(url, urlargs)
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
from multiprocessing import Queue as ProcessQueue

def _dl_worker(username, password, client_matter, cached, dlqueue, docketqueue):
	'''
	A Download worker used by get_dockets to download dockets in parallel.
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
			try:
				if not token or tries % 25 == 0:
					token = login()
				result = call(call="getdocket", method="GET", 
								court=court, docket=docket,login_token=token,
								client_matter=client_matter, cached=cached)
			except Exception as e:
				logging.error("Problem downloading: %s"%e)
				token = None
				tries += 1
				continue
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
						cached = False, num_workers = 15,
						save_progress = None):
	'''
	Download a list of dockets in parallel by launching many processes.
	
	docket_list:		A list of (court, docket) tuples
	num_workers:		How many parallel processes to start
	cached:				Get cached dockets instead of fresh ones from the court
	save_progress		Use a temporary file to save work in case we crash.
	'''
	if save_progress != None:
		save_progress = shelve.open(save_progress, 'c')
	
	def get_key(court, docket):
		return ("(%s),(%s)"%(court, docket)).encode('ascii', 'ignore')
	
	dockets = []
	
	# Put all of the tuples into a processing queue
	dlqueue = ProcessQueue()
	for court, docket in docket_list:
		k = get_key(court, docket)
		if save_progress != None and save_progress.get(k) and \
				save_progress[k]['result']['success']:
			# Add to the results
			dockets.append(save_progress[k])
		else:
			# Add it to the download queue
			dlqueue.put((court, docket))
	
	# The processes will put their results into the docketqueue
	docketqueue = ProcessQueue()
	# The main thread removes them from docketqueue and puts them into a list.
	
	# Start up the parallel processes
	pool = MultiProcessPool(processes=num_workers, initializer=_dl_worker, 
				initargs=[username, password, client_matter,
							cached, dlqueue, docketqueue])
	
	try:
		# Continue until the processing queue is empty
		got = 0
		while True:
			# It takes about 15 seconds to download a docket, so wait that long.
			time.sleep(1.0)
			try:
				# get_nowait will have raise Empty and break the loop
				while True:
					new_docket = docketqueue.get_nowait()
					dockets.append(new_docket)	
					# Only save if succesful
					if save_progress != None and new_docket['result']['success']:
						# Save our progress
						k = get_key(new_docket['court'], new_docket['docket'])
						save_progress[k] = new_docket
					got += 1
			except Empty:
				if save_progress != None:
					print "Syncing dbase (len=%d), dockets=%d "%(
						len(save_progress), len(dockets))
					save_progress.sync()
				left = len(docket_list) - len(dockets)
				if left <= 0:
					break
				logging.info("Got %d, %d total dockets. Waiting again."%(
						got, len(dockets)))
				continue
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
		
	if save_progress != None:
		save_progress.sync()
		save_progress.close()
	return dockets

################################
def _search_worker(username, password, client_matter, q, inqueue, searchqueue):
		# Generic login function
	login = lambda: call(call="login", method="POST", 
				username=username, password=password)['login_token']
	token, tries = None, 0
	while True:
		try:
			offset, limit = inqueue.get_nowait()
		except Empty:
			logging.info("Download Queue Done.")
			return
		except (KeyboardInterrupt, Exception) as e:
			logging.info("Worker exception: %s"%e)
			return
		# Retry handler
		for i in range(0, 2):
			# Try logging in every so often
			try:
				if not token or tries % 25 == 0:
					token = login()
				result = call(call="search", method="GET", q = q, 
							offset = offset, limit = limit,
							login_token=token, client_matter=client_matter)
			except Exception as e:
				logging.error("Could not search at %s, tries - %s: %s"%(
					offset, tries, e))
				tries += 1
				continue
			tries += 1
			if result and not result.get('success'):
				logging.warning("Problem getting results: %s"%result)
				token = None
				continue
			break
		# Save the results
		searchqueue.put({
			'offset' : offset,
			'limit' : limit,
			'result' : result,
		})
	

def search_parallel(username, password, client_matter, q, 
						num_workers = 15):
	'''
	Download a list of dockets in parallel by launching many processes.
	
	docket_list:		A list of (court, docket) tuples
	num_workers:		How many parallel processes to start
	'''
	login_token = call(call="login", method="POST", 
					username=username, password=password)['login_token']
	first_page = call(call="search", method="GET", q=q, 
		login_token=login_token, client_matter=client_matter)
	
	num_first_page = len(first_page['search_results'])
	
	num_results = first_page['count']
	# The main thread removes them from searchqueue and puts them into a list.
	results = [None]*num_results
	results[:num_first_page] = first_page['search_results']
	logging.info("Downloading %s Results, already got first %d"%(
		num_results, num_first_page))
	
	# Put all of the search ranges into the result queue
	dlqueue = ProcessQueue()
	NUM_AT_ONCE = 20
	for i in xrange(num_first_page, num_results, NUM_AT_ONCE):
		limit = min(num_results, i+NUM_AT_ONCE) - i
		logging.info("Added: %s --> %s"%(i, i+limit))
		dlqueue.put((i, limit))
	
	# The processes will put their results into the searchqueue
	searchqueue = ProcessQueue()
	# Start up the parallel processes
	pool = MultiProcessPool(processes=num_workers, initializer=_search_worker, 
				initargs=[username, password, client_matter, q,
							dlqueue, searchqueue])
	try:
		# Continue until the processing queue is empty.
		while True:
			# It takes about 15 seconds to download a docket, so wait that long.
			time.sleep(2.0 / num_workers)
			got = 0
			try:
				item = searchqueue.get_nowait()
				start, end = item['offset'], item['offset']+item['limit']
				results[start:end] = item['result']['search_results']
				logging.info("Downloaded: %s --> %s (of %d total)"%(
					start, end, num_results))
				got += 1
			except Empty:
				left = len(results) - len(filter(None, results))
				if left <= 0:
					break
				logging.info("Got %d, %d results. Waiting for %d more."%(
						got, len(results), left))
				continue
			except Exception as e:
				logging.info("Main thread loop exception: %s"%e)
				break
				
	except KeyboardInterrupt as e:
		logging.info("Main thread exception: %s"%e)
		dlqueue.close()
		searchqueue.close()
		pool.close()
		pool.terminate()
		# Return what we have even if there was an exception.
		return results
	
	for i, r in enumerate(results):
		if not r:
			print "Missing Result %s"%(i+1)
		
	
	return {
		'search_results' : results,
		'count'	: num_results,
	}
	
