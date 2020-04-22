#
# Developer: David Ryder, David.Ryder@AppDynamics.com
# Hacked up by: Bill Harper
#
# Executes a GET request to a URL and posts metrics to a custom
# schema in the AppDynamics Analytics Events Service using the
# Analytics Events API https://analytics.api.appdynamics.com
# Metrics posted include response_time and status_code from the GET request
#
# Runs from the command line only after harper modes for IPP partners
#
# Command line options: runtest1, createCustomSchema, deleteSchema
#
# Also installed the python agent so each api call can be seen in a flow map
#
import os
import sys
import requests
import datetime
import random
import json
#
import time
#
# Import the AppDynamics agent api's
#
from appdynamics.agent import api as appd
#################################################################
# Initiaize the AppDynamics Python agent api's so we can use them
#################################################################
def appdSetup():
    print("Lets setup the AppD agent ...\n\n")
    appd.init()
#############################################################
# Create the header to call the AppDynamics Analytics api's
#############################################################
def createHeaders( auth ):
    return { "X-Events-API-AccountName": auth['globalAccountName'],
             "X-Events-API-Key": auth['analyticsKey'],
             "Content-type": "application/vnd.appd.events+json;v=2"}

exampleSchema = { "schema": { "testid":           "integer",
                              "status_code":      "integer",
                              "status_code_s":    "string",
                              "response_time":    "integer",
                              "url":              "string",
                              "mesid":            "string" } }
############################################################
# Create a custom Schema in the AppD Analytics DB
############################################################
def createCustomSchema( schema=exampleSchema, auth=[] ):
    print (auth['endPoint']) 
    print (auth['schemaName'])
    url =  auth['endPoint'] + "/events/schema/" + auth['schemaName']
    print( "createCustomSchema ", auth, createHeaders( auth ), url)
    r = requests.post( url,
                       data=json.dumps( schema ),
                       headers=createHeaders( auth ) )
    print( "Post create Schema ", r.status_code, r.text )
#    print( "Post metrics ", r.status_code )
#
############################################################
# Delete a Schema from the AppD Analytics DB
############################################################

def deleteCustomSchema( auth ):
    r = requests.delete( auth['endPoint'] + "/events/schema/" + auth['schemaName'], headers=createHeaders( auth ) )

############################################################
# This is where we send the data to the Analytics api ...
############################################################

def postCustomAnalytics( auth, data ):
#    print( "Posting ", auth, data )
# Changing this line to mute the login info that was being printed to the console
#
    print( "Posting results AppD Analytics URL-> ", auth['endPoint'] )
    r = requests.post( auth['endPoint'] + "/events/publish/" + auth['schemaName'],
                       data=json.dumps( data ),
                       headers=createHeaders( auth ))
    #print( "Schema-> ", auth['schemaName'],r.status_code)
    print( "Writing to Analytics Schema-> ", auth['schemaName'])
    print( "With Data-> ", data)
    print("................................................................................")
    if r.status_code != 200:
        print( r.text )
        print( auth )
##################################################################
# This is where you can query the API, but I have not test this  
#################################################################

def postQuery( auth ):
    query = "select * from {schemaName}".format(schemaName=auth['schemaName'])
    r = requests.post( auth['endPoint'] + "/events/query",
                       data=query,
                       headers=createHeaders( auth ))
    print( "postQuery ", r.status_code, auth['schemaName'] )
    if r.status_code == 200:
        print( r.text )
###################################################################
# This is where you query for custom analytics Metrics
###################################################################

def queryCustomAnalyticsMetric( auth ):
        metricPath = "Analytics|TEST1_COUNT"
        applicationName = "AppDynamics Analytics-2" # From Analytics Metric Browser
        params = { 'metric-path': metricPath, # From Analytics Metric Browser
                   'time-range-type': 'BEFORE_NOW',
                   'duration-in-mins': '10080', # 60 * 24 * 7
                   'rollup': 'true', # false for individual values
                   'output': 'JSON'
                   }
        r = requests.get("http://{controllerHost}:{controllerPort}/controller/rest/applications/{applicationName}/metric-data".format(
                            controllerHost=auth['controllerHost'],controllerPort=auth['controllerPort'],applicationName=applicationName),
                         auth=("{0}@{1}".format(auth['controllerAdminUser'],auth['controllerAccount']),"{0}".format( auth['controllerPwd'] )),
                         params=params)
        if r.status_code == 200:
            print('200 status')
            print( r.text )

####################################################################
# This is where we get the URL to test its response time for query
####################################################################

def getRequestURL( testUrl ):
    status_code = 0
    startTime = datetime.datetime.now()
    appd.bt("Getting URL metrics")
    try:
        r = requests.get( testUrl )
        statusCode = r.status_code
    except Exception as e:
        print( "E ", e )
        statusCode = 503 # 503 Service Unavailable
    responseTime = int((datetime.datetime.now() - startTime).total_seconds() * 1000)
    print( "Testing URL-> ", testUrl, statusCode )
    return int( statusCode ), responseTime, testUrl

################################################################
# runTestCase1 is where we do most of the work in this program
# and the first call to get the program going
################################################################

def runTestCase1( auth, testURL ):
    statusCode, responseTime, testedUrl = getRequestURL( testURL )
    data = [ {  "testid":           random.randint( 1, 1000 ),
                "status_code":      statusCode,
                "status_code_s":    str( statusCode ),
                "response_time":    responseTime,
                "url":              testedUrl,
                "mesid":            get_measurement_id() } ]
#
# Call this routine to post the data
#
    postCustomAnalytics( auth, data )
#
# List of URL endpoints to test GET request against, including a few bogus 
# end points so we can generat errors. 
#
urlList = [  "https://google.com",
             "https://yahoo.com",
             "https://www.amazon.com",
             "https://appdynamics.com",
             "https://www.cisco.com",
             "https://www.sun.com",
             "https://yahoo.com/testerror",
             "https://google.com/TESTERROR" ]
print( "Running as script")
print( "Loading up URL test list in memory")
#print( urlList)
#
# Source authentication credentials from environment variables
# cound not make the env method work, harding coding at temp workaround
#
print( "Setting up Authenicating to AppDynamics Analytics API")
#
auth = { "endPoint":            'https://analytics.api.appdynamics.com:443',
         "globalAccountName":   'xxxxxd',
         "analyticsKey":        'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx',
         "controllerHost":      'https://demo.saas.appdynamics.com',
         "controllerPort":      '443',
         "controllerAdminUser": 'user.name',
         "controllerAccount":   'xxxxxxx',
         "controllerPwd":       'xxxxxxxxx',
         "schemaName":          'schemaA' }
#    print(auth)
#    print(os.environ.get('APPDYNAMICS_EVENTS_SERVICE_ENDPOINT'))

def get_measurement_id():
        return "U"

cmd = sys.argv[1] if len(sys.argv) > 1 else "unknown command"
if cmd == "runtest1": # runtest1 <schema name>
#        auth['schemaName'] = sys.argv[2]
#        print( "AUTH ", auth )
    print( "cmd=runtest1")
    runTestCase1( auth, random.choice(urlList) )

elif cmd == "createSchema": # createSchema <schema name>
    auth['schemaName'] = sys.argv[2]
    print (sys.argv[2])
    print (auth['schemaName'])
    createCustomSchema(auth=auth)

elif cmd == "deleteSchema": # deleteSchema <schema name>
    auth['schemaName'] = sys.argv[2]
    deleteCustomSchema(auth=auth)
#
elif cmd == "query1": # createSchema <schema name>
    auth['schemaName'] = sys.argv[2]
    postQuery(auth=auth)

elif cmd == "query2": # createSchema <schema name>
    auth['schemaName'] = sys.argv[2]
    queryCustomAnalyticsMetric(auth=auth)

else:
    print( "Commands: runtest1, createSchema, deleteSchema")

# Main Program Starts here    
print( "main runTestCase1")    
#runTestCase1( auth, random.choice(urlList) )
appdSetup()
while (True):
    with appd.bt('Sending data to Analytics API'):
        runTestCase1( auth, random.choice(urlList) ) 
    time.sleep(1)

