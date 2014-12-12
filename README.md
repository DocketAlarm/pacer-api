docketalarm-api / pacer-api
===============

[Docket Alarm is a legal research site](www.docketalarm.com) that provides
access to the United States court system. This library is a Python API client 
to access the legal filings in Docket Alarm's database.

## Docket Alarm's Court Coverage
As of Dec. 2014, Docket Alarm covers the following jurisdictions:

* Federal District Courts
* Federal Appellate Level Courts (i.e., the Circuit Courts)
* Bankruptcy Courts
* The International Trade Commission (the ITC)
* The Patent Trial and Appeal Board (PTAB)

Docket Alarm provides access to all of the above courts through an API. 
Currently however, Docket Alarm only provides public access API access to 
courts on the PACER system, which covers Federal District, Appellate, and 
Bankruptcy courts. To access others, contact us at admin@docketalarm.com.

Because the [supported courts all use 
PACER](https://www.docketalarm.com/blog/2014/6/2/The-New-Resource-for-All-Things-PACER/), 
you could consider Docket Alarm to be a PACER API.

## Cost and Pricing
This API client code is free to download and run under the Apache license. 
However, to actually use it, you will need a Docket Alarm account, which is not
free.  Unfortunately, the U.S. court's docketing system, PACER charges access 
to all documents.  As a result, Docket Alarm must pass on those charges in the 
form of user fees.

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