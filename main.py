#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


YOUR_BREAKING_IT = [
    "http://twitter.com/binarydan/lists/fabfriends/statuses.json"
]


USERNAME = "YOUR TWITTER USER NAME"
PASSWORD = "YOUR TWITTER PASSWORD"
import wsgiref.handlers
import os
from google.appengine.ext.webapp import template
import cgi
from google.appengine.ext import webapp
import logging
import datetime
import rfc822

def decode_datetime(obj):
    if 'created_at' not in obj:
        return obj

    dt = rfc822.parsedate(obj['created_at'])
    dt = datetime.datetime(*dt[0:6])
    obj['created_at'] = dt
    return obj

class MainHandler(webapp.RequestHandler):
    
    def post(self):
        from google.appengine.api import urlfetch
        from google.appengine.api import memcache
        rpc = urlfetch.create_rpc()
        
        
        list_url = cgi.escape(self.request.get('url'))
        list_url = list_url.strip()
        if list_url[-1] == "/":
            list_url = list_url[:-1]
        if list_url.find("lists/") >= 0:
            list_url = list_url.replace("lists/","")
        split    = list_url.split("/")
        og       = "http://twitter.com/%s/%s" % (split[-2],split[-1])
        json_url = "http://twitter.com/%s/lists/%s/statuses.json" % (split[-2],split[-1])
        rss_url  = "http://twiterlist2rss.appspot.com/%s/lists/%s/statuses.rss" % (split[-2],split[-1])
        urlfetch.make_fetch_call(rpc, rss_url)       
        template_values = {
            "posted":True,
            "og":og,
            "json_url":json_url,
            "rss_url":rss_url           
        }
        path = os.path.join(os.path.dirname(__file__),'templates' ,'index.html')
        self.response.out.write(template.render(path, template_values))
    def get(self):
        template_values = {}
          
        path = os.path.join(os.path.dirname(__file__),'templates' ,'index.html')
        self.response.out.write(template.render(path, template_values))

class RssHandler(webapp.RequestHandler):

    def get(self,username=None,listname=None):
        from django.utils import simplejson as json
        from google.appengine.api.urlfetch import fetch
        from google.appengine.api import memcache
        import base64
        import pprint
        
        json_url = "http://twitter.com/%s/lists/%s/statuses.json" % (username,listname)
        
        if json_url in YOUR_BREAKING_IT:
            self.error(int(400))
            self.response.out.write("your using it too much, 1 request an hour is all you need. Contact me at voidfiles@gmail.com when you reduced the number of calls.")
            return
            
        result = memcache.get(json_url)
        if not result:
            try:
                authString = 'Basic ' + base64.encodestring(USERNAME + ":" + PASSWORD)
                result = fetch(json_url, deadline=10,headers={'AUTHORIZATION' : authString})
                if int(result.status_code) == 200:
                    memcache.add(json_url, result, int(60*60) )
                else:
                    logging.error('There was an error retrieving error code: %s %s %s %s' % (result.status_code,result.content,json_url, pprint.pformat(result.headers)))
                    self.error(int(result.status_code))
                    template_name = str(str(result.status_code) + ".html")
                    path = os.path.join(os.path.dirname(__file__),'templates' ,template_name)
                    self.response.out.write(template.render(path, {}))
                    return
            except e:
                logging.error('There was an error retrieving %s %s' % (json_url, e))
                self.error(500)
                path = os.path.join(os.path.dirname(__file__),'templates' ,'500.html')
                self.response.out.write(template.render(path, {}))
                return
            
        obj = json.loads(result.content, object_hook=decode_datetime)
        template_values = {
            "json_data": obj,
            "json_url":json_url,
            "username":username,
            "listname":listname
        }

        path = os.path.join(os.path.dirname(__file__),'templates' ,'rss.xml')
        self.response.out.write(template.render(path, template_values))
        
        
def main():
    application = webapp.WSGIApplication([
        ('/', MainHandler),
        (r'/([^/]*)/lists/([^/]*)/statuses\.rss', RssHandler),],
        debug=False
    )
    wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
    main()
