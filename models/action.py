import time

from core.models import action
from core import db, helpers, function, logging, cache, audit

import jimi

from plugins.asset.models import asset	

class _assetUpdate(action._action):
	assetName = str()
	assetType = str()
	assetEntity = str()
	updateTime = str()
	updateSource = str()
	sourcePriority = int()
	sourcePriorityMaxAge = 86400
	assetFields = dict()
	replaceExisting = bool()
	delayedUpdate = int()
	auditHistory = bool()
	mergeSource = bool()
	bulkUpdate = True

	def __init__(self,restrictClass=True):
		self.bulkClass = db._bulk()
		self.seen = []
		return super(_assetUpdate, self).__init__(restrictClass)

	def postRun(self):
		self.bulkClass.bulkOperatonProcessing()
		self.seen = []

	def run(self,data,persistentData,actionResult):
		assetName = helpers.evalString(self.assetName,{"data" : data})
		assetType = helpers.evalString(self.assetType,{"data" : data})
		assetEntity = helpers.evalString(self.assetEntity,{"data" : data})
		updateSource = helpers.evalString(self.updateSource,{"data" : data})
		updateTime = helpers.evalString(self.updateTime,{"data" : data})
		assetFields = helpers.evalDict(self.assetFields,{"data" : data})

		if not assetName or not assetType or not updateSource or not assetFields:
			actionResult["result"] = False
			actionResult["msg"] = "Missing required properties"
			actionResult["rc"] = 403
			return actionResult

		match = "{0}-{1}-{2}".format(assetName,assetType,assetEntity)

		if assetName in self.seen:
			actionResult["result"] = False
			actionResult["msg"] = "Asset already seen within this classes execution time"
			actionResult["rc"] = 901
			return actionResult

		assetItem = cache.globalCache.get("assetCache",match,getAsset,assetName,assetType,assetEntity,self.bulkUpdate,customCacheTime=300)
		if assetItem is None:
			assetItem = []
		self.seen.append(assetName)
		if not assetItem:
			if assetName:
				assetItem = asset._asset().bulkNew(self.acl,assetName,assetEntity,assetType,updateSource,assetFields,updateTime,self.sourcePriority,self.sourcePriorityMaxAge,self.bulkClass)
			actionResult["result"] = True
			actionResult["msg"] = "Created new asset"
			actionResult["rc"] = 201
			return actionResult

		assetChanged = False
		# Removing entires if more than one result is found
		if len(assetItem) > 1:
			newestItem = assetItem[0]
			for singleAssetItem in assetItem:
				if newestItem.lastUpdateTime < singleAssetItem.lastUpdateTime:
					singleAssetItem.delete()
				else:
					newestItem.delete()
					newestItem = singleAssetItem
			cache.globalCache.get("assetCache",match,getAsset,assetName,assetType,assetEntity,self.bulkUpdate,customCacheTime=300,forceUpdate=True)
			assetItem = newestItem
			assetChanged = True
		else:
			assetItem = assetItem[0]

		if assetItem._id == "":
			actionResult["result"] = False
			actionResult["msg"] = "Asset not yet added"
			actionResult["rc"] = 404
			return actionResult

		lastSeen = None
		existingLastSeen = True
		for source in assetItem.lastSeen:
			if source["source"] == updateSource:
				lastSeen = source
				if "lastUpdate" not in lastSeen:
					lastSeen["lastUpdate"] = 0
				if "sourcePriorityMaxAge" not in lastSeen:
					lastSeen["sourcePriorityMaxAge"] = self.sourcePriorityMaxAge
				break
		if not lastSeen:
			assetItem.lastSeen.append({ "source" : updateSource, "lastUpdate" : 0 })
			lastSeen = assetItem.lastSeen[-1]
			existingLastSeen = False
		
		# Converting millsecond int epoch into epoch floats
		currentTimestamp = lastSeen["lastUpdate"]
		if len(str(currentTimestamp).split(".")[0]) == 13:
			currentTimestamp = currentTimestamp / 1000
		if len(str(updateTime).split(".")[0]) == 13:
			updateTime = updateTime / 1000
		
		newTimestamp = None
		if updateTime:
			try:
				if updateTime < currentTimestamp and updateTime > 0:
					newTimestamp = False
				else:
					newTimestamp = updateTime
			except (KeyError, ValueError):
				pass
		if newTimestamp == None:
			newTimestamp = time.time()

		if newTimestamp != False:
			try:
				if (time.time() - currentTimestamp) < self.delayedUpdate:
					actionResult["result"] = False
					actionResult["msg"] = "Delay time not met"
					actionResult["rc"] = 300
					return actionResult
			except KeyError:
				pass
			assetChanged = True
			if newTimestamp > assetItem.lastSeenTimestamp:
				assetItem.lastSeenTimestamp = newTimestamp

			if self.replaceExisting:
				lastSeen = assetFields
			else:
				for key, value in assetFields.items():
					if key in lastSeen and (type(lastSeen[key]) == dict and type(value) == dict) and self.mergeSource:
						lastSeen[key] = {**lastSeen[key], **value}
					else:
						lastSeen[key] = value

			lastSeen["source"] = updateSource			
			lastSeen["priority"] = self.sourcePriority
			lastSeen["lastUpdate"] = newTimestamp
			lastSeen["sourcePriorityMaxAge"] = self.sourcePriorityMaxAge

		if assetChanged:
			if existingLastSeen:
				self.bulkClass.newBulkOperaton(assetItem._dbCollection.name,"update",{ "query" : { "_id" : jimi.db.ObjectId(assetItem._id), "lastSeen.source" : updateSource }, "update" : { "$set" : { "lastSeen.$" : lastSeen } } })
			else:
				self.bulkClass.newBulkOperaton(assetItem._dbCollection.name,"update",{ "query" : { "_id" : jimi.db.ObjectId(assetItem._id) }, "update" : { "$push" : { "lastSeen" : lastSeen } } })
			actionResult["result"] = True
			actionResult["msg"] = "Updated asset"
			actionResult["rc"] = 302
			return actionResult

		actionResult["result"] = True
		actionResult["msg"] = "Nothing to do"
		actionResult["rc"] = 304
		return actionResult

class _assetProcess(action._action):
	assetType = str()
	assetEntity = str()

	def __init__(self,restrictClass=True):
		self.bulkClass = db._bulk()
		return super(_assetProcess, self).__init__(restrictClass)

	def postRun(self):
		self.bulkClass.bulkOperatonProcessing()

	def run(self,data,persistentData,actionResult):
		assetType = helpers.evalString(self.assetType,{"data" : data})
		assetEntity = helpers.evalString(self.assetEntity,{"data" : data})

		assetItems = asset._asset().getAsClass(query={ "assetType" : assetType, "entity" : assetEntity })
		for assetItem in assetItems:
			foundValues = {}
			sourceList = []
			lastSeenTimestamp = 0
			now = time.time()
			blacklist = ["lastUpdate","priority","source","sourcePriorityMaxAge"]
			for sourceValue in assetItem.lastSeen:
				if lastSeenTimestamp < sourceValue["lastUpdate"]:
					lastSeenTimestamp = sourceValue["lastUpdate"]
				for key, value in sourceValue.items():
					if key not in blacklist:
						try:
							if key not in foundValues:
								if (sourceValue["lastUpdate"] + sourceValue["sourcePriorityMaxAge"]) > now:
									foundValues[key] = { "value" : value, "priority" : sourceValue["priority"] }
								else:
									foundValues[key] = { "value" : value, "priority" : 66535 }
							else:
								if sourceValue["priority"] < foundValues[key]["priority"] and (sourceValue["lastUpdate"] + sourceValue["sourcePriorityMaxAge"]) > now:
									foundValues[key] = { "value" : value, "priority" : sourceValue["priority"] }
						except KeyError as e:
							print("{0}, {1}, {2}".format(assetItem,sourceValue,e))
			changes = False
			for key, value in foundValues.items():
				if key in assetItem.fields:
					if assetItem.fields[key] != value["value"]:
						changes = True
						assetItem.fields[key] = value["value"]
				else:
					assetItem.fields[key] = value["value"]
					changes = True
			popList = []
			for field in assetItem.fields.keys():
				if field not in foundValues:
					changes = True
					popList.append(field)
			for popItem in popList:
				del assetItem.fields[popItem]
			if assetItem.lastSeenTimestamp < lastSeenTimestamp:
				changes = True
			if changes:
				assetItem.lastSeenTimestamp = lastSeenTimestamp
				assetItem.bulkUpdate(["lastSeenTimestamp","fields"],self.bulkClass)

		actionResult["result"] = True
		actionResult["msg"] = "Done"
		actionResult["rc"] = 0
		return actionResult
		
def getAssetBulk(cacheUID,sessionData,assetType,entity):
	results = asset._asset().getAsClass(query={"assetType" : assetType, "entity" : entity})
	resultDict = {}
	for result in results:
		try:
			resultDict["{0}-{1}-{2}".format(result.name,assetType,entity)].append(result)
		except:
			resultDict["{0}-{1}-{2}".format(result.name,assetType,entity)] = [result]
	return resultDict

def getAsset(cacheUID,sessionData,name,assetType,entity,bulkUpdate):
	if bulkUpdate:
		assetCacheBulk = cache.globalCache.get("assetCacheBulk",f"assetBulk-{assetType}-{entity}",getAssetBulk,assetType,entity,customCacheTime=300)
		try:
			return assetCacheBulk[cacheUID]
		except KeyError:
			return None
	else:
		results = asset._asset().getAsClass(query={ "name" : name, "assetType" : assetType, "entity" : entity})
		if len(results) > 0:
			return results
	return None
