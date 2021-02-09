import json

from core.models import action, trigger
from core import helpers, function, logging, cache, db
from plugins.asset.models import asset


class _assetSearch(action._action):
	search = dict()
	fields = list()
	flattenFields = list()
	return_one = bool()
	cache = bool()

	def __init__(self):
		cache.globalCache.newCache("assetSearchCache")

	def run(self,data,persistentData,actionResult):
		latestTime = 0
		search = helpers.evalDict(self.search,{"data" : data})
		match = ""
		for key, value in search.items():
			match += key
			if type(value) == str:
				match += value

		if not self.cache:
			# cache does not support nested dicts as these will always be seen as the same
			assetList = cache.globalCache.get("assetSearchCache",match,getSearchObject,search,self.fields)
		else:
			assetList = asset._asset().query(query=search,fields=self.fields)["results"]

		if self.return_one:
			actionResult["event"] = ""
		else:
			actionResult["events"] = []
		if assetList is not None:
			for assetItem in assetList:
				if len(self.flattenFields) > 0:
					for flattenField in self.flattenFields:
						if flattenField in assetItem["fields"]:
							assetItem[flattenField] = assetItem["fields"][flattenField]
							del assetItem["fields"][flattenField]
				if self.return_one:
					if assetItem["lastUpdateTime"] > latestTime:
						actionResult["event"] = assetItem
				else:
					actionResult["events"].append(assetItem)
		actionResult["result"] = True
		actionResult["rc"] = 0
		return actionResult

	def setAttribute(self,attr,value,sessionData=None):
		if not sessionData or db.fieldACLAccess(sessionData,self.acl,attr,accessType="write"):
			if attr == "search":
				value = helpers.unicodeEscapeDict(value)
		return super(_assetSearch, self).setAttribute(attr,value,sessionData=sessionData)


class _assetSearchTrigger(trigger._trigger):
	search = dict()
	fields = list()
	flattenFields = list()
	return_one = bool()
	cache = bool()

	def __init__(self):
		cache.globalCache.newCache("assetSearchCache")

	def check(self):
		latestTime = 0
		search = helpers.evalDict(self.search,{"data" : {}})
		match = ""
		for key, value in search.items():
			match += key
			if type(value) == str:
				match += value

		if not self.cache:
			# cache does not support nested dicts as these will always be seen as the same
			assetList = cache.globalCache.get("assetSearchCache",match,getSearchObject,search,self.fields)
		else:
			assetList = asset._asset().query(query=search,fields=self.fields)["results"]
			
		if assetList is not None:
			for assetItem in assetList:
				if len(self.flattenFields) > 0:
					for flattenField in self.flattenFields:
						if flattenField in assetItem["fields"]:
							assetItem[flattenField] = assetItem["fields"][flattenField]
							del assetItem["fields"][flattenField]
				if self.return_one:
					if "event" in self.result:
						if self.result["event"]["lastUpdateTime"] > latestTime:
							self.result["event"] = assetItem
					else:
						self.result["event"] = asset
				else:
					self.result["events"].append(asset)

	def setAttribute(self,attr,value,sessionData=None):
		if not sessionData or db.fieldACLAccess(sessionData,self.acl,attr,accessType="write"):
			if attr == "search":
				value = helpers.unicodeEscapeDict(value)
		return super(_assetSearchTrigger, self).setAttribute(attr,value,sessionData=sessionData)

def getSearchObject(match,sessionData,search,fields):
	return asset._asset().query(query=search,fields=fields)["results"]