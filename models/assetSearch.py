import json

from core.models import action, trigger
from core import helpers, function, logging, cache, db
from plugins.asset.models import asset


class _assetSearch(action._action):
	search = dict()
	fields = list()
	flattenFields = list()
	dontCache = bool()

	def __init__(self):
		cache.globalCache.newCache("assetSearchCache")

	def run(self,data,persistentData,actionResult):
		search = helpers.evalDict(self.search,{"data" : data})
		match = ""
		for key, value in search.items():
			match += key
			if type(value) == str:
				match += value

		if not self.dontCache:
			assetList = cache.globalCache.get("assetSearchCache",match,getSearchObject,search,self.fields)
		else:
			assetList = asset._asset().query(query=search,fields=self.fields)["results"]

		actionResult["events"] = []
		if assetList is not None:
			for assetItem in assetList:
				if len(self.flattenFields) > 0:
					for flattenField in self.flattenFields:
						if flattenField in assetItem["fields"]:
							assetItem[flattenField] = assetItem["fields"][flattenField]
							del assetItem["fields"][flattenField]
				actionResult["events"].append(assetItem)
		actionResult["result"] = True
		actionResult["rc"] = 0
		return actionResult

	def setAttribute(self,attr,value,sessionData=None):
		if not sessionData or db.fieldACLAccess(sessionData,self.acl,attr,accessType="write"):
			if attr == "search":
				value = helpers.unicodeEscapeDict(value)
		return super(_assetSearch, self).setAttribute(attr,value,sessionData=sessionData)

def getSearchObject(match,sessionData,search,fields):
	return asset._asset().query(query=search,fields=fields)["results"]
