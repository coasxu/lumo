from typing import Union, NoReturn, Dict, overload, TYPE_CHECKING

from torch.utils.data import DataLoader, Dataset
from .builder import DatasetWrap

if TYPE_CHECKING:
    from .trainer import ParamsType


class DataModule():
    def __init__(self, train: DataLoader = None, val: DataLoader = None, test: DataLoader = None):
        self._dataloader = {}
        self.regist_dataloader(train=train, val=val, test=test)

    def __getitem__(self, item):
        return self._dataloader.get(item, None)

    @property
    def dataloaders(self) -> Dict[str, DataLoader]:
        return self._dataloader

    @property
    def train_dataloader(self) -> Union[NoReturn, DataLoader]:
        return self['train']

    @property
    def test_dataloader(self) -> Union[NoReturn, DataLoader]:
        return self['test']

    @property
    def val_dataloader(self) -> Union[NoReturn, DataLoader]:
        return self['val']

    @overload
    def regist_dataloader(self, train: DataLoader = None, val: DataLoader = None, test: DataLoader = None,
                          **others: Dict[str, DataLoader]):
        ...

    def regist_dataloader(self, **kwargs: dict):
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        self._dataloader.update(kwargs)

    def idataloader(self, params: 'ParamsType', stage: str, repeat: bool = False):
        pass

    @classmethod
    def wrap_dataloader(cls, dataset: Dataset) -> DataLoader:
        self = cls()
        self._dataset = dataset
        dataset = DatasetWrap(dataset)
        return DataLoader(dataset, sampler=dataset.sampler)
