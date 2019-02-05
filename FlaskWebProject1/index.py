from __future__ import print_function
#from future.standard_library import install_aliases
#install_aliases()

import requests
import time

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    # commented out by Naresh
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    #print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):
    print ("here I am....")
    print ("starting processRequest...",req.get("queryResult").get("action"))
    if req.get("queryResult").get("action") != "yahooWeatherForecast":
        print ("Please check your action name in DialogFlow...")
        return {}
    print("111111111111")
    baseurl = "https://query.yahooapis.com/v1/public/yql?"
    print("1.5 1.5 1.5")
    yql_query = makeYqlQuery(req)
    print ("2222222222")
    if yql_query is None:
        return {}
    yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
    print("3333333333")
    print (yql_url)
    result = urlopen(yql_url).read()
    data = json.loads(result)
    #for some the line above gives an error and hence decoding to utf-8 might help
    #data = json.loads(result.decode('utf-8'))
    print("44444444444")
    print (data)
    res = makeWebhookResult(data)
    return res


def makeYqlQuery(req):
    result = req.get("queryResult")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None
    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"


def makeWebhookResult(data):
    print ("starting makeWebhookResult...")
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Today the weather in " + location.get('city') + ": " + condition.get('text') + \
             ", And the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)
    #Naresh
    return {

    "fulfillmentText": speech,
     "source": "Yahoo Weather"
    }


@app.route('/test', methods=['GET'])
def test():
    return  "Hello there my friend !!"


@app.route('/static_reply', methods=['POST'])
def static_reply():
    speech = "Hello there, this reply is from the webhook !! "
    string = "You are awesome !!"
    Message ="this is the message"

    my_result =  {

    "fulfillmentText": string,
     "source": string
    }

    res = json.dumps(my_result, indent=4)

    r = make_response(res)

    r.headers['Content-Type'] = 'application/json'
    return r

@app.route('/snow_request', methods=['POST'])
def snow_request():
    req = request.get_json(silent=True, force=True)
    if req.get("queryResult").get("action") != "input.CreateIncidentSNOW":
        print ("Please check your action name in DialogFlow...")
        return {}
    
    shortdescription = req.get("queryResult").get("parameters").get("short_description")
    #print(shortdescription)    
    workitemID = addsnowqWI(shortdescription)
    #print(workitemID)
    getsnowqWI(workitemID)
    WIstatus = getsnowqWI.status
    #print(WIstatus)
    processreq = "We are creating your ticket now. Please wait."
    slackmsg(processreq)
    cnt = 0
    while WIstatus != "COMPLETED":
        time.sleep(15)
        getsnowqWI(workitemID)
        WIstatus = getsnowqWI.status
        processreq = "We are still creating you're ticket, please wait."
        if cnt == 2:
            slackmsg(processreq)
        if cnt > 2:
            cnt = 0
        #print("Queue status: " + WIstatus)
        #print(cnt)
        cnt = cnt + 1

    reply = "Processing your request"
          
    my_result = {
        "fulfillmentText": reply,
        "source": reply
        }

    res = json.dumps(my_result, indent=4)

    r = make_response(res)

    r.headers['Content-Type'] = 'application/json'
    processreq = "Ticket has been created."
    WIresult = getsnowqWI.result
    slackmsg(processreq)
    slackmsg(WIresult)
    return r

def CRauth():
    authurl = "http://localhost/v1/authentication"
    data = {"Username": "demo2","Password": "Nimsoft1234"}
    data_json = json.dumps(data)
    headers = {'Content-Type':'application/json'}
    response = requests.post(authurl, data=data_json, headers=headers)
    output = response.json()
    token = output['token']
    return token

def addsnowqWI(workitem): 
    token = CRauth()
    crqurl = "http://localhost/v1/wlm/queues/6/workitems"
    data = {"test":workitem}
    data_json = json.dumps(data)
    headers = {"Content-Type":"application/json","X-Authorization":token}
    response = requests.post(crqurl, data=data_json, headers=headers)
    output = response.json()
    id = output[0]['id']
    return id

def getsnowqWI(id):
    token = CRauth()
    crqurl = "http://localhost/v1/wlm/queues/6/workitems/list"
    data = {"sort":[],"filter":{"operator":"or","operands":[{ "field":"id", "operator": "eq", "value":id}]},"fields":[],"page":{"length": 200,"offset": 0}}
    data_json = json.dumps(data)
    headers = {"Content-Type":"application/json","X-Authorization":token}
    response = requests.post(crqurl, data=data_json, headers=headers)
    output = response.json()
    getsnowqWI.status = output['list'][0]['status']
    getsnowqWI.result = output['list'][0]['result']

def slackmsg(msg):
    slackhook = "https://hooks.slack.com/services/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"
    data = {"text": msg}
    data_json = json.dumps(data)
    headers = {'Content-Type':'application/json'}
    response = requests.post(slackhook, data=data_json, headers=headers)

def snowdirectpost(description):
    snowurl = "https://dev69254.service-now.com/api/now/v1/table/incident"
    data = {"short_description":shortdescription,"comments":"chatbot executing"}
    data_json = json.dumps(data)
    headers = {'Content-Type':'application/json','Authorization':'Basic YWRtaW46Tmltc29mdDEyMw=='}
    response = requests.post(snowurl, data=data_json, headers=headers)
    output = response.json()
    incinum = output['result']['number']
    outputreply = "You're incident number is "
    reply = outputreply+incinum
    return reply

if __name__ == '__main__':


    port = int(os.getenv('PORT', 5000))

    print("Starting app on port %d" % port)

    app.run(debug=True, port=port, host='0.0.0.0')
