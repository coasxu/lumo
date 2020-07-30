from thexp import Trainer
from trainers import GlobalParams
from thexp.torch.data import splits
from thexp import DatasetBuilder

from data.transforms import ToTensor
from data.dataxy import datasets

toTensor = ToTensor()


class DatasetMixin(Trainer):
    def datasets(self, params: GlobalParams):
        raise NotImplementedError()


class BaseDatasetMixin(DatasetMixin):
    """基本的有监督图片数据集"""

    def datasets(self, params: GlobalParams):
        dataset_fn = datasets[params.dataset]

        test_x, testy = dataset_fn(False)
        train_x, train_y = dataset_fn(True)

        train_idx, val_idx = splits.train_val_split(train_y)

        test_dataloader = (
            DatasetBuilder(test_x, testy).add_x(transform=toTensor).add_y()
                .DataLoader(batch_size=params.batch_size, num_workers=4)
        )

        train_dataloader = (
            DatasetBuilder(train_x[train_idx], train_y[train_idx]).add_x(transform=toTensor).add_y()
                .DataLoader(batch_size=params.batch_size,
                            num_workers=params.num_workers,
                            shuffle=True)
        )

        val_datalaoder = (
            DatasetBuilder(train_x[val_idx], train_y[val_idx]).add_x(transform=toTensor).add_y()
                .DataLoader(batch_size=params.batch_size, num_workers=4)
        )

        self.regist_databundler(train=train_dataloader,
                                eval=val_datalaoder,
                                test=test_dataloader)
        self.to(self.device)