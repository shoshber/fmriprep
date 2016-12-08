------------
Installation
------------

There are three ways to use fmriprep: `Docker`_, `Singularity`_, and `Manually Prepared Environment`_.

Docker
======

First, make sure command-line Docker is installed. If you don't receive any output from the following command, `install Docker <https://docs.docker.com/engine/installation/>`_.

::
$ which docker

Download the latest docker image. You will need an active internet connection.

::
$ docker pull poldracklab/fmriprep:latest

Now run fmriprep.

::
$ docker run -i -v filepath/to/data/dir:/data:ro -v filepath/to/output/dir:/out -w /scratch poldracklab/fmriprep:latest /data /out/out participant -w /out/work/ --fmriprep:options

For example:

::
$ docker run -i -v $HOME/fullds005:/data:ro -v $HOME/dockerout:/out  -w /scratch poldracklab/fmriprep:latest /data /out/out participant -w /out/work/ -t ds005 participant -t ds005


Singularity
===========

As above, make sure Docker is installed.

::
$ which docker
file/path/docker

Use `docker2singularity <https://github.com/singularityware/docker2singularity>`_ to create a singularity image.

::
$ docker run -v /var/run/docker.sock:/var/run/docker.sock -v D:\host\path\where\to\ouptut\singularity\image:/output --privileged -t --rm singularityware/docker2singularity poldracklab/fmriprep:latest

On a computer with `Singularity <https://github.com/singularityware/singularity>`_ installed, run fmriprep.

::
$ singularity exec path/to/singularity/image.img /usr/bin/run_fmriprep --fmriprep=options participant

For example:

::
$ singularity exec ~/poldracklab_fmriprep_latest-2016-12-04-5b74ad9a4c4d.img /usr/bin/run_fmriprep --participant_label sub-387 --nthreads 1 -w $WORK/lonestar/work --ants-nthreads 16 --skull--strip-ants /work/04168/berleant/lonestar/ $WORK/lonestar/output participant

Manually Prepared Environment
============================

First, make sure you would rather do this than use `Docker`_ or `Singularity`_.

Make sure all of fmriprep's `External Dependencies`_ are installed. If you have pip installed, install fmriprep:

::
$ pip install fmriprep

Run fmriprep:

::
$ fmriprep data/dir work/dir --participant_label sub-num participant
