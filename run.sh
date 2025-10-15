#!/bin/zsh

alias python=python3

pythonVersion=$(python --version)

if [ ! -f ./python_version.txt ]; then
	echo "$pythonVersion" >> ./python_version.txt
fi

storedPythonVersion=$(cat ./python_version.txt)

if [ "$pythonVersion" != "$storedPythonVersion" ]; then
	rm -rf ./venv
	python -m venv ./venv

	source ./venv/bin/activate
	pip install -r requirements.txt
	deactivate

	rm ./python_version.txt
	echo "$pythonVersion" >> ./python_version.txt
fi

source ./venv/bin/activate
python ./main.py
deactivate
