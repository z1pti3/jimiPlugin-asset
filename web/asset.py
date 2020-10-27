from flask import Blueprint, render_template, make_response, g
from flask import current_app as app

from pathlib import Path
import time, json, csv, io

from plugins.asset.models import asset

from core import api


pluginPages = Blueprint('assetPages', __name__, template_folder="templates")

@pluginPages.route("/asset/")
def mainAssetPage():
    assets = asset._asset().getAsClass(api.g["sessionData"],query={},fields=["_id","name","type","lastSeen","classID"])
    foundAsset = []
    for assetObject in assets:
        foundAsset.append({ "_id" : assetObject._id, "name" : assetObject.name, "type" : assetObject.assetType, "lastSeen" : assetObject.lastSeen })
    return render_template("asset.html",asset=foundAsset)
