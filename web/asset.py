from flask import Blueprint, render_template, make_response, g
from flask import current_app as app

from pathlib import Path
import time, json, csv, io

from plugins.asset.models import asset, relationship

from core import api, helpers, db

from web import ui

import jimi


pluginPages = Blueprint('assetPages', __name__, template_folder="templates")

@pluginPages.route("/")
def mainAssetPage():
	return render_template("asset.html",CSRF=jimi.api.g.sessionData["CSRF"])

@pluginPages.route("/assetItem/")
def singleAsset():
	assetName = jimi.api.request.args.get('value')
	assetObject = asset._asset().query(sessionData=api.g.sessionData,query={ "name" : assetName })["results"][0]
	assetDetails = ui.dictTable(assetObject)
	return render_template("assetItem.html",CSRF=jimi.api.g.sessionData["CSRF"],assetDetails=assetDetails)

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
		print(searchValue)
		searchFilter = { "name" : { "$regex" : ".*{0}.*".format(searchValue) } }
	else:
		searchFilter = {}
	pagedData = jimi.db._paged(asset._asset,sessionData=api.g.sessionData,fields=fields,query=searchFilter,maxResults=200)
	table = ui.table(fields,200,pagedData.total)
	if action == "build":
		return table.getColumns() ,200
	elif action == "poll":
		start = int(jimi.api.request.args.get('start'))
		data = pagedData.getOffset(start,queryMode=1)
		table.setRows(data,links=[{ "field" : "name", "url" : "/plugin/asset/" }])
		return table.generate(int(jimi.api.request.args.get('draw'))) ,200

@pluginPages.route("/pie/",methods=["POST"])
def pie():
	pie = ui.pie()
	pie.labels = ['Sophos','AD','FortiClient','Snow','Humio','Glpi']
	pie.addDataset("Assets",[65, 59, 90, 81, 56, 10])
	data = json.loads(jimi.api.request.data)
	return pie.generate(data), 200

@pluginPages.route("/bar/",methods=["POST"])
def bar():
	bar = ui.bar()
	bar.labels = ['Sophos','AD','FortiClient','Snow','Humio','Glpi']
	bar.addDataset("Assets",[65, 59, 90, 81, 56, 10])
	data = json.loads(jimi.api.request.data)
	return bar.generate(data), 200


@pluginPages.route("/line/",methods=["POST"])
def line():
	line = ui.line()
	line.labels = ['Sophos','AD','FortiClient','Snow','Humio','Glpi']
	line.addDataset("Assets",[65, 59, 90, 81, 56, 10])
	data = json.loads(jimi.api.request.data)
	return line.generate(data), 200

@pluginPages.route("/network/",methods=["GET"])
def network():
    nodesDict = { 
		"1" : { "id" : "1", "label" : "1", "value" : 1, "color" : { "background" : "#C72F1E", "border" : "#C72F1E" , "highlight" : { "background" : "#000", "border" : "#FFF" } } },
		"2" : { "id" : "2", "label" : "1", "value" : 1, "color" : { "background" : "#C72F1E", "border" : "#C72F1E" , "highlight" : { "background" : "#000", "border" : "#FFF" } } },
		"3" : { "id" : "3", "label" : "1", "value" : 1, "color" : { "background" : "#C72F1E", "border" : "#C72F1E" , "highlight" : { "background" : "#000", "border" : "#FFF" } } },
		"4" : { "id" : "4", "label" : "1", "value" : 1, "color" : { "background" : "#C72F1E", "border" : "#C72F1E" , "highlight" : { "background" : "#000", "border" : "#FFF" } } },
		"5" : { "id" : "5", "label" : "1", "value" : 1, "color" : { "background" : "#C72F1E", "border" : "#C72F1E" , "highlight" : { "background" : "#000", "border" : "#FFF" } } }
	}
    edgesDict = {
		"1-2" : { "id" : "1-2", "from" : "1", "to" : "2" },
		"1-3" : { "id" : "1-3", "from" : "1", "to" : "3" },
		"3-4" : { "id" : "3-4", "from" : "3", "to" : "4" },
		"4-5" : { "id" : "4-5", "from" : "4", "to" : "5" }
	}
            
    nodes = [ x for x in nodesDict.values() ]
    edges = [ x for x in edgesDict.values() ]

    return { "nodes" : nodes, "edges" : edges }, 200

@pluginPages.route("/timeline/",methods=["GET"])
def timeline():
    timeline = []

    formatted_date = time.strftime('%Y-%m-%d %H:%M:%S',  time.localtime(time.time()))
    timeline.append({ "id" : len(timeline), "content" : "test", "start" : formatted_date })

    return { "timeline" : timeline }, 200