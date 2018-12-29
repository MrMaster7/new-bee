import logging
import logging.handlers
import boto3
import json

from wsgiref.simple_server import make_server, WSGIServer
from SocketServer import ThreadingMixIn
from string import Template
from cgi import parse_qs, escape

# Create logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handler 
LOG_FILE = '/tmp/sample-app/sample-app.log'
handler = logging.handlers.RotatingFileHandler(LOG_FILE, maxBytes=1048576, backupCount=5)
handler.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Add Formatter to Handler
handler.setFormatter(formatter)

# add Handler to Logger
logger.addHandler(handler)

# Global variable
age_value = 0
 
def return_thing_shadow_json():
    client = boto3.client('iot-data')
    client_response = client.get_thing_shadow(thingName='IoTDevice_ESP8266')
    streamingBody = client_response["payload"]
    jsonMsg = json.loads(streamingBody.read())
    return jsonMsg

def application(environ, start_response):
    path    = environ['PATH_INFO']
    method  = environ['REQUEST_METHOD']
    request_body_size = 0
    
    html_filename = '/tmp/main.html'
    HtmlFile = open(html_filename, 'r')
    html_template = HtmlFile.read()
    print html_template
    response = html_template


    if method == 'POST':
        try:
	    
	    jsonState = return_thing_shadow_json()  
            print jsonState
            response = Template(response).safe_substitute(thing_shadow=jsonState['state']['reported']['open'])      
            if path == '/':
                request_body_size = int(environ['CONTENT_LENGTH'])
            elif path == '/scheduled':
                logger.info("Received task %s scheduled at %s", environ['HTTP_X_AWS_SQSD_TASKNAME'], environ['HTTP_X_AWS_SQSD_SCHEDULED_AT'])
        except (TypeError, ValueError):
            logger.warning('Error retrieving request body for async work.')
            request_body_size = 0
    #response = Template(html_template).safe_substitute(thing_shadow=jsonState['state']['reported']['open'])
    #response = Template(html_template).safe_substitute(thing_shadow=jsonState)
    
    # When the method is POST the variable will be sent in the HTTP request body which 
    # is passed by the WSGI server in the file like wsgi.input environment variable.
    request_body = environ['wsgi.input'].read(request_body_size)
    d = parse_qs(request_body)
    age = d.get('age', [''])[0] # Returns the first age value.
    hobbies = d.get('hobbies', []) # Returns a list of hobbies.
    # Always escape user input to avoid script injection
    age = escape(age)
    hobbies = [escape(hobby) for hobby in hobbies]
    print age
    print hobbies
    response = Template(response).safe_substitute(age_value=age)

    status = '200 OK'
    headers = [('Content-type', 'text/html')]

    start_response(status, headers)
    return [response]

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer): 
    pass

if __name__ == '__main__':  
    httpd = make_server('', 8000, application, ThreadingWSGIServer)

    print "Serving on port 8000..."
    httpd.serve_forever()
