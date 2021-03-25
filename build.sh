git pull
python3 setup.py sdist bdist_wheel
pip install dist/$(python3 install.py)
