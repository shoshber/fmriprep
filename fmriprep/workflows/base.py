#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Created on Wed Dec  2 17:35:40 2015

@author: craigmoodie
"""
from nipype.pipeline import engine as pe
from nipype.interfaces import utility as niu
from nipype.interfaces import fsl
from nipype.interfaces import freesurfer as fs
from nipype.interfaces import io as nio

from fmriprep.interfaces import BIDSDataGrabber
from fmriprep.utils.misc import collect_bids_data
from fmriprep.workflows.anatomical import t1w_preprocessing
from fmriprep.workflows.sbref import sbref_preprocess, sbref_t1_registration
from fmriprep.workflows.fieldmap import phase_diff_and_magnitudes
from fmriprep.workflows.epi import (
    epi_unwarp, epi_hmc, epi_sbref_registration,
    epi_mean_t1_registration, epi_mni_transformation)

def base_workflow_enumerator(subject_list, settings):
    workflow = pe.Workflow(name='workflow_enumerator')
    generated_list = []
    for subject in subject_list:
        generated_workflow = base_workflow_generator(subject, settings)
        if generated_workflow:
            generated_list.append(generated_workflow)
    workflow.add_nodes(generated_list)

    return workflow

def base_workflow_generator(subject_id, settings):
    subject_data = collect_bids_data(settings['bids_root'], subject_id)
    if (subject_data['t1w'] != [] and subject_data['sbref'] != []):
        return wf_ds054_type(subject_data, settings, name=subject_id)
    if (subject_data['t1w'] != [] and subject_data['sbref'] == []):
        return wf_ds005_type(subject_data, settings, name=subject_id)
    return None

def wf_ds054_type(subject_data, settings, name='fMRI_prep'):
    """
    The main fmri preprocessing workflow, for the ds054-type of data:

      * [x] Has at least one T1w and at least one bold file (minimal reqs.)
      * [x] Has one or more SBRefs
      * [x] Has one or more GRE-phasediff images, including the corresponding magnitude images.
      * [ ] No SE-fieldmap images
      * [ ] No Spiral Echo fieldmap

    """

    if settings is None:
        settings = {}

    workflow = pe.Workflow(name=name)

    #  inputnode = pe.Node(niu.IdentityInterface(fields=['subject_id']),
    #                    name='inputnode')
    #  inputnode.iterables = [('subject_id', subject_list)]

    bidssrc = pe.Node(BIDSDataGrabber(subject_data=subject_data), name='BIDSDatasource')

    # Preprocessing of T1w (includes registration to MNI)
    t1w_pre = t1w_preprocessing(settings=settings)

    # Estimate fieldmap
    fmap_est = phase_diff_and_magnitudes()

    # Correct SBRef
    sbref_pre = sbref_preprocess(settings=settings)

    # Register SBRef to T1
    sbref_t1 = sbref_t1_registration(settings=settings)

    # HMC on the EPI
    hmcwf = epi_hmc(settings=settings)
    hmcwf.get_node('inputnode').iterables = ('epi', subject_data['func'])

    # EPI to SBRef
    epi2sbref = epi_sbref_registration()

    # EPI unwarp
    epiunwarp_wf = epi_unwarp(settings=settings)

    workflow.connect([
        (bidssrc, t1w_pre, [('t1w', 'inputnode.t1w')]),
        (bidssrc, fmap_est, [('fmap', 'inputnode.input_images')]),
        (bidssrc, sbref_pre, [('sbref', 'inputnode.sbref')]),
        (fmap_est, sbref_pre, [('outputnode.fmap', 'inputnode.fmap'),
                               ('outputnode.fmap_ref', 'inputnode.fmap_ref'),
                               ('outputnode.fmap_mask', 'inputnode.fmap_mask')]),
        (sbref_pre, sbref_t1, [('outputnode.sbref_unwarped', 'inputnode.sbref_brain')]),
        (t1w_pre, sbref_t1, [
            ('outputnode.t1_brain', 'inputnode.t1_brain'),
            ('outputnode.t1_seg', 'inputnode.t1_seg')]),
        (sbref_pre, epi2sbref, [('outputnode.sbref_unwarped', 'inputnode.sbref_brain')]),
        (hmcwf, epi2sbref, [('outputnode.epi_brain', 'inputnode.epi_brain')]),

        (hmcwf, epiunwarp_wf, [('inputnode.epi', 'inputnode.epi')]),
        (fmap_est, epiunwarp_wf, [('outputnode.fmap', 'inputnode.fmap'),
                                  ('outputnode.fmap_mask', 'inputnode.fmap_mask'),
                                  ('outputnode.fmap_ref', 'inputnode.fmap_ref')])
    ])
    return workflow


def wf_ds005_type(subject_data, settings, name='fMRI_prep'):
    """
    The main fmri preprocessing workflow, for the ds005-type of data:

      * [x] Has at least one T1w and at least one bold file (minimal reqs.)
      * [ ] No SBRefs
      * [ ] No GRE-phasediff images, including the corresponding magnitude images.
      * [ ] No SE-fieldmap images
      * [ ] No Spiral Echo fieldmap

    """

    if settings is None:
        settings = {}

    workflow = pe.Workflow(name=name)

    #  inputnode = pe.Node(niu.IdentityInterface(fields=['subject_id']),
    #                      name='inputnode')
    #  inputnode.iterables = [('subject_id', subject_list)]

    bidssrc = pe.Node(BIDSDataGrabber(subject_data=subject_data),
                      name='BIDSDatasource')

    # Preprocessing of T1w (includes registration to MNI)
    t1w_pre = t1w_preprocessing(settings=settings)

    # HMC on the EPI
    hmcwf = epi_hmc(settings=settings)
    hmcwf.get_node('inputnode').iterables = ('epi', subject_data['func'])

    # mean EPI registration to T1w
    epi_2_t1 = epi_mean_t1_registration(settings=settings)

    # Apply transforms in 1 shot
    epi_mni_trans_wf = epi_mni_transformation(settings=settings)


    workflow.connect([
        (bidssrc, t1w_pre, [('t1w', 'inputnode.t1w')]),
        (hmcwf, epi_2_t1, [('inputnode.epi', 'inputnode.epi')]),

        (hmcwf, epi_2_t1, [('outputnode.epi_mean', 'inputnode.epi_mean')]),
        (t1w_pre, epi_2_t1, [('outputnode.t1_brain', 'inputnode.t1_brain'),
                             ('outputnode.t1_seg', 'inputnode.t1_seg')]),
        (hmcwf, epi_mni_trans_wf, [('inputnode.epi', 'inputnode.epi')]),
        (epi_2_t1, epi_mni_trans_wf, [('outputnode.mat_epi_to_t1', 'inputnode.mat_epi_to_t1')]),
        (hmcwf, epi_mni_trans_wf, [('outputnode.xforms', 'inputnode.hmc_xforms'),
                                   ('outputnode.epi_mask', 'inputnode.epi_mask')]),
        (t1w_pre, epi_mni_trans_wf, [('outputnode.t1_brain', 'inputnode.t1'),
                                     ('outputnode.t1_2_mni_forward_transform',
                                      'inputnode.t1_2_mni_forward_transform')])

    ])

    return workflow

def _first(inlist):
    if isinstance(inlist, (list, tuple)):
        inlist = _first(inlist[0])
    return inlist
