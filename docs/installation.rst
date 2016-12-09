------------
Installation
------------

There are three ways to use fmriprep: `Docker`_, `Singularity`_, and `Manually Prepared Environment`_.
Once you are ready to run fmriprep, see `Usage`_ for details.

Docker
======

First, make sure command-line Docker is installed. If you don't receive any output from the following command, `install Docker <https://docs.docker.com/engine/installation/>`_. ::

$ which docker

Start the Docker daemon. You may need to use `sudo`. ::

$ dockerd

Download the latest docker image. You will need an active internet connection and some time. ::

$ docker pull poldracklab/fmriprep:latest

Now, assuming you have data, you can run fmriprep. ::

$ docker run --rm -v filepath/to/data/dir:/data:ro -v filepath/to/output/dir:/out -w /scratch poldracklab/fmriprep:latest /data /out/out participant -w /out/work/

For example: ::

$ docker run --rm -v $HOME/fullds005:/data:ro -v $HOME/dockerout:/out  -w /scratch poldracklab/fmriprep:latest /data /out/out participant -w /out/work/ -t ds005


Singularity
===========

As above, make sure Docker is installed and the Docker daemon is running. ::

$ which docker
file/path/docker
$ dockerd

Use `docker2singularity <https://github.com/singularityware/docker2singularity>`_ to create a singularity image. You will need an active internet connection and some time. ::

$ docker run -v /var/run/docker.sock:/var/run/docker.sock -v D:\host\path\where\to\ouptut\singularity\image:/output --privileged -t --rm singularityware/docker2singularity poldracklab/fmriprep:latest

On a computer with `Singularity <https://github.com/singularityware/singularity>`_ installed and the data to be prepped, run fmriprep. ::

$ singularity exec path/to/singularity/image.img /usr/bin/run_fmriprep --participant_label label -w path/to/work/dir path/to/data/dir path/to/output/dir participant

For example: ::

$ singularity exec ~/poldracklab_fmriprep_latest-2016-12-04-5b74ad9a4c4d.img /usr/bin/run_fmriprep --participant_label sub-387 --nthreads 1 -w $WORK/lonestar/work --ants-nthreads 16 --skull--strip-ants /work/04168/berleant/lonestar/ $WORK/lonestar/output participant

Manually Prepared Environment
============================

First, make sure you would rather do this than use `Docker`_ or `Singularity`_.

Make sure all of fmriprep's `External Dependencies`_ are installed. If you have pip installed, install fmriprep ::

$ pip install fmriprep

If you have your data on hand, you are ready to run fmriprep: ::

$ fmriprep data/dir work/dir --participant_label sub-num participant
