from flask import Blueprint, render_template, make_response, g
from flask import current_app as app

from pathlib import Path
import time, json, csv, io

from plugins.asset.models import asset, relationship

from core import api, helpers, db

import jimi


pluginPages = Blueprint('assetPages', __name__, template_folder="templates")

@pluginPages.route("/")
def mainAssetPage():
	#assets = asset._asset().getAsClass(api.g.sessionData,query={},fields=["_id","name","type","classID"])
	foundAsset = []
	#for assetObject in assets:
	#    foundAsset.append({ "_id" : assetObject._id, "name" : assetObject.name, "type" : assetObject.assetType, "lastSeen" : assetObject.lastSeen })
	return render_template("asset.html",CSRF=jimi.api.g.sessionData["CSRF"])

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

@pluginPages.route("/radar/",methods=["POST"])
def radar():
	result = { "labels" : [], "datasets" : [], "updates" : [], "deletes" : [] }
	data = json.loads(jimi.api.request.data)
	labels = ['Sophos','AD','FortiClient','Snow','Humio','Glpi']
	if labels != data["labels"]:
		result["labels"] = labels
	
	datasets = { 
		"Assets" : {
			"label": 'Assets',
			"data": [65, 59, 90, 81, 56, 10],
			"fill": True,
			"backgroundColor": 'rgba(255, 99, 132, 0.2)',
			"borderColor": 'rgb(255, 99, 132)',
			"pointBackgroundColor": 'rgb(255, 99, 132)'
		}
	}

	for index, value in enumerate(data["datasets"]):
		if value["label"] not in datasets:
			result["deletes"].append({ "index" : index })
		else:
			if value["data"] != datasets[value["label"]]["data"]:
				result["updates"].append({ "index" : index, "data" : datasets[value["label"]]["data"] })
			del datasets[value["label"]]
	
	for dataset in datasets:
		result["datasets"].append(datasets[dataset])

	return result, 200

@pluginPages.route("/doughnut/",methods=["POST"])
def doughnut():
	result = { "labels" : [], "datasets" : [], "updates" : [], "deletes" : [] }
	data = json.loads(jimi.api.request.data)
	labels = ['Sophos','AD','FortiClient','Snow','Humio','Glpi']
	if labels != data["labels"]:
		result["labels"] = labels
	
	datasets = { 
		"OS" : {
				"label": 'OS',
				"data": [65, 59, 90, 81, 56, 55],
				"backgroundColor": ['red',"blue","green","yellow","orange","white"],
		}
	}

	for index, value in enumerate(data["datasets"]):
		if value["label"] not in datasets:
			result["deletes"].append({ "index" : index })
		else:
			if value["data"] != datasets[value["label"]]["data"]:
				result["updates"].append({ "index" : index, "data" : datasets[value["label"]]["data"] })
			del datasets[value["label"]]
	
	for dataset in datasets:
		result["datasets"].append(datasets[dataset])

	return result, 200

@pluginPages.route("/pie/",methods=["POST"])
def pie():
	result = { "labels" : [], "datasets" : [], "updates" : [], "deletes" : [] }
	data = json.loads(jimi.api.request.data)
	labels = ['Sophos','AD','FortiClient','Snow','Humio','Glpi']
	if labels != data["labels"]:
		result["labels"] = labels
	
	datasets = { 
		"OS" : {
				"label": 'OS',
				"data": [65, 59, 90, 81, 56, 55],
				"backgroundColor": ['red',"blue","green","yellow","orange","white"],
		}
	}

	for index, value in enumerate(data["datasets"]):
		if value["label"] not in datasets:
			result["deletes"].append({ "index" : index })
		else:
			if value["data"] != datasets[value["label"]]["data"]:
				result["updates"].append({ "index" : index, "data" : datasets[value["label"]]["data"] })
			del datasets[value["label"]]
	
	for dataset in datasets:
		result["datasets"].append(datasets[dataset])

	return result, 200

@pluginPages.route("/bar/",methods=["POST"])
def bar():
	result = { "labels" : [], "datasets" : [], "updates" : [], "deletes" : [] }
	data = json.loads(jimi.api.request.data)
	labels = ['Sophos','AD','FortiClient','Snow','Humio','Glpi']
	if labels != data["labels"]:
		result["labels"] = labels
	
	datasets = { 
		"OS" : {
				"label": 'OS',
				"data": [65, 59, 90],
				"backgroundColor": ['red'],
		}
	}

	for index, value in enumerate(data["datasets"]):
		if value["label"] not in datasets:
			result["deletes"].append({ "index" : index })
		else:
			if value["data"] != datasets[value["label"]]["data"]:
				result["updates"].append({ "index" : index, "data" : datasets[value["label"]]["data"] })
			del datasets[value["label"]]
	
	for dataset in datasets:
		result["datasets"].append(datasets[dataset])

	return result, 200


@pluginPages.route("/line/",methods=["POST"])
def line():
	result = { "labels" : [], "datasets" : [], "updates" : [], "deletes" : [] }
	data = json.loads(jimi.api.request.data)
	labels = ['Sophos','AD','FortiClient','Snow','Humio','Glpi']
	if labels != data["labels"]:
		result["labels"] = labels
	
	datasets = { 
		"OS" : {
				"label": 'OS',
				"data": [65, 59, 90],
				"backgroundColor": ['red'],
		}
	}

	for index, value in enumerate(data["datasets"]):
		if value["label"] not in datasets:
			result["deletes"].append({ "index" : index })
		else:
			if value["data"] != datasets[value["label"]]["data"]:
				result["updates"].append({ "index" : index, "data" : datasets[value["label"]]["data"] })
			del datasets[value["label"]]
	
	for dataset in datasets:
		result["datasets"].append(datasets[dataset])

	return result, 200