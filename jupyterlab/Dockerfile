FROM python:3.8-slim-buster
MAINTAINER Kyle F. Downey "kyle.downey@gmail.com"

# copy the config file
USER root
RUN mkdir -p /etc/jupyter
COPY $PWD/jupyter_notebook_config.py /etc/jupyter/jupyter_notebook_config.py

# install dependencies for Git extension and JupyterLab build as well as wheel build for postgresql client
RUN apt-get update && apt-get install --yes git nodejs npm gcc libpq-dev

# upgrade pip itself
RUN python -m pip install --upgrade pip

# install stock requirements and labextensions
COPY $PWD/requirements.txt /app/requirements.txt
RUN pip install -r /app/requirements.txt && \
    jupyter labextension install @jupyterlab/git --no-build && \
    jupyter labextension install @jupyter-widgets/jupyterlab-manager && \
    jupyter labextension install @jupyterlab/plotly-extension --no-build && \
    jupyter labextension install nbdime-jupyterlab --no-build && \
    jupyter serverextension enable --py jupyterlab_git && \
    jupyter lab build

# set up a serenity user so we are not running under root
RUN groupadd -r serenity && useradd -s /bin/bash --create-home --no-log-init -r -g serenity serenity

USER serenity
RUN mkdir -p /home/serenity/dev/shadows
WORKDIR /home/serenity/dev/shadows

CMD ["jupyter", "lab"]
