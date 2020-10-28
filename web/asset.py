from flask import Blueprint, render_template, make_response, g
from flask import current_app as app

from pathlib import Path
import time, json, csv, io

from plugins.asset.models import asset

from core import api


pluginPages = Blueprint('assetPages', __name__, template_folder="templates")

@pluginPages.route("/asset/")
def mainAssetPage():
    #assets = asset._asset().getAsClass(api.g.sessionData,query={},fields=["_id","name","type","classID"])
    foundAsset = []
    #for assetObject in assets:
    #    foundAsset.append({ "_id" : assetObject._id, "name" : assetObject.name, "type" : assetObject.assetType, "lastSeen" : assetObject.lastSeen })
    return render_template("asset.html",asset=foundAsset)

@pluginPages.route("/asset/src_ip/")
def getAssetIPPage():
    return render_template("relationship.html")

@pluginPages.route("/asset/src_ip/<src_ip>/")
def getAssetByIP(src_ip):
    assets = asset._asset().getAsClass(api.g.sessionData,query={ "fields.src_ip" : src_ip },fields=["_id","name","fields"])
    foundAssets = []
    for assetObject in assets:
        assetUsers = asset._asset().getAsClass(api.g.sessionData,query={ "fields.user" : assetObject.name },fields=["_id","name","fields"])
        for assetUser in assetUsers:
            if "src_ip" in assetUser.fields:
                foundAssets.append([assetObject.name,assetUser.fields["src_ip"]])
        foundAssets.append([src_ip,assetObject.name])
    return { "results" : foundAssets }, 200
