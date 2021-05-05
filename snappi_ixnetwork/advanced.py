import re
import time

class Advanced(object):
    _LATENCY = {
        'cut_through' : 'cutThrough',
        'store_forward' : 'storeForward'
    }

    _CONVERGENCE = {
        ('data_plane_convergence_ns', 'DP/DP Convergence Time (us)', float),
        ('control_plane_data_plane_convergence_ns', 'CP/DP Convergence Time (us)', float),
    }
    
    _EVENT = {
        ('begin_timestamp_ns', 'Event Start Timestamp', int),
        ('end_timestamp_ns', 'Event End Timestamp', int)
    }
    
    def __init__(self, ixnetworkapi):
        self._api = ixnetworkapi
        self._analytics_timeout = 10
    
    def config(self):
        advanced = getattr(self._api.snappi_config, 'advanced', None)
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
    
    def _set_result_value(self,
                          row,
                          column_name,
                          column_value,
                          column_type=str):
        try:
            row[column_name] = column_type(column_value)
        except:
            if column_type.__name__ in ['float', 'int']:
                row[column_name] = 0
            else:
                row[column_type] = column_value
        
    def _get_flow_rows(self, flow_names):
        count = 0
        sleep_time = 0.5
        flow_stat = self._api.assistant.StatViewAssistant(
            'Flow Statistics')
        while True:
            flow_rows = flow_stat.Rows
            has_event = False
            for row in flow_rows:
                if row['Traffic Item'] in flow_names \
                        and row['Event Name'] != '':
                    has_event = True
                    break
            if has_event is True:
                break
            if count * sleep_time > self._analytics_timeout:
                raise Exception("Somehow event is not reflected in stat")
            time.sleep(sleep_time)
            count += 1
        return flow_rows
    
    def result(self, request):
        flow_names = request._properties.get('flow_names')
        if not isinstance(flow_names, list):
            msg = "Invalid format of flow_names passed {},\
                                        expected list".format(flow_names)
            raise Exception(msg)
        if flow_names is None or len(flow_names) == 0:
            flow_names = [flow.name for flow in self._api.snappi_config.flows]
        flow_rows = self._get_flow_rows(flow_names)
        traffic_stat = self._api.assistant.StatViewAssistant(
            'Traffic Item Statistics')
        traffic_index = {}
        for index, row in enumerate(traffic_stat.Rows):
            traffic_index[row['Traffic Item']] = index
        response = []
        drill_down_options = traffic_stat.DrillDownOptions()
        for flow_name in flow_names:
            convergence = {}
            if flow_name not in traffic_index.keys():
                raise Exception("Somehow flow %s is missing" %flow_name)
            events = []
            interruption_time = None
            for flow_result in flow_rows:
                event = {}
                event_name = flow_result['Event Name']
                if event_name == '' or \
                        flow_result['Traffic Item'] != flow_name:
                    continue
                for route_name in self._api.ixn_route_objects.keys():
                    if re.search(route_name,
                                    event_name) is not None:
                        event['source'] = route_name
                        event_type = event_name.split(route_name)[-1]
                        if event_type.strip().lower() == 'disable':
                            event_type = 'route_withdraw'
                        else:
                            event_type = "route_advertise"
                        event['type'] = event_type
                        break
                for external_name, internal_name, external_type in self._EVENT:
                    value = int(flow_result[internal_name].split('.')[-1])
                    self._set_result_value(event, external_name, value * 1000, external_type)
                events.append(event)
                if interruption_time is None:
                    interruption_time = float(flow_result['DP Above Threshold Timestamp'].split(':')[-1]) - \
                                        float(flow_result['DP Below Threshold Timestamp'].split(':')[-1])
                    self._set_result_value(convergence, 'service_interruption_time_ns',
                                           interruption_time, float)
            convergence['events'] = events

            drill_down_option = 'Drill down per Dest Endpoint'
            if drill_down_option not in drill_down_options:
                raise Exception("Please configure advance setting")
            drilldown_index = drill_down_options.index(drill_down_option)
            drill_down = traffic_stat.Drilldown(traffic_index[flow_name], drill_down_option,
                                               traffic_stat.TargetRowFilters()[drilldown_index])
            drill_down_result = drill_down.Rows[0]
            for external_name, internal_name, external_type in self._CONVERGENCE:
                self._set_result_value(convergence, external_name, drill_down_result[
                    internal_name], external_type)
            response.append({'name' : flow_name,
                             'convergence' : convergence})
        return response