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

    def __init__(self):
        cache.globalCache.newCache("dbModelCache")

    def addRelationship(self, acl, timespan, fromAsset, toAsset, data, count):
        result = cache.globalCache.get("dbModelCache",self.__class__.__name__,getClassByName,extendCacheTime=True)
        if len(result) == 1:
            result = result[0]
            self._dbCollection.update_one({ "timespan" : timespan, "fromAsset" : fromAsset, "toAsset" : toAsset, "data" : data, "classID" : result["_id"] },{ "$set" : { "acl" : acl, "lastSeen" : int(time.time()) }, "$inc" : { "count" : count } },upsert=True)


class _assetRelationshipUpdate(action._action):
    relationshipData = dict()
    fromAsset = str()
    toAsset = str()
    count = str()
    resolveAsset = bool()
    continueAfterResolveError = bool()
    field = str()
    assetType = str()
    assetEntity = str()
    timespan = int()

    def run(self,data,persistentData,actionResult):
        relationshipData = helpers.evalDict(self.relationshipData,{"data" : data})
        fromAsset = helpers.evalString(self.fromAsset,{"data" : data})
        toAsset = helpers.evalString(self.toAsset,{"data" : data})
        count = helpers.evalString(self.count,{"data" : data})
        field = helpers.evalString(self.field,{"data" : data})
        assetType = helpers.evalString(self.assetType,{"data" : data})
        assetEntity = helpers.evalString(self.assetEntity,{"data" : data})

        if self.resolveAsset:
            try:
                fromAsset = asset._asset().getAsClass(query={ "assetType" : assetType, "entity" : assetEntity, "fields.{0}".format(field) : fromAsset },limit=1,sort=[( "lastSeenTimestamp", -1 )])[0]._id
            except:
                if not self.continueAfterResolveError:
                    actionResult["result"] = True
                    actionResult["msg"] = "Unable to resolve asset"
                    actionResult["rc"] = 9
                    return actionResult
            try:
                toAsset = asset._asset().getAsClass(query={ "assetType" : assetType, "entity" : assetEntity, "fields.{0}".format(field) : toAsset },limit=1,sort=[( "lastSeenTimestamp", -1 )])[0]._id
            except:
                if not self.continueAfterResolveError:
                    actionResult["result"] = True
                    actionResult["msg"] = "Unable to resolve asset"
                    actionResult["rc"] = 9
                    return actionResult

        timespan = 3600
        if self.timespan > 0:
            timespan = self.timespan
        timespan = helpers.roundTime(roundTo=timespan).timestamp()

        _assetRelationship().addRelationship(self.acl,timespan,fromAsset,toAsset,relationshipData,count)
        actionResult["result"] = True
        actionResult["rc"] = 0
        return actionResult

def getClassByName(match,sessionData):
    return model._model().query(query={"className" : match})["results"]