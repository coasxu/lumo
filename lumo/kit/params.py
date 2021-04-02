"""

"""
import copy
import json
import os
import pprint as pp
import sys
import warnings
from collections import namedtuple
from collections.abc import Iterable
from datetime import timedelta
from itertools import chain
from typing import Any, overload

import fire
import torch

from lumo.base_classes.attr import attr
from lumo.base_classes.defaults import default
from lumo.base_classes.errors import BoundCheckError, NewParamWarning
from lumo.base_classes.params_vars import OptimParams, OptimMixin

arange_param = namedtuple('arange_param', ['default', 'left', 'right'], defaults=[None, float('-inf'), float('inf')])
choice_param = namedtuple('choice_param', ['default', 'choices'], defaults=[None, []])
default_param = namedtuple('default_param', ['default', 'warn'], defaults=[True])


class BaseParams(OptimMixin):
    """
    Params make it easy to get/set/load/dump your config, if you use easy_dict before, you can see Params as a easy_dict ppplus.

    Notes:
        Variable name starts with `_` is not recommeded, because of the special inner implement, variable name starts with `_`
        will be ignored when serialize Params instnace, you will loss the value of these variables.

        If you really want to define some special variable to make it look different from others, you can capitalize it or ends with `_`.
    """

    def __init__(self):
        self._param_dict = attr()
        self._repeat = -1
        self._constrain = {}
        self._lock = False

    def __getitem__(self, item):
        return self.__getattr__(item)

    def __setitem__(self, key, value):
        key = str(key)
        self.__setattr__(key, value)

    def __setattr__(self, name: str, value: Any) -> None:
        """
        1. check constrain
        2. check if is default and not exists
        """
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            if isinstance(value, (arange_param, choice_param)):
                self._constrain[name] = value
                value = value.default
            else:
                self._check(name, value)

            if isinstance(value, default_param):  # 设置默认值
                # only set default param when name not exists
                if name not in self._param_dict:
                    if value.warn:
                        warnings.warn(
                            "'{}' is a new param,please check your spelling. It's more recommended to define in advance.".format(
                                name))
                    value = value.default
                    self._param_dict[name] = value
            else:
                self._param_dict[name] = value

    def __getattr__(self, item):
        if item not in self._param_dict and self._lock:
            raise AttributeError(item)
        return self._param_dict.__getattr__(item)

    def __delattr__(self, name: str) -> None:
        if name.startswith("_"):
            super().__delattr__(name)
        else:
            self._param_dict.pop(name)

    def __delitem__(self, key):
        key = str(key)
        self.__delattr__(key)

    def __contains__(self, item):
        return item in self._param_dict

    def __getstate__(self):
        return {
            '_param_dict': self._param_dict,
            '_repeat': self._repeat,
            '_lock': self._lock,
            '_bound': self._constrain,
        }

    def __setstate__(self, d):
        self._param_dict = d['_param_dict']
        self._repeat = d['_repeat']
        self._lock = d['_lock']
        self._bind = d['_bound']

    def __repr__(self):
        dynamic_propertys = [(k, getattr(self, k)) for k in self.__dir__() if
                             isinstance(getattr(self.__class__, k, None), property)]

        return "{}".format(self.__class__.__name__) + pp.pformat(
            [(k, v) for k, v in chain(self._param_dict.items())] + [{'propertys': dynamic_propertys}])

    __str__ = __repr__

    def __eq__(self, other):
        """
        equal function only compare params, and will ignore other Params hidden variables, including `_repeat`, `_lock`, and
        `_bound`, so if param_1 equals to param_2, it means all key-value (need to be hashable) pair in these two Params
        instance is equal.
        """
        if isinstance(other, BaseParams):
            return self.hash() == other.hash()
        return False

    def _check(self, name, value):
        if isinstance(value, default):
            value = value.default
        if name not in self._constrain:
            return True
        bound = self._constrain[name]
        if isinstance(bound, arange_param) and not (bound.left <= value and value <= bound.right):
            raise BoundCheckError(f"value of param '{name}' should in range [{bound.left}, {bound.right}].")
        elif isinstance(bound, choice_param) and value not in bound.choices:
            raise BoundCheckError(f"value of param '{name}' should in values {bound.choices}.")

    def copy(self):
        res = self.__class__()
        res._param_dict = self._param_dict.copy()
        res._repeat = self._repeat
        res._bound = copy.deepcopy(self._constrain)
        res._lock = self._lock
        return res

    def arange(self, default, left=float("-inf"), right=float("inf")) -> arange_param:
        """
        Make sure some value is into some range.

        Examples:
            params.batch_size = params.arange(20,10,100)
            print(params.batch_size) # will print '20' as default.
            params.batch_size = 300 # will raise an Exception
            params.batch_size = 50
            print(params.batch_size) # will print 50

        Args:
            k: key of the value
            default: default value
            left: left interval
            right: right interval

        Returns:
            arange_param(default, left, right)
        """
        if left < default and default < right:
            return arange_param(default, left, right)
        else:
            raise BoundCheckError(f"value {default}' should in range [{left}, {right}].")

    def choice(self, *choices) -> choice_param:
        """
        Make sure some value is into some limited values.

        Examples:
            params.dataset = params.choice('cifar10','cifar100')
            print(params.dataset) # will print 'cifar10' as default.
            params.dataset = 'mnist' # will raise an Exception
            params.dataset = 'cifar100'
            print(params.dataset) # will print 'cifar100'

        Args:
            k: key of the value
            *choices: value can be used for key

        Returns:
            choice_param(choices[0], choices)


        """
        return choice_param(choices[0], choices)

    def default(self, value: Any = None, warn=True) -> default_param:
        """
        Set a default value to a key. This default value will be set only when `key` doesn't exists in Params.

        Examples:
        ```
        params.margin = 3
        params.margin = params.default(5,True)
        params.non_exists = params.default(0.3,True)
        print(params.margin)
        print(params.non_exists)
        ```

        Args:
            value: default value
            warn: warn if default value when set this default value, to warn user set this value manully in advance.
                default is True.

        Returns:
            default_param(value, warn)
        """
        return default_param(value, warn)

    def grid_search(self, key, iterable: Iterable):
        """
        Return a iterator where each element is the original Params instance
        but changes the value of variable `key` to the value in `iterable` one by one.

        Args:
            key:
            iterable:

        Returns:
            Iterator of Params instance with the same class and different value in `key`
        """
        for v in iterable:
            res = self.copy()
            res[key] = v
            yield res

    def grid_range(self, count):
        """
        Repeat this Params instance `count` times, and return its iterator.
        You can identify these instances by `params._repeat`(start from zero)

        Args:
            count:

        Returns:
            Iterator of the repeated Params instance
        """
        for i in range(count):
            res = self.copy()
            res._repeat = i
            yield res

    def from_args(self):
        """
        Load key-value from command line arguments (based on facebook-Fire).


        Examples:
            python demo.py --k=12 --v=qwe

            # demo.py
            params.from_args()
            print(params.k) # will give `12` int object
            print(params.v) # will give `qwe` string object
        """

        def func(**kwargs):
            if '_help' in kwargs:
                print(self)
                return

            if '_json' in kwargs:
                self.from_json(kwargs['_json'])
                return

            for k, v in kwargs.items():
                try:
                    self[k]
                except:
                    warnings.simplefilter('always', NewParamWarning)
                    warnings.warn(
                        "'{}' is a new param,please check your spelling.\n it's more recommended to define in advance.".format(
                            k), NewParamWarning)
                self[k] = v

        fire.Fire(func)
        return self

    def from_yaml(self, fn):
        """
        Read params from yaml file, if file path `fn` not exist or some Exceptions are raised during load, the program won't be terminal
        but error messages will be printed in stderr.

        Args:
            fn: file path of the yaml file
        """
        if os.path.exists(fn):
            try:
                import yaml
                with open(fn, encoding='utf-8') as r:
                    res = yaml.safe_load(r)
                    for k, v in res.items():
                        self[k] = v
            except ImportError as e:
                print(
                    "from_yaml() operation will be ignored, cause you havn't install yaml, use `pip install yaml` to install it")
            except Exception as e:
                print('from_yaml() operation will be ignored, cause:')
                print(e, file=sys.stderr)
        else:
            print(f'{fn} not exists, ignored load params from yaml file, please verify the path.', file=sys.stderr)
        return self

    def from_json(self, fn):
        """
        Read params from json file, if file path `fn` not exist or some Exceptions are raised during load, the program won't be terminal
        but error messages will be printed in stderr.

        Args:
            fn: file path of the yaml file
        """
        if os.path.exists(fn):
            try:
                with open(fn, encoding='utf-8') as r:
                    res = json.load(r)
                    for k, v in res.items():
                        self[k] = v
            except Exception as e:
                print('from_json() operation will be ignored, cause:')
                print(e, file=sys.stderr)
        else:
            print(f'{fn} not exists, ignored load params from json file, please verify the path', file=sys.stderr)
        return self

    def from_dict(self, dic: dict):
        """alias of update()"""
        for k, v in dic.items():
            self[k] = v

    def to_json(self, fn: str):
        """
        write params to the specified file path in json format.
        Args:
            fn: file path to write

        Notes:
            Only hashable key and values will be saved, see `lumo.base_classes.attr.jsonify()` for details.
        """
        with open(fn, 'w', encoding='utf-8') as w:
            json.dump(self.inner_dict().jsonify(), w, indent=2)

    def items(self):
        """like dict.items()"""
        return self._param_dict.items()

    def keys(self):
        """like dict.keys()"""
        for k in self._param_dict:
            yield k

    def update(self, dic: dict):
        """like dict.update()"""
        for k, v in dic.items():
            self._param_dict[k] = v

        return self

    def hash(self) -> str:
        """
        Return a hash string of all key and values. See attr.hash() for details.
        """
        return self._param_dict.hash()

    def lock(self):
        """
        Cause the params behavior is not exactly equal to dict, that is, Params instance will return an empty `attr` instance
        when some value not exists.

        To align this behavior, you can call `lock()`, then nonexist key will raise an AttributeError, which is equal to dict.

        Examples:
            params = Params()
            print(params.a) # will give an empty `attr` object
            params.lock()
            print(params.b) # will raise an AttributeError.

        Notes:
            Params default state is `unlock`, so ignore this method if you don't need this feature.
        """
        self._lock = True
        return self

    def unlock(self):
        """see lock for details."""
        self._lock = False
        return self

    def inner_dict(self) -> attr:
        """Return the inner attr, which is a dict-like object that saves all params."""
        return self._param_dict

    def get(self, k, default=None):
        """like dict.get()"""
        if k in self:
            return self[k]
        else:
            return default

    def replace(self, **kwargs):
        """alias of update()"""
        return self.update(kwargs)

    def contains(self, key: str):
        """like dict.contains()"""
        return key in self

    def merge(self, *params: 'BaseParams'):
        """Merge other params values"""
        for param in params:
            self._param_dict.update(param._param_dict)

    def initial(self):
        """"""
        pass


class DistributionParams(BaseParams):
    def __init__(self):
        super().__init__()
        self.backend = 'nccl'
        self.distributed = False
        self.world_size = -1
        self.local_rank = -1  # if not -1, means will use
        self.init_method = 'env://'

    @overload
    def init_process_group(self, backend,
                           init_method=None,
                           timeout=timedelta(minutes=30),
                           world_size=-1,
                           rank=-1,
                           store=None,
                           group_name=''):
        pass

    def init_process_group(self, *args, **kwargs):
        self.init_process_group_args = (args, kwargs)
        return self.init_process_group_args


class Params(BaseParams):

    def __init__(self):
        super().__init__()
        self.epoch = 10
        self.eidx = 1
        self.idx = 0
        self.global_step = 0
        self.device = "cuda:0" if torch.cuda.is_available() else "cpu"
        self.device_ids = []
        self.dataset = None
        self.architecture = None
        self.optim = None  # type:OptimParams
        self.git_commit = True
        self.tmp_dir = None  # type:str # set TMPDIR environment