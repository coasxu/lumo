"""
Methods about files/paths/hash
"""
import hashlib
import os
from functools import lru_cache

from git import Git

from thexp.utils import re
from ..globals import _GITKEY


def listdir_by_time(dir_path):
    dir_list = os.listdir(dir_path)
    if not dir_list:
        return []
    else:
        # os.path.getctime() 函数是获取文件最后创建时间
        dir_list = sorted(dir_list, key=lambda x: os.path.getatime(os.path.join(dir_path, x)), reverse=True)
        return dir_list


def _default_config():
    return {
        _GITKEY.expsdir: os.path.expanduser("~/.cache/thexp/experiments")
    }


def _create_home_dir(path):
    os.makedirs(path)
    import json
    with open("config.json", "w") as w:
        json.dump({
            _GITKEY.expsdir: os.path.join(path, 'experiments')
        }, w, indent=2)


@lru_cache(1)
def home_dir():
    """dir for storing global record"""
    path = os.path.expanduser("~/.thexp")
    if not os.path.exists(path):
        _create_home_dir(path)

    return path


def local_dir():
    path = repo_root()
    if path is not None:
        path = os.path.join(path, '.thexp')
        if not os.path.exists(path):
            os.makedirs(path)
    return path


@lru_cache(1)
def config_path():
    """global config file path"""
    return os.path.join(home_dir(), "config.json")


def global_config_path():
    return os.path.join(home_dir(), "config.json")


def local_config_path():
    res = repo_root()
    if res is None:
        return None
    return os.path.join(res, '')


def file_atime_hash(file):
    """
    calculate hash of given file's atime
    atime : time of last access
    """
    return string_hash(str(os.path.getatime(file)))


def string_hash(*str):
    """calculate hash of given string list"""
    hl = hashlib.md5()
    for s in str:
        hl.update(s.encode(encoding='utf-8'))
    return hl.hexdigest()[:16]


def file_hash(file: str) -> str:
    """calculate hash of given file path"""
    hl = hashlib.md5()
    with open(file, 'rb') as r:
        hl.update(r.read())
    return hl.hexdigest()[:16]


def filter_filename(title: str, substr='-'):
    """replace invalid string of given file path by `substr`"""
    title = re.sub('[\/:*?"<>|]', substr, title)  # 去掉非法字符
    return title


def hash(value) -> str:
    """try to calculate hash of any given object"""
    import hashlib
    from collections.abc import Iterable
    from numbers import Number
    from numpy import ndarray
    from torch import Tensor
    hl = hashlib.md5()

    if isinstance(value, (ndarray, Tensor)):
        if isinstance(hl, Tensor):
            value = value.detach_().cpu().numpy()
        try:
            value = value.item()
        except:
            value = None
    if isinstance(value, (Number)):
        value = str(value)

    if isinstance(value, dict):
        for k in sorted(value.keys()):
            v = value[k]
            hl.update(str(k).encode(encoding='utf-8'))
            hl.update(hash(v).encode(encoding='utf-8'))
    elif isinstance(value, str):
        hl.update(value.encode(encoding='utf-8'))
    elif isinstance(value, Iterable):
        for v in value:
            hl.update(hash(v).encode(encoding='utf-8'))
    return hl.hexdigest()


def renormpath(path):
    return os.path.normcase(path).replace("\\", '/')


@lru_cache()
def repo_root(dir="./", ignore_info=False):
    """
    判断某目录是否在git repo 目录内（包括子目录），如果是，返回该 repo 的根目录
    :param dir:  要判断的目录。默认为程序运行目录
    :return: 如果是，返回该repo的根目录（包含 .git/ 的目录）
        否则，返回空
    """
    cur = os.getcwd()
    os.chdir(dir)
    try:
        res = Git().execute(['git', 'rev-parse', '--git-dir'])
    except Exception as e:
        if not ignore_info:
            print(e)
        res = None
    os.chdir(cur)
    return res
