from flask import Blueprint, render_template, make_response, g
from flask import current_app as app

from pathlib import Path
import time, json, csv, io

from plugins.asset.models import asset, relationship

from core import api, helpers, db


pluginPages = Blueprint('assetPages', __name__, template_folder="templates")

@pluginPages.route("/asset/")
def mainAssetPage():
    #assets = asset._asset().getAsClass(api.g.sessionData,query={},fields=["_id","name","type","classID"])
    foundAsset = []
    #for assetObject in assets:
    #    foundAsset.append({ "_id" : assetObject._id, "name" : assetObject.name, "type" : assetObject.assetType, "lastSeen" : assetObject.lastSeen })
    return render_template("asset.html",asset=foundAsset)

@pluginPages.route("/asset/relationship/")
def getAssetRelationshipPage():
    return render_template("relationship.html")

@pluginPages.route("/asset/relationship/<fromAsset>/<timespan>/")
def getRelationshipsByTimespan(fromAsset,timespan):
    timespan = helpers.roundTime(roundTo=int(timespan)).timestamp()

    accessIDs = []
    adminBypass = False
    sessionData = api.g.sessionData
    if "admin" in sessionData:
        if sessionData["admin"]:
            adminBypass = True
    if not adminBypass:
        accessIDs = sessionData["accessIDs"]
        match = { "$or" : [ { "acl.ids.accessID" : { "$in" : accessIDs }, "acl.ids.read" : True }, { "acl.fields.ids.accessID" : { "$in" : accessIDs } }, { "acl" : { "$exists" : False } }, { "acl" : {} } ], "timespan" : timespan }
    else:
        match = { "timespan" : timespan, "fromAsset" : fromAsset }
    
    if fromAsset == "":
        del match["fromAsset"]

    relationships = relationship._assetRelationship()._dbCollection.aggregate([ 
        {
            "$match" : match
        },
        { 
            "$graphLookup" : 
            { 
                "from" : "assetRelationship",
                "startWith" : "$fromAsset",
                "connectFromField" : "fromAsset",
                "connectToField" : "toAsset",
                "as" : "relationships"
            }
        }
    ])

    graph = []
    for relationshipItem in relationships:
        graph.append([relationshipItem["fromAsset"],relationshipItem["toAsset"]])
        for relationshipItemRelationship in relationshipItem["relationships"]:
            graph.append([relationshipItemRelationship["fromAsset"],relationshipItemRelationship["toAsset"]])
    return { "results" : graph }, 200


