from core import plugin, model

class _asset(plugin._plugin):
    version = 0.3

    def install(self):
        # Register models
        model.registerModel("asset","_asset","_asset","plugins.asset.models.asset")
        model.registerModel("assetUpdate","_assetUpdate","_action","plugins.asset.models.action")
        model.registerModel("assetBulkUpdate","_assetBulkUpdate","_action","plugins.asset.models.action")
        model.registerModel("assetSearch","_assetSearch","_action","plugins.asset.models.assetSearch")
        return True

    def uninstall(self):
        # deregister models
        model.deregisterModel("asset","_asset","_asset","plugins.asset.models.asset")
        model.deregisterModel("assetUpdate","_assetUpdate","_action","plugins.asset.models.action")
        model.deregisterModel("assetBulkUpdate","_assetBulkUpdate","_action","plugins.asset.models.action")
        model.deregisterModel("assetSearch","_assetSearch","_action","plugins.asset.models.assetSearch")
        return True
    
    def upgrade(self,LatestPluginVersion):
        if self.version < 0.3:
            model.registerModel("assetBulkUpdate","_assetBulkUpdate","_action","plugins.asset.models.action")
        if self.version < 0.2:
            model.registerModel("assetSearch","_assetSearch","_action","plugins.asset.models.assetSearch")
