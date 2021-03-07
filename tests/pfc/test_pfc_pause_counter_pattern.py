import pytest

@pytest.mark.skip(reason="Temporary skip for this branch")
def test_counter_pfc_pause(api, b2b_raw_config, utils):
    """
    Configure a pfc pause header fields,
    - with counter pattern

    Validate,
    - Fetch the pfc pause header config via restpy and validate
    against expected
    """
    f = b2b_raw_config.flows[0]
    f.name = 'pfcpause'
    f.size.fixed = 100

    f.packet.pfcpause()
    pfc = f.packet[0]

    pfc.src.increment.start = '00:AB:BC:AB:BC:AB'
    pfc.src.increment.step = '00:01:00:00:01:00'
    pfc.src.increment.count = 10
    pfc.dst.increment.start = '00:AB:BC:AB:BC:AB'
    pfc.dst.increment.step = '00:01:00:00:01:00'
    pfc.dst.increment.count = 10
    pfc.ether_type.increment.start = '8100'
    pfc.ether_type.increment.step = 1
    pfc.ether_type.increment.count = 10
    pfc.class_enable_vector.increment.start = 'FF'
    pfc.class_enable_vector.increment.step = 1
    pfc.class_enable_vector.increment.count = 10
    pfc.control_op_code.value = '101'

    for i in range(8):
        cl = getattr(pfc, 'pause_class_{}'.format(i))
        cl.increment.start = 'FFFF'
        cl.increment.step = 1
        cl.increment.count = 10

    api.set_config(b2b_raw_config)
    attrs = {
        'Destination address': (
            '00:AB:BC:AB:BC:AB'.lower(),
            '00:01:00:00:01:00', '10'
        ),
        'Source address': (
            '00:AB:BC:AB:BC:AB'.lower(),
            '00:01:00:00:01:00', '10'
        ),
        'Ethertype': ('8100', '1', '10'),
        'Control opcode': '101',
        'priority_enable_vector': ('ff', '1', '10'),
        'PFC Queue 0': ('ffff', '1', '10'),
        'PFC Queue 1': ('ffff', '1', '10'),
        'PFC Queue 2': ('ffff', '1', '10'),
        'PFC Queue 3': ('ffff', '1', '10'),
        'PFC Queue 4': ('ffff', '1', '10'),
        'PFC Queue 5': ('ffff', '1', '10'),
        'PFC Queue 6': ('ffff', '1', '10'),
        'PFC Queue 7': ('ffff', '1', '10'),
    }

    utils.validate_config(api, 0, **attrs)

    pfc.pause_class_7.increment.start = '3333'

    api.set_config(b2b_raw_config)

    attrs['PFC Queue 7'] = ('3333', '1', '10')
    utils.validate_config(api, 0, **attrs)

import pytest
if __name__ == '__main__':
    pytest.main(['-s', __file__])