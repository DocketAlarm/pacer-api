import pprint
import base64
import urllib
import urllib2
import json
import shelve
__version__ = '1.1'
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
DEBUG = True					# View additional debug information
TESTING = False					# Automatically turn on testing for all calls.
_INTERNAL_TESTING = False		# Used internally
USE_LOCAL = False				# For internal development purposes only

# Helpful for command line interaction
PRESS_KEY_BEFORE_CALL = False	# Wait for input before making url fetch
PRESS_KEY_AFTER_CALL = False	# Wait for input before going to the next step

SEARCH_RESULTS_AT_ONCE = 50		# Results per call when searching in parallel.
TIMEOUT = 120

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

	username, password = None, None
	if call not in ['login', 'subaccount']:
		if 'username' in kwargs:
			username = kwargs['username']
			del kwargs['username']
		if 'password' in kwargs:
			password = kwargs['password']
			del kwargs['password']
		if username and password and kwargs.get('login_token'):
			kwargs['login_token'] = ''

	# Sort the keywords so they are applied consistently.
	sorted_kw = sorted(kwargs.items(), key = lambda val: val[0])
	urlargs = urllib.urlencode(sorted_kw, doseq=True)

	if method == "GET":
		url = url + "?" + urlargs

	# Allow for debug printing
	if DEBUG:
		print("%s: %s"%(method, url))
		if method == "POST":
			print("ARGUMENTS: %s"%pprint.pformat(urlargs))
		
	# Add an authorization header if provided.
	req = urllib2.Request(url)
	if username and password:
		auth = base64.encodestring('%s:%s' % (username, password)).strip()
		req.add_header("Authorization", "Basic %s" % auth)

	# Make the call
	if _INTERNAL_TESTING:
		out = _INTERNAL_TESTING(method, url, urlargs)
	elif method == "GET":
		out = urllib2.urlopen(req, timeout = TIMEOUT).read()
	else:
		out = urllib2.urlopen(req, urlargs, timeout = TIMEOUT).read()

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
				logging.error("Problem accessing %s, %s: %s", court, docket, e)
				token = None
				tries += 1
				result = {'success' : False, 'error':str(e)}
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
						save_progress = None, async = False):
	'''
	Download a list of dockets in parallel by launching many processes.
	
	docket_list:		A list of (court, docket) tuples
	num_workers:		How many parallel processes to start
	cached:				Get cached dockets instead of fresh ones from the court
	save_progress		Use a temporary file to save work in case we crash.
	async               If True, we get data asyncrhonously.
	'''
	if save_progress != None:
		if async:
			raise NotImplementedError("Cannot save progress and async.")
		save_progress = shelve.open(save_progress, 'c')
	
	def get_key(court, docket):
		return ("(%s),(%s)"%(court, docket)).encode('ascii', 'ignore')
	
	dockets = []
	def deb(msg, *args, **kwargs):
		msg = "getdocket_parallel %s-%s: %s"%(username, client_matter, msg)
		logging.info(msg, *args, **kwargs)

	# Put all of the tuples into a processing queue
	dlqueue = ProcessQueue()
	for c_vals in docket_list:
		c_vals = list(c_vals)
		if len(c_vals) < 2:
			raise Exception("Expecting a list of at least two with court, "
			                "docket, instead got: %s", c_vals)
		court, docket = c_vals[:2]
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

	def iterator(sleep_time = 1.0):
		'''An iterator that goes through all of the given dockets.'''
		# Continue until the processing queue is empty
		got, iters, total = 0, 0, len(docket_list)
		while True:
			# It takes about 15 seconds to download a docket, so wait that long.
			iters += 1
			try:
				time.sleep(sleep_time)
				# get_nowait will have raise Empty and break the loop
				while True:
					yield docketqueue.get_nowait()
					got += 1
			except Empty:
				left = total - got
				if left <= 0:
					deb("Finished iterating %s"%total)
					break
				if iters % 5 == 0:
					deb("Did %d/%d, %d left.", got, total, left)
				continue
			except KeyboardInterrupt as e:
				deb("Main thread interrupt: %s" % e)
				break
			except Exception as e:
				deb("Main thread loop exception: %s" % e)
				break

		dlqueue.close()
		docketqueue.close()
		pool.close()
		pool.terminate()

	if async:
		return iterator

	for new_i, new_docket in enumerate(iterator()):
		dockets.append(new_docket)
		# Only save if succesful
		if save_progress != None and new_docket['result']['success']:
			# Save our progress
			k = get_key(new_docket['court'], new_docket['docket'])
			save_progress[k] = new_docket
		elif save_progress != None and new_i % 20 ==0:
			deb("sync dbase len=%d, added=%d ", len(save_progress), got)
			save_progress.sync()

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
							offset = offset, limit = limit, o = 'date_filed',
							login_token = token, client_matter = client_matter)
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
	if 'search_results' not in first_page:
		raise Exception("Could not find search results: %s"%first_page)
	
	num_first_page = len(first_page['search_results'])
	
	num_results = first_page['count']
	# The main thread removes them from searchqueue and puts them into a list.
	results = [None]*num_results
	results[:num_first_page] = first_page['search_results']
	logging.info("Downloading %s Results, already got first %d"%(
		num_results, num_first_page))
	
	# Put all of the search ranges into the result queue
	dlqueue = ProcessQueue()
	for i in xrange(num_first_page, num_results, SEARCH_RESULTS_AT_ONCE):
		limit = min(num_results, i+SEARCH_RESULTS_AT_ONCE) - i
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
	
