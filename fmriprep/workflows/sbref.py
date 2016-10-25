#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
"""
Preprocessing workflows for :abbr:`SB (single-band)`-reference (SBRef)
images.

Originally coded by Craig Moodie. Refactored by the CRN Developers.
"""

import os
import os.path as op
from nipype.pipeline import engine as pe
from nipype.interfaces import io as nio
from nipype.interfaces import utility as niu
from nipype.interfaces import fsl, c3
from nipype.interfaces import freesurfer as fs
from nipype.interfaces import ants

from fmriprep.utils.misc import gen_list
from fmriprep.interfaces import (ReadSidecarJSON, IntraModalMerge,
    DerivativesDataSink)
from fmriprep.workflows.fieldmap import sdc_unwarp
from fmriprep.viz import stripped_brain_overlay

def sbref_preprocess(name='SBrefPreprocessing', settings=None):
    """SBref processing workflow"""

    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['sbref', 'fmap', 'fmap_ref', 'fmap_mask']
        ),
        name='inputnode'
    )
    outputnode = pe.Node(niu.IdentityInterface(fields=['sbref_unwarped', 'sbref_unwarped_mask']),
                         name='outputnode')

    # Unwarping
    unwarp = sdc_unwarp()
    unwarp.inputs.inputnode.hmc_movpar = ''

    mean = pe.Node(fsl.MeanImage(dimension='T'), name='SBRefMean')
    inu = pe.Node(ants.N4BiasFieldCorrection(dimension=3), name='SBRefBias')
    bet = pe.Node(fsl.BET(frac=0.6, mask=True), name='SBRefBET')

    workflow.connect([
        (inputnode, unwarp, [('fmap', 'inputnode.fmap'),
                             ('fmap_ref', 'inputnode.fmap_ref'),
                             ('fmap_mask', 'inputnode.fmap_mask')]),
        (inputnode, unwarp, [('sbref', 'inputnode.in_file')]),
        (unwarp, mean, [('outputnode.out_file', 'in_file')]),
        (mean, inu, [('out_file', 'input_image')]),
        (inu, bet, [('output_image', 'in_file')]),
        (bet, outputnode, [('out_file', 'sbref_unwarped'),
                           ('mask_file', 'sbref_unwarped_mask')])
    ])

    # Plot result
    def _first(inlist):
        return sorted(inlist)[0]

    sbref_corr= pe.Node(
        niu.Function(
            input_names=["in_file", "overlay_file", "out_file"],
            output_names=["out_file"],
            function=stripped_brain_overlay
        ),
        name="SBRefCorr"
    )
    sbref_corr.inputs.out_file = "corrected_SBRef.svg"

    datasink = pe.Node(
        DerivativesDataSink(base_directory=settings['output_dir'], 
                            suffix='sdc'),
        name='datasink'
    )

    sbref_stripped_overlay = pe.Node(
        niu.Function(
            input_names=["in_file", "overlay_file", "out_file"],
            output_names=["out_file"],
            function=stripped_brain_overlay
        ),
        name="SbrefStrippedOverlay"
    )
    sbref_stripped_overlay.inputs.out_file = "sbref_stripped_overlay.svg"

    ds_sbref_stripped_overlay = pe.Node(
        interface=nio.DataSink(
            base_directory=op.join(settings['output_dir'], 'images')
        ),
        name='dsSBRefStrippedOverlay',
        parameterization=False
    )
    
    workflow.connect([
        (inputnode, datasink, [(('sbref', _first), 'source_file')]),
        (bet, datasink, [('out_file', 'in_file')]),
        (mean, sbref_corr, [('out_file', 'overlay_file')]),
        (inputnode, sbref_corr, [('fmap_mask', 'in_file')]),
        (mean, sbref_stripped_overlay, [('out_file', 'overlay_file')]),
        (bet, sbref_stripped_overlay, [('mask_file', 'in_file')]),
        (sbref_stripped_overlay, ds_sbref_stripped_overlay, [('out_file', '@sbref_stripped_overlay')])
    ])
    return workflow

def sbref_t1_registration(name='SBrefSpatialNormalization', settings=None):
    """
    Uses FSL FLIRT with the BBR cost function to find the transform that
    maps the SBRef space into the T1-space
    """
    workflow = pe.Workflow(name=name)

    inputnode = pe.Node(
        niu.IdentityInterface(fields=['sbref_brain', 't1_brain', 't1_seg']),
        name='inputnode'
    )
    outputnode = pe.Node(
        niu.IdentityInterface(fields=['mat_sbr_to_t1', 'mat_t1_to_sbr', 'itk_t1_to_sbr']),
        name='outputnode'
    )

    # Make sure sbref is in RAS coordinates
    reorient = pe.Node(
        fs.MRIConvert(out_type='niigz', out_orientation='RAS'),
        name='SBRefReorient'
    )

    # Extract wm mask from segmentation
    wm_mask = pe.Node(
        niu.Function(input_names=['in_file'], output_names=['out_file'],
                     function=_extract_wm),
        name='WM_mask'
    )

    # BBR works better with initialization
    flt_bbr_init = pe.Node(fsl.FLIRT(dof=6, out_matrix_file='init.mat'),
        name='Flirt_BBR_init')
    flt_bbr = pe.Node(fsl.FLIRT(dof=6, cost_func='bbr'), name="Flirt_BBR")
    flt_bbr.inputs.schedule = op.join(os.getenv('FSLDIR'),
                                      'etc/flirtsch/bbr.sch')

    # make equivalent warp fields
    invt_bbr = pe.Node(fsl.ConvertXFM(invert_xfm=True), name="Flirt_BBR_Inv")

    # transform inv to itk format
    invt_itk_formatter = pe.Node(c3.C3dAffineTool(fsl2ras=True, itk_transform=True),
                                 name='InvtITKFormatter')

    workflow.connect([
        (inputnode, reorient, [('sbref_brain', 'in_file')]),
        (inputnode, wm_mask, [('t1_seg', 'in_file')]),
        (inputnode, flt_bbr_init, [('t1_brain', 'reference')]),
        (inputnode, flt_bbr, [('t1_brain', 'reference')]),
        (reorient, flt_bbr_init, [('out_file', 'in_file')]),
        (reorient, flt_bbr, [('out_file', 'in_file')]),
        (flt_bbr_init, flt_bbr, [('out_matrix_file', 'in_matrix_file')]),
        (wm_mask, flt_bbr, [('out_file', 'wm_seg')]),
        (flt_bbr, invt_bbr, [('out_matrix_file', 'in_file')]),
        (flt_bbr, outputnode, [('out_matrix_file', 'mat_sbr_to_t1')]),
        (invt_bbr, outputnode, [('out_file', 'mat_t1_to_sbr')]),

        (invt_bbr, invt_itk_formatter, [('out_file', 'transform_file')]),
        (inputnode, invt_itk_formatter, [('t1_seg', 'source_file'),
                                         ('sbref_brain', 'reference_file')]),
        (invt_itk_formatter, outputnode, [('itk_transform', 'itk_t1_to_sbr')])
    ])

    # Plots for report
    sbref_t1 = pe.Node(
        niu.Function(
            input_names=["in_file", "overlay_file", "out_file"],
            output_names=["out_file"],
            function=stripped_brain_overlay
        ),
        name="PNG_sbref_t1"
    )
    sbref_t1.inputs.out_file = "sbref_to_t1.svg"

    datasink = pe.Node(
        nio.DataSink(base_directory=op.join(settings['output_dir'], "images")),
        name="datasink",
        parameterization=False
    )

    workflow.connect([
        (flt_bbr, sbref_t1, [('out_file', 'overlay_file')]),
        (inputnode, sbref_t1, [('t1_seg', 'in_file')]),
        (sbref_t1, datasink, [('out_file', '@sbref_to_t1')])
    ])

    return workflow


def _extract_wm(in_file):
    import os.path as op
    import nibabel as nb
    import numpy as np

    im = nb.load(in_file)
    data = im.get_data().astype(np.uint8)
    data[data != 3] = 0
    data[data > 0] = 1

    out_file = op.abspath('wm_mask.nii.gz')
    nb.Nifti1Image(data, im.get_affine(), im.get_header()).to_filename(out_file)
    return out_file

###################################
# Deprecated code
###################################

def sbref_workflow_deprecated(name='SBrefPreprocessing', settings=None):
    """Legacy SBref processing workflow"""
    if settings is None:
        settings = {}

    workflow = pe.Workflow(name=name)
    inputnode = pe.Node(
        niu.IdentityInterface(
            fields=['sbref', 'mag_brain', 'fmap_scaled', 'fmap_mask',
                    'fmap_unmasked', 'in_topup', 't1', 't1_brain', 't1_seg']
        ),
        name='inputnode'
    )
    outputnode = pe.Node(
        niu.IdentityInterface(
            fields=['sbref_unwarped', 'sbref_fmap', 'mag2sbref_matrix',
                    'sbref_brain', 'sbref_brain_corrected', 't1_brain',
                    'wm_seg', 'sbref_2_t1_transform']
        ),
        name='outputnode'
    )

    #  Skull strip SBRef to get reference brain
    sbref_bet = pe.Node(
        fsl.BET(mask=True, functional=True, frac=0.6), name="sbref_bet")

    #  Unwarp SBRef using Fugue  (N.B. duplicated in epi_reg_workflow!!!!!)
    fugue_sbref = pe.Node(
        fsl.FUGUE(unwarp_direction='x', dwell_time=dwell_time),
        name="SBRef_Unwarping"
    )

    strip_corrected_sbref = pe.Node(fsl.BET(mask=True, frac=0.6, robust=True),
                                    name="BET_Corrected_SBRef")

    flt_sbref_brain_t1_brain = pe.Node(
        fsl.FLIRT(dof=6, bins=640, cost_func='mutualinfo'),
        name='sbref_brain_2_t1_brain_affine_transform'
    )

    flt_sbref_2_t1 = pe.Node(
        fsl.FLIRT(dof=6, bins=640, cost_func='mutualinfo'),
        name='sbref_2_t1_affine_transform'
    )

    # Affine transform of T1 segmentation into SBRref space
    flt_wmseg_sbref = pe.Node(fsl.FLIRT(dof=6, bins=64, cost_func='mutualinfo'),
                              name="WMSeg_2_SBRef_Brain_Affine_Transform")

    invert_wmseg_sbref = pe.Node(
        fsl.ConvertXFM(invert_xfm=True), name="invert_wmseg_sbref"
    )

    #  Run the commands from epi_reg_dof
    #  WITH FIELDMAP (unwarping steps)
    #  flirt -in ${fmapmagbrain} -ref ${vrefbrain} -dof ${dof} -omat
    #  ${vout}_fieldmap2str_init.mat
    flt_fmap_mag_brain_sbref_brain = pe.Node(
        fsl.FLIRT(dof=6, bins=640, cost_func='mutualinfo'),
        name="Fmap_Mag_Brain_2_SBRef_Brain_Affine_Transform"
    )

    #  flirt -in ${fmapmaghead} -ref ${vrefhead} -dof ${dof} -init
    #  ${vout}_fieldmap2str_init.mat -omat ${vout}_fieldmap2str.mat -out
    #  ${vout}_fieldmap2str -nosearch
    flt_fmap_mag_sbref = pe.Node(
        fsl.FLIRT(dof=6, no_search=True, bins=640, cost_func='mutualinfo'),
        name="Fmap_Mag_2_SBRef_Affine_Transform"
    )

    #  the following is a NEW HACK to fix extrapolation when fieldmap is too
    #  small
    #  applywarp -i ${vout}_fieldmaprads_unmasked -r ${vrefhead}
    #  --premat=${vout}_fieldmap2str.mat -o ${vout}_fieldmaprads2str_pad0
    aw_fmap_unmasked_sbref = pe.Node(fsl.ApplyWarp(relwarp=True),
                                     name="Apply_Warp_Fmap_Unmasked_2_SBRef")

    # fslmaths ${vout}_fieldmaprads2str_pad0 -abs -bin
    # ${vout}_fieldmaprads2str_innermask
    fmap_unmasked_abs = pe.Node(
        fsl.UnaryMaths(operation='abs'), name="Abs_Fmap_Unmasked_Warp")
    fmap_unmasked_bin = pe.Node(
        fsl.UnaryMaths(operation='bin'), name="Binarize_Fmap_Unmasked_Warp")

    # fugue --loadfmap=${vout}_fieldmaprads2str_pad0
    # --mask=${vout}_fieldmaprads2str_innermask --unmaskfmap
    # --unwarpdir=${fdir} --savefmap=${vout}_fieldmaprads2str_dilated
    fugue_dilate = pe.Node(
        fsl.FUGUE(unwarp_direction='x', dwell_time=dwell_time,
                  save_unmasked_fmap=True),
        name="Fmap_Dilating"
    )

    # epi_reg --epi=sub-S2529LVY1263171_task-nback_run-1_bold_brain
    # --t1=../Preprocessing_test_workflow/_subject_id_S2529LVY1263171/Bias_Field_Correction/sub-S2529LVY1263171_run-1_T1w_corrected.nii.gz
    # --t1brain=sub-S2529LVY1263171_run-1_T1w_corrected_bet_brain.nii.gz
    # --out=sub-S2529LVY1263171/func/sub-S2529LVY1263171_task-nback_run-1_bold_undistorted
    # --fmap=Topup_Fieldmap_rad.nii.gz
    # --fmapmag=fieldmap_topup_corrected.nii.gz
    # --fmapmagbrain=Magnitude_brain.nii.gz --echospacing=dwell_time
    # --pedir=x- -v

    sbref_stripped_overlay= pe.Node(
        niu.Function(
            input_names=["in_file", "overlay_file", "out_file"],
            output_names=["out_file"],
            function=stripped_brain_overlay
        ),
        name="sbref_stripped_overlay"
    )
    sbref_stripped_overlay.inputs.out_file = "sbref_stripped_overlay.png"

    datasink = pe.Node(
        interface=nio.DataSink(base_directory=op.join(settings['work_dir'],
                               "images")),
        name="datasink",
        parameterization=False
    )

    workflow.connect([
        (inputnode, flt_wmseg_sbref, [('sbref', 'reference')]),
        (inputnode, flt_wmseg_sbref, [('t1_seg', 'in_file')]),
        (flt_wmseg_sbref, invert_wmseg_sbref, [('out_matrix_file', 'in_file')]),
        (flt_wmseg_sbref, outputnode, [('out_file', 'wm_seg')]),
        (invert_wmseg_sbref, outputnode, [('out_file', 'sbref_2_t1_transform')]),
        (inputnode, sbref_bet, [('sbref', 'in_file')]),
        (inputnode, fugue_sbref, [
            ('sbref', 'in_file'),
            ('fmap_scaled', 'fmap_in_file')
        ]),
        (inputnode, flt_fmap_mag_brain_sbref_brain, [('mag_brain', 'in_file')]),
        (inputnode, fugue_sbref, [('fmap_mask', 'mask_file')]),
        (inputnode, flt_fmap_mag_sbref, [('in_topup', 'in_file')]),
        (inputnode, aw_fmap_unmasked_sbref, [('fmap_unmasked', 'in_file')]),
        #  (inputnode, flt_sbref_brain_t1_brain, [('stripped_t1', 'reference')]),
        #  (strip_corrected_sbref, flt_sbref_brain_t1_brain, [('out_file', 'in_file')]),
        #  (fugue_sbref, flt_sbref_2_t1, [('unwarped_file', 'in_file')]),
        #  (inputnode, flt_sbref_2_t1, [('t1', 'reference')]),
        #  (flt_sbref_brain_t1_brain, flt_sbref_2_t1, [('out_matrix_file', 'in_matrix_file')]),
        #  (inputnode, SBRef_skull_strip, [("sbref", "in_file")]),
        (fugue_sbref, strip_corrected_sbref, [('unwarped_file', 'in_file')]),
        # might need to switch to [strip_corrected_sbref, "in_file"] here
        # instead of [sbref_bet, "out_file"]
        # might need to switch to [strip_corrected_sbref, "in_file"] here
        # instead of [sbref_bet, "out_file"]
        (sbref_bet, flt_fmap_mag_brain_sbref_brain, [('out_file', 'reference')]),
        (fugue_sbref, flt_fmap_mag_sbref, [('unwarped_file', 'reference')]),
        (flt_fmap_mag_brain_sbref_brain, flt_fmap_mag_sbref, [
            ('out_matrix_file', 'in_matrix_file')
        ]),
        (flt_fmap_mag_sbref, aw_fmap_unmasked_sbref, [('out_matrix_file', 'premat')]),
        (fugue_sbref, aw_fmap_unmasked_sbref, [('unwarped_file', 'ref_file')]),
        (aw_fmap_unmasked_sbref, fmap_unmasked_abs, [('out_file', 'in_file')]),
        (fmap_unmasked_abs, fmap_unmasked_bin, [('out_file', 'in_file')]),
        (aw_fmap_unmasked_sbref, fugue_dilate, [('out_file', 'fmap_in_file')]),
        (fmap_unmasked_bin, fugue_dilate, [('out_file', 'mask_file')]),
        (sbref_bet, outputnode, [('out_file', 'sbref_brain')]),
        (fugue_sbref, outputnode, [('unwarped_file', 'sbref_unwarped')]),
        (fugue_dilate, outputnode, [('fmap_out_file', 'sbref_fmap')]),
        (flt_fmap_mag_sbref, outputnode, [('out_matrix_file', 'mag2sbref_matrix')]),
        (strip_corrected_sbref, outputnode, [('out_file', 'sbref_brain_corrected')]),
        (inputnode, sbref_stripped_overlay, [('sbref', 'overlay_file')]),
        (sbref_bet, sbref_stripped_overlay, [('mask_file', 'in_file')]),
        (sbref_stripped_overlay, datasink, [('out_file', '@sbref_stripped_overlay')])
    ])
    return workflow
