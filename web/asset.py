from flask import Blueprint, render_template, make_response, g
from flask import current_app as app

from pathlib import Path
import time, json, csv, io

from plugins.asset.models import asset, relationship

from core import api, helpers, db


pluginPages = Blueprint('assetPages', __name__, template_folder="templates")

@pluginPages.route("/")
def mainAssetPage():
	#assets = asset._asset().getAsClass(api.g.sessionData,query={},fields=["_id","name","type","classID"])
	foundAsset = []
	#for assetObject in assets:
	#    foundAsset.append({ "_id" : assetObject._id, "name" : assetObject.name, "type" : assetObject.assetType, "lastSeen" : assetObject.lastSeen })
	return render_template("asset.html",asset=foundAsset)

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


