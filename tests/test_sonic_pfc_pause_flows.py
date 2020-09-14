import pytest
from abstract_open_traffic_generator.flow import *
from abstract_open_traffic_generator.flow_ipv4 import *
from abstract_open_traffic_generator.config import *
from abstract_open_traffic_generator.control import FlowTransmit
from abstract_open_traffic_generator.result import PortRequest, FlowRequest


def test_sonic_pfc_pause_flows(serializer, tx_port, rx_port, b2b_ipv4_device_groups, api):
    """Pfc pause lossless test traffic configuration
    """
    data_endpoint = DeviceEndpoint(tx_device_names=[b2b_ipv4_device_groups[0].name],
        rx_device_names=[b2b_ipv4_device_groups[1].name],
        packet_encap='ipv4',
        src_dst_mesh='',
        route_host_mesh='',
        bi_directional=False,
        allow_self_destined=False)

    test_dscp = Priority(Dscp(phb=Pattern(Dscp.PHB_CS7, ingress_result_name='phb')))
    test_flow = Flow(name='Test Data',
        endpoint=Endpoint(data_endpoint),
        packet=[
            Header(Ethernet()), 
            Header(Vlan()), 
            Header(Ipv4(priority=test_dscp))
        ],
        size=Size(128),
        rate=Rate('line', 50),
        duration=Duration(Fixed(packets=0)))

    background_dscp = Priority(Dscp(phb=Pattern(Dscp.PHB_CS1)))
    background_flow = Flow(name='Background Data',
        endpoint=Endpoint(data_endpoint),
        packet=[
            Header(Ethernet()), 
            Header(Vlan()), 
            Header(Ipv4(priority=background_dscp))
        ],
        size=Size(128),
        rate=Rate('line', 50),
        duration=Duration(Fixed(packets=0)))

    pause_endpoint = PortEndpoint(tx_port_name=tx_port.name,
        rx_port_names=[rx_port.name])
    pause = Header(PfcPause(
        dst=Pattern('01:80:C2:00:00:01'),
        src=Pattern('00:00:fa:ce:fa:ce'),
        class_enable_vector=Pattern('1'),
        pause_class_0=Pattern('3', ingress_result_name='pfc class 0'),
        pause_class_1=Pattern(Counter(start='2', step='6', count=99), ingress_result_name='pfc1'),
        pause_class_2=Pattern(Counter(start='1', step='6', count=99, up=False)),
        pause_class_3=Pattern(['6', '9', '2', '39']),
        pause_class_4=Pattern(Random(min='11', max='33', step=1, seed='4', count=10))
    ))
    pause_flow = Flow(name='Pause Storm',
        endpoint=Endpoint(pause_endpoint),
        packet=[pause],
        size=Size(64),
        rate=Rate('line', value=100),
        duration=Duration(Fixed(packets=0)))

    config = Config(
        ports=[
            tx_port, 
            rx_port
        ], 
        device_groups=b2b_ipv4_device_groups,
        flows = [
            test_flow,
            background_flow,
            pause_flow
        ]
    )
    print(serializer.json(config))

    api.set_config(None)
    api.set_config(config)
    
    # start flows
    api.set_flow_transmit(FlowTransmit(flow_names=[], state='start'))
    import time
    time.sleep(10)
    
    # get port results
    request = PortRequest()
    results = api.get_port_results(request)
    print(results['columns'])
    for row in results['rows']:
        print(row)
    
    # stop flows
    api.set_flow_transmit(FlowTransmit(flow_names=[], state='stop'))
    time.sleep(10)

    # get flow results
    results = api.get_flow_results(FlowRequest(flow_names=['Test Data']))
    print(results['columns'])
    for row in results['rows']:
        print(row)


if __name__ == '__main__':
    pytest.main(['-s', __file__])
