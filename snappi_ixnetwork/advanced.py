

class Advanced(object):
    _LATENCY = {
        'cut_through' : 'cutThrough',
        'store_forward' : 'storeForward'
    }
    
    def __init__(self, ixnetworkapi):
        self._api = ixnetworkapi
    
    def config(self):
        advanced = self._api.snappi_config.advanced
        if advanced is None:
            return
        latency =advanced.latency
        has_latency = False
        ixn_latency = self._api._traffic.Statistics.Latency
        if latency is not None:
            if latency.enable is True:
                has_latency = True
                ixn_latency.Enabled = True
                ixn_latency.Mode = Advanced._LATENCY[
                            latency.mode]
        if has_latency is False:
            ixn_latency.Enabled = False
        
        event = advanced.event
        if event is not None and event.enable \
                is True:
            ixn_CpdpConvergence = self._api._traffic.Statistics.CpdpConvergence
            if event.rx_rate_threshold is not None and \
                    event.rx_rate_threshold.enable is True:
                if has_latency is True:
                    raise Exception("We are supporting either latency or rx_rate_threshold")
                ixn_CpdpConvergence.Enabled = True
                ixn_CpdpConvergence.EnableControlPlaneEvents = True
                ixn_CpdpConvergence.EnableDataPlaneEventsRateMonitor = True
                if event.rx_rate_threshold.threshold is not None:
                    ixn_CpdpConvergence.DataPlaneThreshold = event.rx_rate_threshold.threshold
            else:
                ixn_CpdpConvergence.Enabled = False

        convergence = advanced.convergence
        if convergence is not None:
            if convergence.enable is True:
                for ixn_traffic_item in self._api._traffic_item.find():
                    ixn_traffic_item.Tracking.find()[0].TrackBy = ['destEndpoint0',
                                                                   'destSessionDescription0']
    
    def result(self, request):
        flow_names = request._properties.get('flow_names')
        if not isinstance(flow_names, list):
            msg = "Invalid format of flow_names passed {},\
                                        expected list".format(flow_names)
            raise Exception(msg)
        if flow_names is None or len(flow_names) == 0:
            flow_names = [flow.name for flow in self._api.snappi_config.flows]
        