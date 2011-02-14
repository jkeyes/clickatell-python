#
# Copyright 2010 John Keyes <code@keyes.ie>
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import httplib, re, types, urllib

# regular expression to parse individual lines of a response
KEY_VALUE_RE = re.compile('^([A-Za-z]+)\:\s*(.*)$')

class ClickatellError(Exception):
    """
    Any error returned by the Clickatell HTTP API.
    """
    
    def __init__(self, code, message):
        """
        Creates a new error with the specified code and message.
        """
        self.code = code
        self.message = message
        
    def __str__(self):
        """
        Return a string representation of the error.
        """
        return "<Clickatell Error: %s (Code %s)>" % (self.message, self.code)

class ClickatellResponse(dict):
    """
    A ClickatellReponse instance is a dict representation of a response
    received from the Clickatell HTTP API.
    
    Unique key-value responses from the API are stored as strings, for example;
        response['ID'] == '863db9cfe0cd991ed17fd3ac2cc22c8b'.
    
    Repeating keys are stored as lists (the batch methods return
    multiple messages ids). For example;
        response['ID'] == ['863db9cfe0cd991ed17fd3ac2cc22c8b', '...']
    """

    def __init__(self, data):
        """
        Creates a new response from the data received from the API.
        """
        self._parse_response(data)

    def _parse_response(self, data):
        """
        Parses the response data and stores in the dict.
        """
        
        for line in data.split("\n"):
            # just in case there is any leading or trailing whitespace
            line = line.strip()
            
            # Some API calls end with an empty line (e.g. routeCoverage)
            # We ignore blank lines.
            if not line:
                continue
            
            # parse the response
            match = KEY_VALUE_RE.match(line)
            key = match.group(1)
            value = match.group(2)
            
            # error handling
            if key == "ERR":
                # If an error response has a code the message beings with <code>, <description>.
                # RouteCoverage provides no error code, so we use None as the code.
                if ',' in value:
                    code, message = value.split(',')
                    raise ClickatellError(code.strip(), message.strip())
                else:
                    raise ClickatellError(None, value.strip())
            
            # Store the response.
            # This response object is simply a dict. The value of a unique key is stored as a
            # string. The values of a repeating key are stored in a list.
            if key in self:
                _value = self[key]
                if type(_value) == types.ListType:
                    _value.append(value)
                else:
                    self[key] = [_value, value]
            else:
                self[key] = value


class Clickatell(object):
    """
    A Clickatell instance provides access to the Clickatell HTTP API.
    
    For example;
      clickatell = Clickatell(user=xxx, password=xxx, api_id=xxx)
      clickatell.ping()
      
    Note: because the sendmsg api uses 'from' as a parameter you cannot use
    that as a named argument to the method.
    
    >>> clickatell.sendmsg(to='xxx', from='xxx', text='xxx') 
      File "<stdin>", line 1
        clickatell.sendmsg(to='xxx', from='xxx', text='xxx')
                                        ^
    SyntaxError: invalid syntax

    Instead you should use a final parameter of the form **params (see
    http://docs.python.org/tutorial/controlflow.html#keyword-arguments).
    
    >>> params = { 'to': 'xxx', 'from': 'xxx', 'text':'xxx' }
    >>> clickatell.sendmsg(**params)
    """

    # The address of the api server.
    SERVER = 'api.clickatell.com'
    
    # all of the methods supported by the Clickatell API.
    METHODS = {
        'auth':          'http/auth',
        'delmsg':        'http/delmsg',
        'getbalance':    'http/getbalance',
        'getmsgcharge':  'http/getmsgcharge',
        'ping':          'http/ping',
        'sendmsg':       'http/sendmsg',
        'token_pay':     'http/token_pay',
        'querymsg':      'http/querymsg',
        'startbatch':    'http_batch/startbatch',
        'senditem':      'http_batch/senditem',
        'quicksend':     'http_batch/quicksend',
        'endbatch':      'http_batch/endbatch',
        'routeCoverage': 'utils/routeCoverage.php',
        'ind_push':      'mms/ind_push.php',
        'si_push':       'mms/si_push'
    }

    def __init__(self, user, password, api_id):
        """
        Creates a Clickatell API stub.
        """
        self._connection = httplib.HTTPSConnection(Clickatell.SERVER)
        auth = self.auth(user=user,password=password,api_id=api_id)
        self._session_id = auth['OK']

    def _create_handler(self, method):
        """
        Creates a handler for the specified method.
        """
        def _handler(**args):
            # If we have a session_id include it in the parameters. This
            # session_id is returned by the http/auth method (which is
            # called when an instance of this class is created).
            if hasattr(self, '_session_id'):
                args['session_id'] = self._session_id
            params = urllib.urlencode(args)
            self._connection.connect()
            self._connection.request("GET", "/%s?%s" % (method, params))
            response = self._connection.getresponse()
            result = ClickatellResponse(response.read())
            self._connection.close()
            return result
        return _handler

    def __getattribute__(self, name):
        if name in Clickatell.METHODS:
            return self._create_handler(Clickatell.METHODS[name])
        else:
            return object.__getattribute__(self, name)        
