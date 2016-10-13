#!/usr/bin/python

import urllib2
import json
import sys

class RSAuthToken:
  def __init__(self):
    self.user=""
    self.key=""
    self.token=""

  def getToken(self):
    auth = {
      "auth": {
        "RAX-KSKEY:apiKeyCredentials": {
          "username": self.user,
          "apiKey": self.key
        }
      }
    }
    authData = json.dumps(auth)
    req = urllib2.Request('https://identity.api.rackspacecloud.com/v2.0/tokens')
    req.add_header("Content-type", "application/json")
    req.add_header("Content-length", str(len(authData)))
    req.add_data(authData)
    res = urllib2.urlopen(req)
    authRes = json.loads(res.read())
    # ERROR CHECK HERE!
    self.token = authRes['access']['token']['id'] 
    return self.token
