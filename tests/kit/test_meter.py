from lumo import AvgItem
import torch
import numpy as np


def test_avgitem():
    item = AvgItem(0, 'slide')
    for i in range(200):
        item.update(i)
    assert item.res == np.mean(range(200)[-AvgItem.SLIDE_WINDOW_SIZE:], dtype=np.float).item()

    item = AvgItem([1, 2, 3], 'last')
    for i in range(4):
        res = [j for j in range(i)]
        item.update(res)
        assert item.res == res

    rand = [np.random.rand(4) for i in range(4)]
    avg = AvgItem(rand[0], 'sum')
    assert (avg.res == rand[0]).all()
    for i, r in enumerate(rand[1:]):
        if i > 2:
            avg.update(r)
        else:
            avg.update(torch.tensor(r))
        assert (avg.res == np.stack(rand[:i + 2]).sum(axis=0)).all()

    rand = [torch.rand(4) for i in range(4)]

    avg = AvgItem(rand[0], 'mean')
    assert (avg.res == rand[0].numpy()).all()
    for i, r in enumerate(rand[1:]):
        if i > 2:
            avg.update(r)
        else:
            avg.update(np.array(r))
        # print(torch.stack(rand[:i + 1]))
        assert (avg.res == torch.stack(rand[:i + 2]).mean(dim=0).numpy()).all()

    try:
        avg = AvgItem(rand[0], 'max')
        avg = AvgItem(rand[0], 'min')
        assert False
    except:
        assert True

    avg = AvgItem(0, 'max')
    for i in range(10):
        avg.update(torch.tensor(i))
    assert avg.res == i

    avg = AvgItem(torch.tensor(10), 'min')
    for i in reversed(range(10)):
        if i > 5:
            avg.update(i)
        else:
            avg.update(np.array(i))
    assert avg.res == i


def test_avgmeter():
    pass


def test_meter():
    pass
