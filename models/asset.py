import time

from core import db, helpers, logging
from core import model, cache

class _asset(db._document):
    name = str()
    entity = str()
    assetType = str()
    lastSeen = list()
    lastSeenTimestamp = float()
    fields = dict()

    _dbCollection = db.db["asset"]

    def new(self, acl, name, entity, assetType, updateSource, fields, lastSeenTimestamp, priority):
        self.acl = acl
        self.name = name
        self.entity = entity
        self.assetType = assetType
        self.lastSeen = [ {**fields, **{"priority":priority, "source" : updateSource}} ]
        self.lastSeenTimestamp = lastSeenTimestamp
        self.fields = fields
        return super(_asset, self).new()

    def bulkNew(self, acl, name, entity, assetType, updateSource, fields, lastSeenTimestamp, priority, bulkClass):
        self.acl = acl
        self.name = name
        self.entity = entity
        self.assetType = assetType
        self.lastSeen = [ {**fields, **{"priority":priority, "source" : updateSource}} ]
        self.lastSeenTimestamp = lastSeenTimestamp
        self.fields = fields
        return super(_asset, self).bulkNew(bulkClass)

    # Override parent to support plugin dynamic classes
    def loadAsClass(self,jsonList,sessionData=None):
        result = []
        # Ininilize global cache
        cache.globalCache.newCache("modelCache",sessionData=sessionData)
        # Loading json data into class
        for jsonItem in jsonList:
            _class = cache.globalCache.get("modelCache",jsonItem["classID"],getClassObject,sessionData=sessionData)
            if _class is not None:
                if len(_class) == 1:
                    _class = _class[0].classObject()
                if _class:
                    result.append(helpers.jsonToClass(_class(),jsonItem))
                else:
                    logging.debug("Error unable to locate class: actionID={0} classID={1}".format(jsonItem["_id"],jsonItem["classID"]))
        return result

    def setAttribute(self,attr,value,lastSeenSource=None,sessionData=None):
        if not sessionData or db.fieldACLAccess(sessionData,self.acl,attr,accessType="write"):
            if lastSeenSource:
                self.lastSeen[lastSeenSource][attr] = value
                return True
            setattr(self,attr,value)
        return True

def getClassObject(classID,sessionData):
    return model._model().getAsClass(sessionData,id=classID)

