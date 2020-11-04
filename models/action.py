import time

from core.models import action
from core import db, helpers, function, logging, cache, audit

from plugins.asset.models import asset

class _assetBulkUpdate(action._action):
	assetType = str()
	assetEntity = str()
	updateTime = str()
	updateSource = str()
	sourcePriority = int()
	assetData = dict()
	replaceExisting = bool()
	delayedUpdate = int()
	auditHistory = bool()

	
	def __init__(self):
		cache.globalCache.newCache("assetCache")
		self.bulkClass = db._bulk()

	def postRun(self,data,persistentData):
		self.bulkClass.bulkOperatonProcessing()

	def run(self,data,persistentData,actionResult):
		assetType = helpers.evalString(self.assetType,{"data" : data})
		assetEntity = helpers.evalString(self.assetEntity,{"data" : data})
		updateSource = helpers.evalString(self.updateSource,{"data" : data})
		updateTime = helpers.evalString(self.updateTime,{"data" : data})
		assetData = helpers.evalDict(self.assetData,{"data" : data})

		assetNames = []
		for assetName, assetFields in assetData.items():
			assetNames.append(assetName)

		existingAssets = asset._asset().getAsClass(query={ "name" : { "$in" : assetNames }, "assetType" : assetType, "entity" : assetEntity })

		# Updating existing
		for assetItem in existingAssets:
			if assetItem.name in assetData:
				del assetData[assetItem.name]

			newTimestamp = None
			if updateTime:
				try:
					if updateTime < assetItem.lastSeen[updateSource]["lastUpdate"]:
						newTimestamp = False
					else:
						newTimestamp = updateTime
				except (KeyError, ValueError):
					pass
			if newTimestamp == None:
				newTimestamp = time.time()

			assetChanged = False
			if newTimestamp != False:
				try:
					if (time.time() - assetItem.lastSeen[updateSource]["lastUpdate"]) < self.delayedUpdate:
						continue
				except KeyError:
					pass
				assetChanged = True
				if newTimestamp > assetItem.lastSeenTimestamp:
					assetItem.lastSeenTimestamp = newTimestamp

				if self.replaceExisting:
					assetItem.lastSeen[updateSource] = assetFields
				else:
					for key, value in assetFields.items():
						assetItem.lastSeen[updateSource][key] = value

				assetItem.lastSeen[updateSource]["priority"] = self.sourcePriority
				assetItem.lastSeen[updateSource]["lastUpdate"] = newTimestamp

			# Working out priority and define fields
			if assetChanged:
				foundValues = {}
				blacklist = ["lastUpdate","priority"]
				for source, sourceValue in assetItem.lastSeen.items():
					for key, value in sourceValue.items():
						if key not in blacklist:
							if key not in foundValues:
								foundValues[key] = { "value" : value, "priority" : sourceValue["priority"] }
							else:
								if sourceValue["priority"] < foundValues[key]["priority"]:
									foundValues[key] = { "value" : value, "priority" : sourceValue["priority"] }
				assetItem.fields = {}
				for key, value in foundValues.items():
					assetItem.fields[key] = value["value"]
				assetItem.bulkUpdate(["lastSeen","fields"],self.bulkClass)

		# Adding new
		for assetName, assetFields in assetData.items():
			assetItem = asset._asset().bulkNew(self.acl,assetName,assetEntity,assetType,updateSource,assetFields,updateTime,self.sourcePriority,self.bulkClass)	
			
		actionResult["result"] = True
		actionResult["rc"] = 0
		return actionResult
	

class _assetUpdate(action._action):
	assetName = str()
	assetType = str()
	assetEntity = str()
	updateTime = str()
	updateSource = str()
	sourcePriority = int()
	assetFields = dict()
	replaceExisting = bool()
	delayedUpdate = int()
	auditHistory = bool()

	def __init__(self):
		cache.globalCache.newCache("assetCache")
		self.bulkClass = db._bulk()

	def postRun(self,data,persistentData):
		self.bulkClass.bulkOperatonProcessing()

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

		assetItem = cache.globalCache.get("assetCache",match,getAssetObject,assetName,assetType,assetEntity)
		if not assetItem:
			assetItem = asset._asset().bulkNew(self.acl,assetName,assetEntity,assetType,updateSource,assetFields,updateTime,self.sourcePriority,self.bulkClass)
			cache.globalCache.insert("assetCache",match,[assetItem])
			actionResult["result"] = True
			actionResult["msg"] = "Created new asset"
			actionResult["rc"] = 201
			return actionResult

		assetChanged = False
		# Merging and removing entires if more than one result is found
		if len(assetItem) > 1:
			newestItem = assetItem[0]
			for singleAssetItem in assetItem:
				if newestItem.lastUpdateTime < singleAssetItem.lastUpdateTime:
					for key, value in singleAssetItem.lastSeen.items():
						if key not in newestItem.lastSeen:
							newestItem.lastSeen[key] = value
						elif value["lastUpdate"] < newestItem.lastSeen[key]["lastUpdate"]:
							newestItem.lastSeen[key] = value
					singleAssetItem.delete()
				else:
					newestItem.delete()
					newestItem = singleAssetItem
			assetItem = newestItem
			cache.globalCache.update("assetCache",match,[assetItem])
			assetChanged = True
		else:
			assetItem = assetItem[0]

		if assetItem._id == "":
			actionResult["result"] = False
			actionResult["msg"] = "Asset not yet added"
			actionResult["rc"] = 404
			return actionResult

		if updateSource not in assetItem.lastSeen:
			assetItem.lastSeen[updateSource] = {}
		

		newTimestamp = None
		if updateTime:
			try:
				if updateTime < assetItem.lastSeen[updateSource]["lastUpdate"]:
					newTimestamp = False
				else:
					newTimestamp = updateTime
			except (KeyError, ValueError):
				pass
		if newTimestamp == None:
			newTimestamp = time.time()

		if newTimestamp != False:
			try:
				if (time.time() - assetItem.lastSeen[updateSource]["lastUpdate"]) < self.delayedUpdate:
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
				assetItem.lastSeen[updateSource] = assetFields
			else:
				for key, value in assetFields.items():
					assetItem.lastSeen[updateSource][key] = value

			assetItem.lastSeen[updateSource]["priority"] = self.sourcePriority
			assetItem.lastSeen[updateSource]["lastUpdate"] = newTimestamp

		# Working out priority and define fields
		if assetChanged:
			foundValues = {}
			blacklist = ["lastUpdate","priority"]
			for source, sourceValue in assetItem.lastSeen.items():
				for key, value in sourceValue.items():
					if key not in blacklist:
						if key not in foundValues:
							foundValues[key] = { "value" : value, "priority" : sourceValue["priority"] }
						else:
							if sourceValue["priority"] < foundValues[key]["priority"]:
								foundValues[key] = { "value" : value, "priority" : sourceValue["priority"] }
			assetItem.fields = {}
			for key, value in foundValues.items():
				assetItem.fields[key] = value["value"]
			assetItem.bulkUpdate(["lastSeen","fields"],self.bulkClass)
			
			actionResult["result"] = True
			actionResult["msg"] = "Updated asset"
			actionResult["rc"] = 302
			return actionResult

		actionResult["result"] = True
		actionResult["msg"] = "Nothing to do"
		actionResult["rc"] = 304
		return actionResult

def getAssetObject(match,sessionData,assetName,assetType,assetEntity):
	return asset._asset().getAsClass(query={ "name" : assetName, "assetType" : assetType, "entity" : assetEntity })
