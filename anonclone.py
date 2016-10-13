#!/usr/bin/python

import urllib2
import json
import sys
import os
import argparse
import time

from rsvol import RSVolume
from rsauth import RSAuthToken
from rsserver import RSServer

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
  targetServer = RSServer()
  targetServer.setToken(authToken.token)
  targetServer.setAccount(auth['auth']['account'])
  serverID = targetServer.getIDByName(jobObj['job']['server'])
  if not serverID:
    print "ERROR: Can't find target server"
    sys.exit(1)
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
#  targetVolume.listAll()
  # Exit here for testing
#  sys.exit(0)
  print "Cloning volume"
  # Set type to SSD so clone produces an SSD
  targetVolume.volume_type="SSD"
  newID = targetVolume.clone(jobObj['job']['newName'],jobObj['job']['newDesc'])
  if not newID:
    print "ERROR: Disk could not be cloned"
    sys.exit(1)
  print "  New ID: %s" % newID
  print "Showing volume"
  targetVolume.showDetail(newID)
  print "Waiting for volume"
  targetVolume.waitComplete(newID)
  print "Getting ID of /dev/xvdb"
  oldID = targetVolume.getIDByAttachedDevice(serverID,"/dev/xvdb")
  if not oldID:
    print "ERROR: Old disk could not be found"
    sys.exit(1)
  print "  Old ID: %s" % oldID
  print "Detaching volume"
  targetVolume.detach(oldID,serverID,"/dev/xvdb")
  time.sleep(30)
  print "Attaching volume"
  targetVolume.attach(newID,serverID,"/dev/xvdb")
  time.sleep(30)
#  print "Detaching volume"
#  targetVolume.detach(newID,serverID,"/dev/xvdc")
#  time.sleep(30)
#  print "Deleting volume"
#  targetVolume.delete(newID)

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

