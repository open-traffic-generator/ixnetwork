from pprint import pprint
from abstract_open_traffic_generator.port import Port, OneHundredGbe, Layer1, Fcoe
from abstract_open_traffic_generator.device import DeviceGroup, Device
from abstract_open_traffic_generator.device import Ethernet, Vlan, Ipv4
from abstract_open_traffic_generator.device import Pattern
from abstract_open_traffic_generator.config import Config
from abstract_open_traffic_generator.flow import DeviceEndpoint, Endpoint, Flow, Header, Size, Rate,\
    Duration, Fixed, PortEndpoint, PfcPause, Counter, Random

################################################################################
# COMMENTS
# 1. Some classes defined "abstract_open_traffic_generator.device" and
#    "abstract_open_traffic_generator.flow" has the same name. Like Ipv4, Vlan,
#    Ethernet, Pattern. Different name required.
################################################################################
from abstract_open_traffic_generator.flow import Pattern as PATTERN
from abstract_open_traffic_generator.flow import Ipv4 as IPV4
from abstract_open_traffic_generator.flow import Vlan as VLAN
from abstract_open_traffic_generator.flow import Ethernet as ETHERNET
from abstract_open_traffic_generator.flow_ipv4 import Priority, Dscp
from abstract_open_traffic_generator.request import Port as Request


from ixnetwork_open_traffic_generator.ixnetworkapi import IxNetworkApi


TX_LOCATION = '10.39.34.250;1;1'
RX_LOCATION = '10.39.34.250;1;2'
API_SERVER  = '10.39.32.100'
PORT        = '443'

def run_pfc_pause_lossy_traffic_test(serializer,
                                     api,
                                     phy_tx_port,
                                     phy_rx_port,
                                     port_speed,
                                     tx_port_ip='0.0.0.0',
                                     rx_port_ip='0.0.0.0',
                                     tx_gateway_ip='0.0.0.0',
                                     rx_gateway_ip='0.0.0.',
                                     tx_ip_incr='0.0.0.0',
                                     rx_ip_incr='0.0.0.0',
                                     tx_gateway_incr='0.0.0.0',
                                     rx_gateway_incr='0.0.0.0',
                                     configure_pause_frame=True):
    ########################################################################### 
    # TX port 
    ########################################################################### 
    tx = Port(name='Tx', location=phy_tx_port)

    ########################################################################### 
    # RX port  
    ########################################################################### 
    rx = Port(name='Rx', location=phy_rx_port)

    ########################################################################### 
    # Tx + Rx port commom L1 config
    # COMMENT --> This is not comming up
    # auto_negotiate=False --> is not working.
    # ieee_media_defaults=False is now working --> issue resolved 
    ########################################################################### 
    l1_oneHundredGbe = OneHundredGbe(link_training=True,
                                     ieee_media_defaults=False,
                                     auto_negotiate=False,
                                     speed='one_hundred_gbps',
                                     rs_fec=True)

    fcoe = Fcoe(flow_control_type='ieee_802_1qbb',
        pfc_delay_quanta=3,
        pfc_class_0='zero',
        pfc_class_1='three',
        pfc_class_4='seven')


    common_l1_config = Layer1(name='common L1 config',
                              choice=l1_oneHundredGbe,
                              port_names=[tx.name, rx.name],
                              fcoe=fcoe)

    ########################################################################### 
    # Create TX stack configuration
    ########################################################################### 
    tx_ipv4 = Ipv4(name='Tx Ipv4',
                   address=Pattern(tx_port_ip),
                   prefix=Pattern('24'),
                   gateway=Pattern(tx_gateway_ip))

    tx_ethernet = Ethernet(name='Tx Ethernet', ipv4=tx_ipv4)

    tx_device = Device(name='Tx Device',
                       devices_per_port=1,
                       ethernets=[tx_ethernet])

    tx_device_group = DeviceGroup(name='Tx Device Group',
                                  port_names=[tx.name],
                                  devices=[tx_device])

    ########################################################################### 
    # Create RX stack configuration
    ########################################################################### 
    rx_ipv4 = Ipv4(name='Rx Ipv4',
                   address=Pattern(rx_port_ip),
                   prefix=Pattern('24'),
                   gateway=Pattern(rx_gateway_ip))

    rx_ethernet = Ethernet(name='Rx Ethernet', ipv4=rx_ipv4)

    rx_device = Device(name='Rx Device',
                       devices_per_port=1,
                       ethernets=[rx_ethernet])

    rx_device_group = DeviceGroup(name='Rx Device Group',
                                  port_names=[rx.name],
                                  devices=[rx_device])

    ########################################################################### 
    # Traffic configuration Test data
    # COMMENT --> DSCP values are not getting set
    ########################################################################### 
    data_endpoint = DeviceEndpoint(
        tx_device_names=[tx_device.name],
        rx_device_names=[rx_device.name],
        packet_encap='ipv4',
        src_dst_mesh='',
        route_host_mesh='',
        bi_directional=False,
        allow_self_destined=False
    )

    test_dscp = Priority(Dscp(phb=PATTERN(choice=[0, 1, 2, 5, 6, 7])))

    test_flow = Flow(
        name='Test Data',
        endpoint=Endpoint(data_endpoint),
        packet=[
            Header(choice=ETHERNET()),
            Header(choice=VLAN()),
            Header(choice=IPV4(priority=test_dscp))
        ],
        size=Size(128),
        rate=Rate('line', 50),
        duration=Duration(Fixed(packets=0, delay=1000000000, delay_unit='nanoseconds'))
    )

    ########################################################################### 
    # Traffic configuration Background data
    # COMMENT --> DSCP values are not getting set
    ########################################################################### 
    background_dscp = Priority(Dscp(phb=PATTERN(choice=[3, 4])))
    background_flow = Flow(
        name='Background Data',
        endpoint=Endpoint(data_endpoint),
        packet=[
            Header(choice=ETHERNET()),
            Header(choice=VLAN()),
            Header(choice=IPV4(priority=background_dscp))
        ],
        size=Size(128),
        rate=Rate('line', 50),
        duration=Duration(Fixed(packets=0, delay=1000000000, delay_unit='nanoseconds'))
    )

    ########################################################################### 
    # Traffic configuration Pause
    # COMMENT --> Throwing an error. 
    # ../ixnetwork_open_traffic_generator/trafficitem.py:92: AttributeError 
    # AttributeError: 'Header' object has no attribute 'name'
    ########################################################################### 
    if (configure_pause_frame) :
        pause_endpoint = PortEndpoint(tx_port_name=rx.name)
        pause = Header(PfcPause(
            dst=PATTERN(choice='01:80:C2:00:00:01'),
            src=PATTERN(choice='00:00:fa:ce:fa:ce'),
            class_enable_vector=PATTERN(choice='E7'),
            pause_class_0=PATTERN(choice='ffff'),
            pause_class_1=PATTERN(choice='ffff'),
            pause_class_2=PATTERN(choice='ffff'),
            pause_class_3=PATTERN(choice='0'),
            pause_class_4=PATTERN(choice='0'),
            pause_class_5=PATTERN(choice='ffff'),
            pause_class_6=PATTERN(choice='ffff'),
            pause_class_7=PATTERN(choice='ffff'),
        ))

        pause_flow = Flow(
            name='Pause Storm',
            endpoint=Endpoint(pause_endpoint),
            packet=[pause],
            size=Size(64),
            rate=Rate('line', value=100),
            duration=Duration(Fixed(packets=0, delay=0, delay_unit='nanoseconds'))
        )
        flows = [test_flow, background_flow, pause_flow]
    else :
       flows = [test_flow, background_flow]

    ########################################################################### 
    # Set config 
    # COMMENT: Forced ownership is required. I found that forced ownership
    #          is not happening.
    #
    # COMMENT: I tried to set only L1 config --> auto_negotiate=False
    # But it seems that there is no way to do that. 
    ########################################################################### 
    config = Config(
        ports=[
            tx,
            rx
        ],
        layer1=[common_l1_config],
        device_groups=[tx_device_group, rx_device_group],
        flows=flows
    )
    print(serializer.json(config))
    api.set_config(config)

    request = Request()
    results = api.get_port_results(request)
    #print(results['columns'])
    #for row in results['rows']:
    #    print(row)
    stats = {}
    for name in results['columns']:
        val = []
        col_index = results['columns'].index(name)
        for row in results['rows']:
            val.append(row[col_index])
        stats[name] = val

    pprint(stats)


def test_start_lossy(serializer) :
    tx_location = TX_LOCATION
    rx_location = RX_LOCATION
    tx_speed = 100000
    vlan_ip_addrs = ['192.168.1.2', '192.168.1.3']
    gw_addr = '192.168.1.1'

    api = IxNetworkApi(API_SERVER, port=PORT)
    api.set_config(None)
    config = run_pfc_pause_lossy_traffic_test(
                serializer=serializer,
                api = api,
                phy_tx_port=tx_location,
                phy_rx_port=rx_location,
                port_speed=tx_speed,
                tx_port_ip=vlan_ip_addrs[1],
                rx_port_ip=vlan_ip_addrs[0],
                tx_gateway_ip=gw_addr,
                rx_gateway_ip=gw_addr,
                tx_ip_incr='0.0.0.0',
                rx_ip_incr='0.0.0.0',
                tx_gateway_incr='0.0.0.0',
                rx_gateway_incr='0.0.0.0')
