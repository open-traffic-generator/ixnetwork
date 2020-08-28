import json


class Vport(object):
    """Vport configuration

    Args
    ----
    - ixnetworkapi (IxNetworkApi): instance of the ixnetworkapi class
    """
    def __init__(self, ixnetworkapi):
        self._api = ixnetworkapi
        
    def config(self):
        """Configure config.ports onto Ixnetwork.Vport
        
        CRUD
        ----
        - DELETE any Ixnetwork.Vport.Name that does not exist in config.ports
        - CREATE vport for any config.ports[*].name that does not exist
        - UPDATE vport for any config.ports[*].name that does exist
        """
        vports = self._api.assistant.Ixnetwork.Vport
        for vport in vports.find():
            if self._api.find_item(self._api.config.ports, 'name', vport.Name) is None:
                vport.remove()
        vports.find()

        for port in self._api.config.ports:
            args = {
                'Name': port.name
            }
            vport = self._api.find_item(vports, 'Name', port.name)
            if vport is None:
                vports.add(**args)
            else:
                vport.update(**args)

    def state(self):
        """Set state of config.ports onto Ixnetwork.Vport
        """
        resource_manager = self._api.assistant.Ixnetwork.ResourceManager
        vports = json.loads(resource_manager.ExportConfig(['/vport'], True, 'json'))
        for port in self._api.config.ports:
            vport = parse("$.vport[?(@.name='%s')]" % port.name).find(vports)
            vport.location = port.location
        resource_manager.ImportConfig(json.dumps(vports), False)