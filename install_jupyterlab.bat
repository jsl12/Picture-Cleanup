CALL .\venv\Scripts\activate.bat
pip install jupyterlab qgrid
jupyter nbextension enable --py --sys-prefix widgetsnbextension
jupyter nbextension enable --py --sys-prefix qgrid
jupyter labextension install @jupyter-widgets/jupyterlab-manager
jupyter labextension install qgrid
