from core import plugin, model

class _asset(plugin._plugin):
    version = 0.8

    def install(self):
        # Register models
        model.registerModel("asset","_asset","_document","plugins.asset.models.asset")
        model.registerModel("assetUpdate","_assetUpdate","_action","plugins.asset.models.action")
        model.registerModel("assetBulkUpdate","_assetBulkUpdate","_action","plugins.asset.models.action")
        model.registerModel("assetSearch","_assetSearch","_action","plugins.asset.models.assetSearch")
        model.registerModel("assetSearchTrigger","_assetSearchTrigger","_action","plugins.asset.models.assetSearch")
        model.registerModel("assetRelationship","_assetRelationship","_document","plugins.asset.models.relationship")
        model.registerModel("assetRelationshipUpdate","_assetRelationshipUpdate","_action","plugins.asset.models.relationship")
        model.registerModel("assetRelationshipBulkUpdate","_assetRelationshipBulkUpdate","_action","plugins.asset.models.relationship")
        model.registerModel("assetMatch","_assetMatch","_action","plugins.asset.models.assetSearch")
        model.registerModel("assetProcess","_assetProcess","_action","plugins.asset.models.action")
        return True

    def uninstall(self):
        # deregister models
        model.deregisterModel("asset","_asset","_document","plugins.asset.models.asset")
        model.deregisterModel("assetUpdate","_assetUpdate","_action","plugins.asset.models.action")
        model.deregisterModel("assetBulkUpdate","_assetBulkUpdate","_action","plugins.asset.models.action")
        model.deregisterModel("assetSearch","_assetSearch","_action","plugins.asset.models.assetSearch")
        model.deregisterModel("assetSearchTrigger","_assetSearchTrigger","_action","plugins.asset.models.assetSearch")
        model.deregisterModel("assetRelationship","_assetRelationship","_document","plugins.asset.models.relationship")
        model.deregisterModel("assetRelationshipUpdate","_assetRelationshipUpdate","_action","plugins.asset.models.relationship")
        model.deregisterModel("assetRelationshipBulkUpdate","_assetRelationshipBulkUpdate","_action","plugins.asset.models.relationship")
        model.deregisterModel("assetMatch","_assetMatch","_action","plugins.asset.models.assetSearch")
        model.deregisterModel("assetProcess","_assetProcess","_action","plugins.asset.models.action")
        return True
    
    def upgrade(self,LatestPluginVersion):
        if self.version < 0.6:
            model.registerModel("assetSearchTrigger","_assetSearchTrigger","_action","plugins.asset.models.assetSearch")
        if self.version < 0.5:
            model.registerModel("assetRelationshipBulkUpdate","_assetRelationshipBulkUpdate","_action","plugins.asset.models.relationship")
        if self.version < 0.4:
            model.registerModel("assetRelationship","_assetRelationship","_document","plugins.asset.models.relationship")
            model.registerModel("assetRelationshipUpdate","_assetRelationshipUpdate","_action","plugins.asset.models.relationship")
        if self.version < 0.3:
            model.registerModel("assetBulkUpdate","_assetBulkUpdate","_action","plugins.asset.models.action")
        if self.version < 0.2:
            model.registerModel("assetSearch","_assetSearch","_action","plugins.asset.models.assetSearch")
        if self.version < 0.7:
            model.registerModel("assetMatch","_assetMatch","_action","plugins.asset.models.assetSearch")
        if self.version < 0.8:
            model.registerModel("assetProcess","_assetProcess","_action","plugins.asset.models.action")
        return True
