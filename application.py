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
inc_value = 0 
age = 0
garage_door_toggle_input = ''

def return_thing_shadow_json():
    client = boto3.client('iot-data')
    client_response = client.get_thing_shadow(thingName='IoTDevice_ESP8266')
    streamingBody = client_response["payload"]
    jsonMsg = json.loads(streamingBody.read())
    return jsonMsg

def read_html_file():
    html_filename = '/tmp/main.html'
    HtmlFile = open(html_filename, 'r')
    html_template = HtmlFile.read()
    return html_template

html_template = read_html_file()

def application(environ, start_response):
    path    = environ['PATH_INFO']
    method  = environ['REQUEST_METHOD']
    request_body_size = 0
    response = html_template
    global inc_value
    global jsonState
    global age
    global garage_door_toggle_input
	
    inc_value += 1
    if method == 'POST':
        try:
            if path == '/':
                request_body_size = int(environ['CONTENT_LENGTH'])
            elif path == '/scheduled':
                logger.info("Received task %s scheduled at %s", environ['HTTP_X_AWS_SQSD_TASKNAME'], environ['HTTP_X_AWS_SQSD_SCHEDULED_AT'])
			
			# When the method is POST the variable will be sent in the HTTP request body which 
            # is passed by the WSGI server in the file like wsgi.input environment variable.
            request_body = environ['wsgi.input'].read(request_body_size)
            d = parse_qs(request_body)
            print d
            age = d.get('age', [''])[0] # Returns the first age value.
            hobbies = d.get('hobbies', []) # Returns a list of hobbies.
            action = d.get('action', []) # Returns a list of hobbies.
            # Always escape user input to avoid script injection
            age = escape(age)
            hobbies = [escape(hobby) for hobby in hobbies]
            if len(action) > 0:
                if action[0] == 'Get IoT States':
                    print 'REQUESTING AWS IOT INFO'
                    jsonMsg = return_thing_shadow_json()
                    jsonState = jsonMsg['state']['reported']['open']
                    if  jsonState == 1:
                        garage_door_toggle_input = 'checked'
                        print 'door closed'
                    else: 
                        garage_door_toggle_input = ''
                        print 'door open'
					 
					#response = Template(response).safe_substitute(thing_shadow=jsonState)
        except (TypeError, ValueError):
            logger.warning('Error retrieving request body for async work.')
            request_body_size = 0
    
    print "Age = ",age,"Visits = ", inc_value, "jsonState = ", jsonState 
    response = Template(response).safe_substitute(inc_value=inc_value,age_value=age,
    LED_toggle_handle='checked',thing_shadow=jsonState, garage_door_toggle_handle = garage_door_toggle_input)
	
    status = '200 OK'
    headers = [('Content-type', 'text/html')]

    start_response(status, headers)
    return [response]

class ThreadingWSGIServer(ThreadingMixIn, WSGIServer): 
    pass

if __name__ == '__main__':  
    global jsonState
    jsonMsg = return_thing_shadow_json()
    jsonState = jsonMsg['state']['reported']['open']
	
	#jsonState = 'TestjsonState'
	
    httpd = make_server('', 8000, application, ThreadingWSGIServer)

    print "Serving on port 8000..."
    httpd.serve_forever()
