from abstract_open_traffic_generator.config import *
from abstract_open_traffic_generator.layer1 import *
from abstract_open_traffic_generator.control import *


def test_layer1_flow_control_8023x(api, tx_port, rx_port, options, utils):
    """
    Test that layer1 flow controle 8023x configuration settings
    are being applied correctly.

    Validation: Validate the layer1 properties applied using Restpy
    """

    directed_address = '01 80 C2 00 00 01'

    enabled_pfc = Ieee8023x()
    fcoe1 = Layer1(name='pfc delay-1',
                   port_names=[tx_port.name],
                   speed=utils.settings.speed,
                   auto_negotiate=True,
                   media='fiber',
                   flow_control=FlowControl(directed_address=directed_address,
                                            choice=enabled_pfc))

    fcoe2 = Layer1(name='pfc delay-2',
                   port_names=[rx_port.name],
                   auto_negotiate=True,
                   speed=utils.settings.speed,
                   media='fiber',
                   flow_control=FlowControl(directed_address=directed_address,
                                            choice=enabled_pfc))

    config = Config(ports=[tx_port, rx_port],
                    layer1=[fcoe1, fcoe2],
                    options=options)
    api.set_state(State(ConfigState(config=config, state='set')))
    validate_8023x_config(api,
                          directed_address)


def validate_8023x_config(api,
                          directed_address):
    """
    Validate 8023x config using Restpy
    """
    ixnetwork = api._ixnetwork
    port1 = ixnetwork.Vport.find()[0]
    port2 = ixnetwork.Vport.find()[1]
    type = port1.Type.replace('Fcoe', '')
    type = type[0].upper() + type[1:]
    port1_type = eval('port1.L1Config.' + type)
    port1_fcoe = (eval('port1.L1Config.' + type + '.Fcoe'))
    port2_fcoe = (eval('port2.L1Config.' + type + '.Fcoe'))
    assert port1_type.FlowControlDirectedAddress == directed_address
    assert port1_fcoe.FlowControlType == 'ieee802.3x'
    assert port2_fcoe.FlowControlType == 'ieee802.3x'
