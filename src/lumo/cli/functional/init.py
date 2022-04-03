import git
from pathlib import Path

from lumo.utils.repository import git_commit

git_ignore = ['# Byte-compiled / optimized / DLL files', '.DS_Store', '__pycache__/', '*.py[cod]', '*$py.class', '',
              '# C extensions', '*.so', '', '# Distribution / packaging', '.Python', 'build/', 'develop-eggs/', 'dist/',
              'downloads/', 'eggs/', '.eggs/', 'lib/', 'lib64/', 'parts/', 'sdist/', 'var/', 'wheels/',
              'share/python-wheels/',
              '*.egg-info/', '.installed.cfg', '*.egg', 'MANIFEST', '', '# PyInstaller',
              '#  Usually these files are written by a python script from a template',
              '#  before PyInstaller builds the exe, so as to inject date/other infos into it.', '*.manifest', '*.spec',
              '',
              '# Installer logs', 'pip-log.txt', 'pip-delete-this-directory.txt', '', '# Unit test / coverage reports',
              'htmlcov/',
              '.tox/', '.nox/', '.coverage', '.coverage.*', '.cache', 'nosetests.xml', 'coverage.xml', '*.cover',
              '*.py,cover',
              '.hypothesis/', '.pytest_cache/', 'cover/', '', '# Translations', '*.mo', '*.pot', '', '# Django stuff:',
              '*.log',
              'local_settings.py', 'db.sqlite3', 'db.sqlite3-journal', '', '# Flask stuff:', 'instance/',
              '.webassets-cache', '',
              '# Scrapy stuff:', '.scrapy', '', '# Sphinx documentation', 'docs/_build/', '', '# PyBuilder',
              '.pybuilder/',
              'target/', '', '# Jupyter Notebook', '.ipynb_checkpoints', '', '# IPython', 'profile_default/',
              'ipython_config.py',
              '', '# pyenv', '#   For a library or package, you might want to ignore these files since the code is',
              '#   intended to run in multiple environments; otherwise, check them in:', '# .python-version', '',
              '# pipenv',
              '#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.',
              '#   However, in case of collaboration, if having platform-specific dependencies or dependencies',
              "#   having no cross-platform support, pipenv may install dependencies that don't work, or not",
              '#   install all needed dependencies.', '#Pipfile.lock', '',
              '# PEP 582; used by e.g. github.com/David-OConnor/pyflow',
              '__pypackages__/', '', '# Celery stuff', 'celerybeat-schedule', 'celerybeat.pid', '',
              '# SageMath parsed files',
              '*.sage.py', '', '# Environments', '.env', '.venv', 'env/', 'venv/', 'ENV/', 'env.bak/', 'venv.bak/', '',
              '# Spyder project settings', '.spyderproject', '.spyproject', '', '# Rope project settings',
              '.ropeproject', '',
              '# mkdocs documentation', '/site', '# pycharm', '.idea', '', '', '# mypy', '.mypy_cache/', '.dmypy.json',
              'dmypy.json',
              '', '# Pyre type checker', '.pyre/', '', '# pytype static type analyzer', '.pytype/', '',
              '# Cython debug symbols',
              'cython_debug/', '.thexp/', 'repo.json', '.expsdirs', '.idea/', '*.pth', '*.npy',
              '*.ckpt',
              '*.thexp.*', '*.pkl', '.cache/', '.lumo/config.json', '*.lumo.*', '*.ft', 'kk', 'temp', '.idea', '',
              'lumo_temp',
              '.lumo/', '*scratch*']


def check_gitignore(path):
    ignore_file = Path(path).joinpath('.gitignore')
    if ignore_file.exists():
        res = ignore_file.read_text().split('\n')
        new_ignore = [i for i in git_ignore if i not in res]
    else:
        new_ignore = git_ignore

    Path(path).joinpath('.gitignore').write_text('\n'.join(new_ignore))


def git_init(path=None):
    if path is None:
        path = './'

    repo = git.Repo.init(path, mkdir=True)
    check_gitignore(path)
    git_commit(repo, branch_name=None)
    return repo