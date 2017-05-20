docketalarm-api / pacer-api
===============

[Docket Alarm is a legal research system](www.docketalarm.com) that provides
access to the United States court system. This Python API client provides 
access to all legal filings in Docket Alarm's database across the 
United States.

## Docket Alarm's Court Coverage
As of May 2017, Docket Alarm covers the following jurisdictions:

* Federal Courts / PACER cases (District Courts, Bankruptcies, Appellate, MDL)
* U.S. Supreme Court
* The International Trade Commission (the ITC)
* The Patent Trial and Appeal Board (PTAB)
* The Trademark Trial and Appeal Board (TTAB)
* Trademark Prosecution History at the USPTO
* Orange Book Filings and Related Correspondence with the FDA
* State courts including California, Texas, Florida and New York.

A complete list of [courts is maintained on the Docket Alarm 
website](https://www.docketalarm.com/courts). If a court you are looking for
is not on this list, let us know at admin@docketalarm.com, we're always adding 
more.

Docket Alarm provides access to all of the above courts. Because Docket Alarm's
API is [often used to download court cases from PACER](https://www.docketalarm.com/blog/2014/6/2/The-New-Resource-for-All-Things-PACER/), 
Docket Alarm serves as a PACER API. Note however, that while 
Docket Alarm does provide an API to PACER, it also provides an API to many other 
court systems as well.

## Cost and Pricing
This API client is freely licensed under the Apache license. However to use it, 
you will need a Docket Alarm account, which is not free.  Unfortunately, the 
U.S. court's docketing system, PACER charges access to all documents.  As a 
result, Docket Alarm must pass on those charges in the form of user fees.

### Saving Money on Court Fees
Every time Docket Alarm downloads a document from the court, it saves a copy
of that document. If another user then attempts to access that document, rather
than going to the court a second time, Docket Alarm returns its saved copy.
This allows users to reduce their court fees because we do not pay a fee for 
the same document twice.

### Test Mode
For development purposes, Docket Alarm provides a free test mode. This test 
mode allows you to see exactly what comes back from the API, but returns fake 
test data.

## Getting Started
You will need a functioning Docket Alarm account. If you do not have one,
[you can sign up at Docket Alarm](https://www.docketalarm.com) and enter a 
user name and password. You will need to enter your credit card information.

### Downloading Source and Running the Test Program
Run the following commands to download the python client API and run the API
test program:

1. `git clone https://github.com/speedplane/docketalarm-api.git`
2. `cd docketalarm-api`
3. `python api_test.py`

The test program greets you with a number of prompts and instructs you on how
to perform API calls to Docket Alarm and how to process the responses. It is
a great way to get started with the API and learn about its functionality.

## Learning More
To learn more about the API take a look at the official Docket Alarm API 
 documentation at: https://www.docketalarm.com/api/v1/

You can also explore the API by reviewing the code in this repository:

* **`api\client.py`**: This is the python API client. It has a function called 
 `api.call` that provides access to Docket Alarm's RESTful API.
* **`api_test.py`**: This is a small test program that uses `client.py`. It will
 log into Docket Alarm, search for a few documents, and download a docket.  If
 you are creating your own python program, one way to start would be to edit 
 this program.
 
## Help and Support
Because Docket Alarm is a commercial SaaS product, it is fully supported. To
get help with this python client or the Docket Alarm API in general, contact
admin@docketalarm.com. 