#!/usr/bin/python

import urllib2
import json
import sys
import time

class RSServer:
  endpoint = "https://lon.servers.api.rackspacecloud.com/v2/xx/servers"
  authToken = "NONE"

  def __init__(self):
    self.ID=""
    self.name=""

  def setToken(self,token):
    RSServer.authToken = token

  def setAccount(self,accountID):
    RSServer.endpoint = "https://lon.servers.api.rackspacecloud.com/v2/"+accountID+"/servers"

  def checkToken(self,message):
    if RSServer.authToken == "NONE":
      print "ERROR: RSServer - Attempt to use API without calling setToken ("+message+")"
      sys.exit(1)

  # Gets an ID by matching on name
  def getIDByName(self,serverName):
    self.checkToken("getByID")
    req = urllib2.Request(RSServer.endpoint)
    req.add_header("X-Auth-Token",RSServer.authToken)
    res = urllib2.urlopen(req)
    serverObj = json.loads(res.read())
    for server in serverObj['servers']:
      if server['name'] == serverName:
        return server['id']
    return False

