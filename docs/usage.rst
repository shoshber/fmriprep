Usage
-----

Workflow graph:

.. graphviz:: ds005.dot

end of graph

::


Execution and the BIDS format
=============================

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
=========================

The documentation of this project is found here: http://fmriprep.readthedocs.org/en/latest/.

If you have a problem or would like to ask a question about how to use ``fmriprep``,
please submit a question to NeuroStars.org with an ``fmriprep`` tag.
NeuroStars.org is a platform similar to StackOverflow but dedicated to neuroinformatics.

All previous ``fmriprep`` questions are available here:
http://neurostars.org/t/fmriprep/

To participate in the ``fmriprep`` development-related discussions please use the
following mailing list: http://mail.python.org/mailman/listinfo/neuroimaging
Please add *[fmriprep]* to the subject line when posting on the mailing list.


All bugs, concerns and enhancement requests for this software can be submitted here:
https://github.com/poldracklab/fmriprep/issues.
