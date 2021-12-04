from flask import Blueprint, render_template, make_response, g
from flask import current_app as app

from pathlib import Path
import time, json, csv, io, datetime

from plugins.asset.models import asset, relationship

from core import api, helpers, db

from web import ui

import jimi


pluginPages = Blueprint('assetPages', __name__, template_folder="templates")

@pluginPages.app_template_filter('from_timestamp')
def fromTimestamp(value, format="%d/%m/%Y %H:%M:%S"):
	dt = datetime.datetime.fromtimestamp(value)
	if value is None:
		return ""
	return dt.strftime(format)

@pluginPages.app_template_filter('ui_safe')
def uiSafe(value):
	return ui.safe(value)

# Home Page

@pluginPages.route("/")
def mainAssetPage():
	return render_template("asset.html",CSRF=jimi.api.g.sessionData["CSRF"])

@pluginPages.route("/radarSources/",methods=["POST"])
def radarSources():
	radar = ui.radar()
	sources = asset._asset().groupby(sessionData=api.g.sessionData,field="lastSeen.source")
	data = {}
	for source in sources:
		for _id in source["_id"]:
			if _id not in data:
				data[_id] = 0
			data[_id] += source["_count"]
	dataPoints = []
	for key, value in data.items():
		radar.addLabel(key)
		dataPoints.append(value)
	radar.addDataset("Assets",dataPoints)
	data = json.loads(jimi.api.request.data)
	return radar.generate(data), 200

@pluginPages.route("/doughnutEntity/",methods=["POST"])
def doughnutEntity():
	doughnut = ui.doughnut()
	entities = asset._asset().groupby(sessionData=api.g.sessionData,field="entity")
	data = []
	for entity in entities:
		doughnut.addLabel(entity["_id"])
		data.append(entity["_count"])
	doughnut.addDataset("Assets",data)
	data = json.loads(jimi.api.request.data)
	return doughnut.generate(data), 200

@pluginPages.route("/lineCreated/",methods=["POST"])
def lineCreated():
	line = ui.line()
	aggregateStatement = [
		{
			"$match" : {
				"creationTime" : { "$gt" : time.time() - (86400 * 365) }
			}
		},
		{
			"$project" : {
				"_id" : 0,
				"date" : { "$toDate" : "$_id" }
			}
		},
		{
			"$group" : {
				"_id" : { "$month" : "$date" },
				"_count" : { "$sum" : 1 }
			}
		},
		{
			"$sort" : {
				"_id" : 1
			}
		}
	]
	timeline = asset._asset().aggregate(sessionData=api.g.sessionData,aggregateStatement=aggregateStatement)
	data = []
	for item in timeline:
		line.addLabel(item["_id"])
		data.append(item["_count"])
	line.addDataset("Assets",data)
	data = json.loads(jimi.api.request.data)
	return line.generate(data), 200

@pluginPages.route("/tableAssetList/<action>/",methods=["GET"])
def table(action):
	fields = [ "name", "entity", "assetType" ]
	searchValue = jimi.api.request.args.get('search[value]')
	if searchValue:
		searchValue = jimi.helpers.typeCast(searchValue)
		if type(searchValue) is dict:
			searchFilter = searchValue
		else:
			searchFilter = { "$or" : [ 
				{ "name" : { "$regex" : ".*{0}.*".format(searchValue), "$options":"i" } },
				{ "entity" : { "$regex" : ".*{0}.*".format(searchValue), "$options":"i" } },
				{ "assetType" : { "$regex" : ".*{0}.*".format(searchValue), "$options":"i" } },
				{ "fields.ip" : { "$regex" : ".*{0}.*".format(searchValue) } }
			] }
	else:
		searchFilter = {}
	pagedData = jimi.db._paged(asset._asset,sessionData=api.g.sessionData,fields=fields,query=searchFilter,maxResults=200)
	table = ui.table(fields,200,pagedData.total)
	if action == "build":
		return table.getColumns() ,200
	elif action == "poll":
		start = int(jimi.api.request.args.get('start'))
		data = pagedData.getOffset(start,queryMode=1)
		table.setRows(data,links=[{ "field" : "name", "url" : "/plugin/asset/assetItem/", "fieldValue" : "_id" },{ "field" : "assetType", "url" : "/plugin/asset/assetType/", "fieldValue" : "assetType" },{ "field" : "assetType", "url" : "/plugin/asset/assetItem/", "fieldValue" : "assetType" }])
		return table.generate(int(jimi.api.request.args.get('draw'))) ,200

# Asset Item

@pluginPages.route("/assetItem/<assetID>/")
def singleAsset(assetID):
	assetObject = asset._asset().getAsClass(sessionData=api.g.sessionData,id=assetID)[0]
	assetSources = []
	for source in assetObject.lastSeen:
		assetSources.append(source["source"])
	assetSources = ", ".join(assetSources)
	return render_template("assetItem.html",CSRF=jimi.api.g.sessionData["CSRF"],assetObject=assetObject,assetSources=assetSources)


@pluginPages.route("/assetItem/<assetID>/tableFields/<action>/")
def singleAssetTableFields(assetID,action):
	assetObject = asset._asset().getAsClass(sessionData=api.g.sessionData,id=assetID)[0]
	total = len(assetObject.fields)
	columns = ["Field","Value"]
	table = ui.table(columns,total,total)
	if action == "build":
		return table.getColumns() ,200
	elif action == "poll":
		# Custom table data so it can be vertical
		data = []
		for k,v in assetObject.fields.items():
			data.append([ui.safe(k),ui.safe(v)])
		table.data = data
		return { "draw" : int(jimi.api.request.args.get('draw')), "recordsTable" : 0, "recordsFiltered" : 0, "recordsTotal" : 0, "data" : data } ,200


@pluginPages.route("/assetItem/<assetID>/tableFieldsSources/<action>/")
def singleAssetTableFieldsSources(assetID,action):
	assetObject = asset._asset().getAsClass(sessionData=api.g.sessionData,id=assetID)[0]
	total = len(assetObject.fields)
	columns = ["Source","Fields"]
	table = ui.table(columns,total,total)
	if action == "build":
		return table.getColumns() ,200
	elif action == "poll":
		# Custom table data so it can be vertical
		data = []
		for source in assetObject.lastSeen:
			data.append([ui.safe(source["source"]),ui.dictTable(source)])
		table.data = data
		return { "draw" : int(jimi.api.request.args.get('draw')), "recordsTable" : 0, "recordsFiltered" : 0, "recordsTotal" : 0, "data" : data } ,200


@pluginPages.route("/assetItem/<assetID>/networkRelationships/",methods=["GET"])
def singleAssetNetworkRelationships(assetID):
	assetObject = asset._asset().getAsClass(sessionData=api.g.sessionData,id=assetID)[0]
	timespan = helpers.roundTime(roundTo=int("86400")).timestamp()
	relationships = relationship._assetRelationship().getAsClass(sessionData=api.g.sessionData,query={ "timespan" : timespan, "$or" : [ { "fromAsset" : assetObject.fields["ip"] },{ "toAsset" : assetObject.fields["ip"] } ] })

	nodesDict = {}
	edgesDict = {}
	for relationshipItem in relationships:
		if relationshipItem.fromAsset not in nodesDict:
			nodesDict[relationshipItem.fromAsset] = { "id" : relationshipItem.fromAsset, "label" : relationshipItem.fromAsset, "shape" : "image", "image" : "/static/img/computer.svg", "value" : 1, "color" : { "background" : "#C72F1E", "border" : "#C72F1E" , "highlight" : { "background" : "#000", "border" : "#FFF" } } }
		if relationshipItem.toAsset not in nodesDict:
			nodesDict[relationshipItem.toAsset] = { "id" : relationshipItem.toAsset, "label" : relationshipItem.toAsset, "shape" : "image", "image" : "/static/img/computer.svg", "value" : 1, "color" : { "background" : "#C72F1E", "border" : "#C72F1E" , "highlight" : { "background" : "#000", "border" : "#FFF" } } }
		key = "{0}-{1}".format(relationshipItem.fromAsset,relationshipItem.toAsset)
		if key not in edgesDict:
			edgesDict[key] = { "id" : key, "from" : relationshipItem.fromAsset, "to" : relationshipItem.toAsset }
			
	nodes = [ x for x in nodesDict.values() ]
	edges = [ x for x in edgesDict.values() ]
	return { "nodes" : nodes, "edges" : edges }, 200


# Asset Type

@pluginPages.route("/assetType/<assetType>/")
def assetType(assetType):
	if assetType == "computer":
		return render_template("assetType_computer.html",CSRF=jimi.api.g.sessionData["CSRF"])
	else:
		return {}, 200

# Old Stuff

@pluginPages.route("/relationship/")
def getAssetRelationshipPage():
	return render_template("relationship.html")

@pluginPages.route("/relationship/<fromAsset>/<timespan>/")
def getRelationshipsByTimespan(fromAsset,timespan):
	timespan = helpers.roundTime(roundTo=int(timespan)).timestamp()

	relationships = relationship._assetRelationship().getAsClass(sessionData=api.g.sessionData,query={ "timespan" : timespan, "$or" : [ { "fromAsset" : fromAsset },{ "toAsset" : fromAsset } ] })
	graph = []
	for relationshipItem in relationships:
		graph.append([relationshipItem.fromAsset,relationshipItem.toAsset])

	return { "results" : graph }, 200

@pluginPages.route("/timeline/",methods=["GET"])
def timeline():
    timeline = []

    formatted_date = time.strftime('%Y-%m-%d %H:%M:%S',  time.localtime(time.time()))
    timeline.append({ "id" : len(timeline), "content" : "test", "start" : formatted_date })

    return { "timeline" : timeline }, 200