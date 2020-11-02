import time

from core.models import action

from core import db, helpers, logging
from core import model, cache

from plugins.asset.models import asset

class _assetRelationship(db._document):
    timespan = int()
    data = dict()
    fromAsset = str()
    toAsset = str()
    count = int()
    lastSeen = int()

    _dbCollection = db.db["assetRelationship"]

    def addRelationship(self, acl, timespan, fromAsset, toAsset, data, count):
        try:
            result = cache.globalCache.get("dbModelCache",self.__class__.__name__,getClassByName,extendCacheTime=True)[0]
            self._dbCollection.update_one({ "timespan" : timespan, "fromAsset" : fromAsset, "toAsset" : toAsset, "data" : data, "classID" : result["_id"] },{ "$set" : { "acl" : acl, "lastSeen" : int(time.time()) }, "$inc" : { "count" : count } },upsert=True)
        except:
            pass

    def addRelationshipBulk(self, acl, timespan, fromAsset, toAsset, data, count, bulkClass):
        try:
            result = cache.globalCache.get("dbModelCache",self.__class__.__name__,getClassByName,extendCacheTime=True)[0]
            query = { "timespan" : timespan, "fromAsset" : fromAsset, "toAsset" : toAsset, "data" : data, "classID" : result["_id"] }
            update= { "$set" : { "acl" : acl, "lastSeen" : int(time.time()) }, "$inc" : { "count" : count } }
            self.bulkUpsert(query, update, bulkClass, customUpdate=True)
        except:
            pass

class _assetRelationshipUpdate(action._action):
    relationshipData = dict()
    fromAsset = str()
    toAsset = str()
    count = str()
    timespan = int()

    def __init__(self):
        self.bulkClass = db._bulk()

    def postRun(self):
        self.bulkClass.bulkOperatonProcessing()

    def run(self,data,persistentData,actionResult):
        relationshipData = helpers.evalDict(self.relationshipData,{"data" : data})
        fromAsset = helpers.evalString(self.fromAsset,{"data" : data})
        toAsset = helpers.evalString(self.toAsset,{"data" : data})
        count = helpers.evalString(self.count,{"data" : data})

        timespan = 3600
        if self.timespan > 0:
            timespan = self.timespan
        timespan = helpers.roundTime(roundTo=timespan).timestamp()

        _assetRelationship().addRelationshipBulk(self.acl,timespan,fromAsset,toAsset,relationshipData,count,self.bulkClass)
        actionResult["result"] = True
        actionResult["rc"] = 0
        return actionResult

def getClassByName(match,sessionData):
    return model._model().query(query={"className" : match})["results"]