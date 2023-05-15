from rudi_node_write.utils.date import time_epoch_s, time_epoch_ms


def test_now_epoch_s():
    now_s = time_epoch_s()
    # print(now_s)
    assert (2683040158 > now_s > 1683040158)
    assert (2683040158 > time_epoch_s(10) > 1683040158)


def test_now_epoch_ms():
    now_ms = time_epoch_ms()
    # print(now_ms)
    assert (21683040158094 > now_ms > 1683040158094)
    assert (21683040158094 > time_epoch_ms(10) > 1683040158094)
