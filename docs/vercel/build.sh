~/micromamba/bin/python --version
cd docs
~/micromamba/bin/python -m pdm run sphinx-build -M html "." "_build" -W --keep-going
