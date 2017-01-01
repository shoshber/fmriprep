.. include:: links.rst

------------
Installation
------------

There are three ways to use fmriprep: in a `Docker Container`_, in a `Singularity Container`_, or in a `Manually Prepared Environment`_.
Using a container method is highly recommended.
Once you are ready to run fmriprep, see Usage_ for details.

Docker Container
================

Make sure command-line `Docker is installed <https://docs.docker.com/engine/installation/>`_.

See `External Dependencies`_ for more information (e.g., specific versions) on what is included in the fmriprep Docker image.

Now, assuming you have data, you can run fmriprep. You will need an active internet connection the first time. ::

    $ docker run --rm -v filepath/to/data/dir:/data:ro -v filepath/to/output/dir:/out -w /scratch poldracklab/fmriprep:latest /data /out/out participant

For example: ::

    $ docker run --rm -v $HOME/fullds005:/data:ro -v $HOME/dockerout:/out  -w /scratch poldracklab/fmriprep:latest /data /out/out participant -w /out/work/ -t ds005


Singularity Container
=====================

For security reasons, many HPCs (e.g., TACC) do not allow Docker containers, but do allow `Singularity <https://github.com/singularityware/singularity>`_ containers.
In this case, start with a machine (e.g., your personal computer) with Docker installed.
Use `docker2singularity <https://github.com/singularityware/docker2singularity>`_ to create a singularity image. You will need an active internet connection and some time. ::

    $ docker run -v /var/run/docker.sock:/var/run/docker.sock -v D:\host\path\where\to\ouptut\singularity\image:/output --privileged -t --rm singularityware/docker2singularity poldracklab/fmriprep:latest

Transfer the resulting Singularity image to the HPC, for example, using ``scp``. ::

    $ scp poldracklab_fmriprep_latest-*.img  user@hcpserver.edu:/path/to/downloads

If the data to be preprocessed is also on the HPC, you are ready to run fmriprep. ::

    $ singularity run path/to/singularity/image.img --participant_label label  path/to/data/dir path/to/output/dir participant

For example: ::

    $ singularity run ~/poldracklab_fmriprep_latest-2016-12-04-5b74ad9a4c4d.img --participant_label sub-387 --nthreads 1 -w $WORK/lonestar/work --ants-nthreads 16 --skull--strip-ants /work/04168/asdf/lonestar/ $WORK/lonestar/output participant


Manually Prepared Environment
=============================

.. note::

   This method is not recommended! Make sure you would rather do this than use a `Docker Container`_ or a `Singularity Container`_.

Make sure all of fmriprep's `External Dependencies`_ are installed.
These tools must be installed and their binaries available in the
system's ``$PATH``.

If you have pip installed, install fmriprep ::

    $ pip install fmriprep

If you have your data on hand, you are ready to run fmriprep: ::

    $ fmriprep data/dir output/dir --participant_label sub-num participant

External Dependencies
=====================

``fmriprep`` is implemented using nipype_, but it requires some other neuroimaging
software tools:

- `FSL <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_ (version 5.0)
- `ANTs <http://stnava.github.io/ANTs/>`_ (version 2.1.0.Debian-Ubuntu_X64)
- `AFNI <https://afni.nimh.nih.gov/>`_ (version Debian-16.2.07)
- `FreeSurfer <https://surfer.nmr.mgh.harvard.edu/>`_ (version Linux-centos4_x86_64-stable-pub-v5.3.0-HCP)
- `C3D <https://sourceforge.net/projects/c3d/>`_ (version 1.0.0)
