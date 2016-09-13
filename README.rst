FMRIPREP: A Robust Preprocessing Pipeline for fMRI Data
=======================================================

This pipeline is developed by the `Poldrack lab at Stanford University <https://poldracklab.stanford.edu/>`_
for use at the `Center for Reproducible Neuroscience (CRN) <http://reproducibility.stanford.edu/>`_,
as well as for open-source software distribution.

.. image:: https://circleci.com/gh/poldracklab/fmriprep/tree/master.svg?style=shield
  :target: https://circleci.com/gh/poldracklab/fmriprep/tree/master

.. image:: https://readthedocs.org/projects/fmriprep/badge/?version=latest
  :target: http://fmriprep.readthedocs.io/en/latest/?badge=latest
  :alt: Documentation Status

.. image:: https://img.shields.io/pypi/v/fmriprep.svg
  :target: https://pypi.python.org/pypi/fmriprep/
  :alt: Latest Version


About
-----

``fMRIprep`` is a functional magnetic resonance imaging (fMRI) data pre-processing pipeline.
It performs basic processing steps (coregistration, normalization, unwarping, 
noise component extraction, segmentation, skullstripping etc.) providing outputs that make
running a variety of group level analyses (task based or resting state fMRI, graph theory measures, surface or volume, etc.) easy.
``fMRIrep`` is build around three principles:

1. **Robustness** - the pipeline adapts the preprocessing steps depending on the input dataset and should provide results as good as possible independently of scanner make, scanning parameters or presence of additional correction scans (such as fieldmaps)
2. **Ease of use** - thanks to dependance on the BIDS standard manual parameter input is reduced to a minimum allow the pipelien to run in an automatic fashion.
3. **"Glass box"** philosophy - automation should not mean that one should not visually inspect the results or understand the methods. Thus ``fMRIprep`` provides for each subject visual reports detailing the accuracy of the most importatnt processing steps. This combined with the documentation can help researchers to understand the process and decide which subjects should be kept for the group level analysis.


External Dependencies
---------------------

``fMRIprep`` is implemented using ``nipype``, but it requires some other neuroimaging
software tools: `FSL <http://fsl.fmrib.ox.ac.uk/fsl/fslwiki/>`_,
`ANTs <http://stnava.github.io/ANTs/>`_, `AFNI <https://afni.nimh.nih.gov/>`_,
`FreeSurfer <https://surfer.nmr.mgh.harvard.edu/>`_,
`C3D <https://sourceforge.net/projects/c3d/>`_.

These tools must be installed and their binaries available in the
system's ``$PATH``.


Installation
------------

The ``fMRIprep`` is packaged and available through the PyPi repository.
Therefore, the easiest way to install the tool is: ::

    pip install fmriprep


Execution and the BIDS format
-----------------------------

The ``fmriprep`` workflow takes as principal input the path of the dataset
that is to be processed.
The only requirement to the input dataset is that it has a valid `BIDS (Brain
Imaging Data Structure) <http://bids.neuroimaging.io/>`_ format.
This can be easily checked online using the
`BIDS Validator <http://incf.github.io/bids-validator/>`_.

The command line interface follows the
`BIDS-Apps <https://github.com/BIDS-Apps>`_ definition.
Example: ::

    fmriprep data/bids_root/ out/ participant -w work/


Support and communication
-------------------------

The documentation of this project is found here: http://preprocessing-workflow.readthedocs.org/en/latest/.

If you have a problem or would like to ask a question about how to use ``fmriprep``,
please submit a question to NeuroStars.org with an ``fmriprep`` tag.
NeuroStars.org is a platform similar to StackOverflow but dedicated to neuroinformatics.

All previous ``fmriprep`` questions are available here:
http://neurostars.org/t/fmriprep/

To participate in the ``fmriprep`` development-related discussions please use the
following mailing list: http://mail.python.org/mailman/listinfo/neuroimaging
Please add *[fmriprep]* to the subject line when posting on the mailing list.


All bugs, concerns and enhancement requests for this software can be submitted here:
https://github.com/poldracklab/preprocessing-workflow/issues.


Acknowledgements
----------------

Please acknowledge this work mentioning explicitly the name of this software (fmriprep)
and the version, along with the link to the GitHub repository
(https://github.com/poldracklab/preprocessing-workflow).


License information
-------------------

We use the 3-clause BSD license; the full license is in the file ``LICENSE`` in
the ``fmriprep`` distribution.

All trademarks referenced herein are property of their respective
holders.

Copyright (c) 2015-2016, the fmriprep developers and the CRN.
All rights reserved.
