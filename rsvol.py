#!/usr/bin/python

import urllib2
import json
import sys
import time

class RSVolume:
  endpoint = "https://lon.blockstorage.api.rackspacecloud.com/v1/xx/volumes"
  serverEndpoint = "https://lon.servers.api.rackspacecloud.com/v2/xx/servers"
  authToken = "NONE"

  def __init__(self):
    self.ID=""
    self.size=0
    self.display_name=""
    self.display_description=""
    self.source_volID=""
    self.volume_type=""

  def setToken(self,token):
    RSVolume.authToken = token

  def checkToken(self,message):
    if RSVolume.authToken == "NONE":
      print "ERROR: Attempt to access storage API without setting auth token ("+message+")"
      sys.exit(1)

  def setAccount(self,accountID):
     RSVolume.endpoint = "https://lon.blockstorage.api.rackspacecloud.com/v1/"+accountID+"/volumes"
     RSVolume.serverEndpoint = "https://lon.servers.api.rackspacecloud.com/v2/"+accountID+"/servers"

  def getByID(self,volID):
    self.checkToken("getByID")
    req = urllib2.Request(RSVolume.endpoint+"/"+volID)
    req.add_header("X-Auth-Token",RSVolume.authToken)
    try: 
      res = urllib2.urlopen(req)
    except urllib2.HTTPError as err:
      message = "Unknown error"
      if err.code == 404:
        message = "Volume ID not found"
      if err.code == 401:
        message = "Authentication failed"
      print "ERROR: getByID - %s %s" % (message,err.code)
      return False
    volumeObj = json.loads(res.read())
    self.display_name = volumeObj['volume']['display_name']
    self.display_description = volumeObj['volume']['display_description']
    self.volume_type = volumeObj['volume']['volume_type']
    self.ID = volID
    self.size = int(volumeObj['volume']['size'])
    return True

  # Clone current volume to a new one
  # Returns False on failure or a Volume ID on success
  def clone(self,newName,newDesc):
    self.checkToken("clone")
    if self.ID == "":
      print "ERROR: No volume ID set"
      return False
    req = urllib2.Request(RSVolume.endpoint)
    req.add_header("X-Auth-Token",RSVolume.authToken)
    req.add_header("Content-type","application/json")
    newVol = {
      "volume": {
        "display_name": newName,
        "display_description": newDesc,
        "size": self.size,
        "volume_type": self.volume_type,
        "source_volid": self.ID
      }
    }
    volData = json.dumps(newVol)
    req.add_header("Content-length",str(len(volData)))
    req.add_data(volData)
    try: 
      res = urllib2.urlopen(req)
    except urllib2.HTTPError as err:
      message = "Unknown error"
      print "ERROR: cloneVolume - %s %s" % (message,err.code)
      return False
    newVolObj = json.loads(res.read())
    newVolID = newVolObj['volume']['id']
    return newVolID 

  # Lists all volumes
  def listAll(self):
    self.checkToken("listAll")
    print "All Volumes:"
    req = urllib2.Request(RSVolume.endpoint)
    req.add_header("X-Auth-Token",RSVolume.authToken)
    res = urllib2.urlopen(req)
    volumeObj = json.loads(res.read())
    for volume in volumeObj['volumes']:
      print "%s - %s" % (volume['display_name'],volume['id'])

  # Delete the volume with specified ID of volID
  def delete(self,volID):
    self.checkToken("delete")
    req = urllib2.Request(RSVolume.endpoint+"/"+volID)
    req.add_header("X-Auth-Token",RSVolume.authToken)
    req.get_method=lambda: "DELETE"
    res = urllib2.urlopen(req)
    print res.code

  # Show the detail of volume matching ID volID
  def showDetail(self,volID):
    self.checkToken("showDetail")
    req = urllib2.Request(RSVolume.endpoint+"/"+volID)
    req.add_header("X-Auth-Token",RSVolume.authToken)
    res = urllib2.urlopen(req)
    volumeObj = json.loads(res.read())
    for key in volumeObj['volume']:
      print "%s = %s" % (key, volumeObj['volume'][key])
  
  # Simple block - wait for a clone to complete 
  def waitComplete(self,volID):
    self.checkToken("waitComplete")
    cloneProgress = "0%"
    while cloneProgress is not None:
      req = urllib2.Request(RSVolume.endpoint+"/"+volID)
      req.add_header("X-Auth-Token",RSVolume.authToken)
      res = urllib2.urlopen(req)
      volumeObj = json.loads(res.read())
      if 'clone-progress' in volumeObj['volume']['metadata']: 
        cloneProgress = volumeObj['volume']['metadata']['clone-progress']
      else:
        if volumeObj['volume']['status'] == 'creating':
          cloneProgress = "creating"
        else:
          cloneProgress = None
      if cloneProgress is not None:
        print "Progress: "+cloneProgress 
        time.sleep(60)
    
    for key in volumeObj['volume']:
      print "%s = %s" % (key, volumeObj['volume'][key])
 
  def attach(self,volID,serverID,deviceName=None):
    self.checkToken("attach")
    print "Attaching to server"
    req = urllib2.Request(RSVolume.serverEndpoint+"/"+serverID+"/os-volume_attachments")
    req.add_header("X-Auth-Token",RSVolume.authToken)
    attachObj = {
      "volumeAttachment": {
        "device": deviceName,
        "volumeId": volID
      }
    }
    attachReq = json.dumps(attachObj)
    print attachReq
    req.add_header("Content-type","application/json")
    req.add_header("Content-length",str(len(attachReq)))
    req.add_data(attachReq)
    res = urllib2.urlopen(req)
    attachRes = json.loads(res.read())
    if 'id' not in attachRes['volumeAttachment']:
      return False
    return attachRes['volumeAttachment']['id']

  # Returns the volume ID of a volume attached to a server.  Matches on device name (eg /dev/xvdb1) 
  # Returns False if no match found
  def getIDByAttachedDevice(self,serverID,deviceName):
    self.checkToken("getIDByAttachedDevice")
    req = urllib2.Request(RSVolume.serverEndpoint+"/"+serverID+"/os-volume_attachments")
    req.add_header("X-Auth-Token",RSVolume.authToken)
    res = urllib2.urlopen(req)
    attachedRes = json.loads(res.read())
    for volume in attachedRes['volumeAttachments']:
      if volume['device'] == deviceName:
        return volume['id']
    return False

  # Detaches a disk from a server - matches on device name (eg /dev/xvdb1)
  # Returns False on error or True on success. 
  def detach(self,volID,serverID,deviceName):
    self.checkToken("detach")
    print "Detaching" 
    targetID = self.getIDByAttachedDevice(serverID,deviceName)
    if targetID is None:
      return False
    req2 = urllib2.Request(RSVolume.serverEndpoint+"/"+serverID+"/os-volume_attachments/"+targetID)
    req2.add_header("X-Auth-Token",RSVolume.authToken)
    req2.get_method = lambda: 'DELETE'
    try:
      res2 = urllib2.urlopen(req2)
    except urllib2.HTTPError as err:
      print "ERROR: detaching %s" % err.code
      return False
    return True
 
if __name__ == "__main__":
  sys.exit(0)

