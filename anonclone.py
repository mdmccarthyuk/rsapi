#!/usr/bin/python

import urllib2
import json
import sys
import os
import argparse
import time

from rsvol import RSVolume
from rsauth import RSAuthToken

authFile = "acc.json"
jobFile = "job.json"

def main():
  if (os.path.isfile(authFile)):
    with open(authFile) as inFile:
      auth = json.load(inFile)
    authToken = RSAuthToken()
    authToken.user=auth['auth']['user']
    authToken.key=auth['auth']['key']
  else:
    print "Can't find acc.json account file"
    sys.exit(1)
  if (os.path.isfile(jobFile)):
    with open(jobFile) as inFile:
      jobObj = json.load(inFile)
  print "Getting auth token"
  authToken.getToken()
  print "Getting server ID"
  serverID = rsGetServerID(authToken.token,jobObj['job']['server'],auth['auth']['account'])
  print "  Server: %s" % serverID
  print "Getting volume ID"
  targetVolume = RSVolume()
  targetVolume.setToken(authToken.token)
  targetVolume.setAccount(auth['auth']['account'])
  volumeID = rsGetVolumeID(authToken.token,jobObj['job']['volume'],auth['auth']['account'])
  print "  Volume: %s" % volumeID
  print "Getting volume Name"
  if targetVolume.getByID(volumeID):
    print "  Name: %s" % targetVolume.display_name 
  else:
    print "ERROR: Volume could not be found"
    sys.exit(1)
  targetVolume.listAll()
  # Exit here for testing
  sys.exit(0)
  print "Cloning volume"
  newID = targetVolume.clone(jobObj['job']['newName'],jobObj['job']['newDesc'])
  if not newID:
    print "ERROR: Disk could not be cloned"
    sys.exit(1)
  print "  New ID: %s" % newID
  print "Showing volume"
  targetVolume.showDetail(newID)
  print "Waiting for volume"
  targetVolume.waitComplete(newID)
  print "Attaching volume"
  targetVolume.attach(newID,serverID,"/dev/xvdc")
  time.sleep(30)
  print "Detaching volume"
  targetVolume.detach(newID,serverID,"/dev/xvdc")
  time.sleep(30)
  print "Deleting volume"
  targetVolume.delete(newID)

def rsGetServerID(token,serverName,account):
  req = urllib2.Request('https://lon.servers.api.rackspacecloud.com/v2/'+account+'/servers')
  req.add_header("X-Auth-Token",token)
  res = urllib2.urlopen(req)
  serverObj = json.loads(res.read())
  for server in serverObj['servers']:
    if server['name'] == serverName:
      return server['id']
  return False
 
def rsGetVolumeID(token,volumeName,account):
  req = urllib2.Request('https://lon.blockstorage.api.rackspacecloud.com/v1/'+account+'/volumes')
  req.add_header("X-Auth-Token",token)
  res = urllib2.urlopen(req)
  volumeObj = json.loads(res.read())
  for volume in volumeObj['volumes']:
    if volume['display_name'] == volumeName:
      return volume['id']
  return False

if __name__ == "__main__":
  main()
  sys.exit(0)

