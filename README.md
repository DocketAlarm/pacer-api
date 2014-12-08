docketalarm-api
===============

Python API Client for the Docket Alarm Legal Database (www.docketalarm.com)

This library guides you through some of the capabilities of the Docket Alarm 
API. It will show you how to search and download docket information and how to
read the output.

## Docket Alarm's Court Coverage
[Docket Alarm is a legal research website](www.docketalarm.com) that provides
access to a number of different United States courts:

* All Federal District Courts
* All Federal Appellate Level Courts (i.e., the Circuit Courts)
* All Bankruptcy Courts
* The International Trade Commission (the ITC)
* The Patent Trial and Appeal Board (PTAB)

Each court listed above has a different scope.

Docket Alarm provides to all of the documents in its database through an 
API. However, at the moment, the only courts that are currently officially 
supported are the first three items listed above: Federal District Courts,
Appellate courts, and Bankruptcy courts.  All of the [supported courts use 
PACER](https://www.docketalarm.com/blog/2014/6/2/The-New-Resource-for-All-Things-PACER/), 
so you could consider Docket Alarm to be a PACER API.

## Cost and Pricing
This API client code is free to download and run under the Apache license. 
However, to actually use it, you will need a Docket Alarm account, which is not
free.  Unfortunately, the U.S. court system's docketing system, PACER charges 
access to all documents.  As a result, Docket Alarm must pass on those charges 
in the form of user fees.

However, for development purposes, Docket Alarm provides a free test mode. This
test mode allows you to see exactly what comes back from the API, but returns
only fake test data.

## Getting Started
### Prerequisites
* You will need a Docket Alarm user name and password. If you do not have one,
[you can sign up at Docket Alarm](https://www.docketalarm.com). You will need 
to either enter your credit card information.
* A few pieces of software:
 * A text editor (such as notepad++)
 * The python runtime
 * git

### Downloading Source and Running the Test Program
Run the following commands to download the python client api and run an api 
test program:

1. `git clone https://github.com/speedplane/docketalarm-api.git`
2. `cd docketalarm-api`
3. `python api_test.py`

Once you run the program above, you will be greeted with a number of prompts 
asking you to log into the Docket Alarm and will be guided through a number of
operations.

## Learning More
The first thing to do to learn more about the api is to take a look at the 
official documentation located at: https://www.docketalarm.com/api/v1/

Another great way to learn about the API is to explore the code in this 
repository:

* **`api\client.py`**: This is the true python api client, which provides a 
 function called `api.call` that provides full access to Docket Alarm's API.
* **`api_test.py`**: This is a small test program that uses `client.py` to log 
 into Docket Alarm, search for a few documents, and download a docket.  If you
 are creating your own python program, one way to start would be to edit this
 program.