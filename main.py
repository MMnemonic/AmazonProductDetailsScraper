import os
import sys
import datetime
from flask import Flask, request, redirect, url_for, send_from_directory, jsonify
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
import socket
import logging
import requests,time,re,cgi,cgitb
import csv
from bs4 import BeautifulSoup
import datetime
from html.parser import HTMLParser
import random
from collections import OrderedDict 
 
app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

 

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def debugPrint(exception):
    if isinstance(exception, SCRError):
        errorString = "SCR_ERROR: (" + str(exception.errorCode) + "): " + str(exception.internalErrorMessage)
    else:
        errorString = "SCR_ERROR: " + str(exception)

    eprint(errorString)
    errorLogPath = os.path.abspath(os.path.join(os.path.dirname(__file__), 'errors.log'))
    errorString = str(datetime.datetime.now()) + ": " + errorString
    with open(errorLogPath, "a") as errorLog:
        print(errorString, file=errorLog)


# Convenience methods for checking the HTTP request type
def get():
	if request.method == 'GET':
		return True
	return False

def post():
	if request.method == 'POST':
		return True
	return False

def put():
	if request.method == 'PUT':
		return True
	return False

def delete():
	if request.method == 'DELETE':
		return True
	return False



def valueForParam(param, default=None, nullable=True, isList=False):
	if request.method == 'GET':
		if isList:
			value = request.args.getlist(param, default)
		else:
			value = request.args.get(param, default)
	else:
		if isList:
			value = request.form.getlist(param, default)
		else:
			value = request.form.get(param, default)

	if value == "" or not value:
		value = None

	if not nullable and value is None:
		raise SCRError(errorCode=418029, internalErrorMessage="Required parameter '{}' is missing.".format(param))

	return value




class SCRError(Exception):
    def __init__(self, errorCode=-1, externalErrorMessage=None, internalErrorMessage=None, statusCode=500):
        self.errorCode = str(errorCode) if errorCode else None
        self.externalErrorMessage = externalErrorMessage
        self.internalErrorMessage = internalErrorMessage if internalErrorMessage else externalErrorMessage
        self.statusCode = statusCode
        self.jsonRepresentation = {"errorCode": self.errorCode, "externalErrorMessage": self.externalErrorMessage, "internalErrorMessage": self.internalErrorMessage}


class Stripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = Stripper()
    s.feed(html)        
    return s.get_data()
 
def isConnected():
    try:
        host = socket.gethostbyname("www.google.co.in")
        s = socket.create_connection((host, 80), 3)
        return True
    except:
        pass
    return False


def scrape(asin):
    base = 30
    avg = random.uniform(0.2,10.3)
    url = "http://www.amazon.in/dp/"+str(asin)
    header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36'}
    #header = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
    page = requests.get(url, headers=header);
    if page.status_code == 404:
        msg = "Please enter a valid asin"
        return msg
    else:
        soup = BeautifulSoup(page.content,"lxml")
        pTitle = soup.find(id='productTitle')
        while pTitle == None:
            page = requests.get(url, headers=header);
            time.sleep(base-avg)
            soup = BeautifulSoup(page.content,"lxml")
            pTitle = soup.find(id='productTitle')
        line = soup.find(id='priceblock_ourprice')
        if line is None:
            line = soup.find(id='priceblock_saleprice')
            if line is None:
                line = soup.find(id='priceblock_dealprice')
        price = strip_tags(str(line))
        price = ' '.join(price.split())
        pTitle = strip_tags(str(pTitle)) 
        pTitle = ' '.join(pTitle.split())
        fBullets = soup.find(id='feature-bullets')
        fBullets = strip_tags(str(fBullets))
        fBullets = "".join(fBullets.split('\t'))
        fBullets = (fBullets.split('\n'))
        finalBullets = []
        for elem in fBullets:
            finalBullets.append(str(elem.encode("UTF-8")).replace("b'", "").replace("'b","").replace("'",""))
            finalBullets[:] = [item for item in finalBullets if item != '' if item != ' ' if item != '\x9b' if item != 'See more product details' if item != '\xae' if item != '\xa0' if item != u'']
        pDesc = soup.find(id='productDescription')
        pDesc = strip_tags(str(pDesc))
        pDesc = ' '.join(pDesc.split()) 
        csvDict =  OrderedDict()
        csvDict['ASIN'] = str(asin)
        csvDict['Title'] = str(pTitle)
        csvDict['Price'] = str(price)
        csvDict['Bullets'] = finalBullets
        csvDict['Description'] = str(pDesc)
        return (csvDict) 


@app.route('/search', methods=['GET'])
@cross_origin()
def search_price():
    if get():
        asin = valueForParam('asin', nullable=False) 
        return jsonify(scrape(asin))


@app.route('/')
def index():
    return jsonify("Hello, World!")

@app.errorhandler(Exception)
def handleError(error):
    debugPrint(error)
    if not isinstance(error, SCRError):
        error = SCRError(errorCode=-1000, internalErrorMessage=str(error))
    return jsonify(error.jsonRepresentation), error.statusCode

 
 
if __name__ == "__main__":
    app.run(debug=True)
