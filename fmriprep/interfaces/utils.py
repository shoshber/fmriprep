#!/usr/bin/env python
# -*- coding: utf-8 -*-
# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:
#
# @Author: oesteban
# @Date:   2016-06-03 09:35:13
# @Last Modified by:   oesteban
# @Last Modified time: 2016-08-17 17:41:23
import os
import numpy as np
import os.path as op
from nipype.interfaces.base import (traits, isdefined, TraitedSpec, BaseInterface,
                                    BaseInterfaceInputSpec, File, InputMultiPath,
                                    OutputMultiPath)
from nipype.interfaces import fsl

class IntraModalMergeInputSpec(BaseInterfaceInputSpec):
    in_files = InputMultiPath(File(exists=True), mandatory=True,
                              desc='input files')

class IntraModalMergeOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='merged image')
    out_avg = File(exists=True, desc='average image')
    out_mats = OutputMultiPath(exists=True, desc='output matrices')
    out_movpar = OutputMultiPath(exists=True, desc='output movement parameters')

class IntraModalMerge(BaseInterface):
    input_spec = IntraModalMergeInputSpec
    output_spec = IntraModalMergeOutputSpec

    def __init__(self, **inputs):
        self._results = {}
        super(IntraModalMerge, self).__init__(**inputs)

    def _run_interface(self, runtime):
        if len(self.inputs.in_files) == 1:
            self._results['out_file'] = self.inputs.in_files[0]
            self._results['out_avg'] = self.inputs.in_files[0]
            # TODO: generate identity out_mats and zero-filled out_movpar

            return runtime

        magmrg = fsl.Merge(dimension='t', in_files=self.inputs.in_files)
        mcflirt = fsl.MCFLIRT(cost='normcorr', save_mats=True, save_plots=True,
                              ref_vol=0, in_file=magmrg.run().outputs.merged_file)
        mcres = mcflirt.run()
        self._results['out_mats'] = mcres.outputs.mat_file
        self._results['out_movpar'] = mcres.outputs.par_file
        self._results['out_file'] = mcres.outputs.out_file

        mean = fsl.MeanImage(dimension='T', in_file=mcres.outputs.out_file)
        self._results['out_avg'] = mean.run().outputs.out_file
        return runtime

    def _list_outputs(self):
        return self._results



class FormatHMCParamInputSpec(BaseInterfaceInputSpec):
    translations = traits.List(traits.Tuple(traits.Float, traits.Float, traits.Float),
                               mandatory=True, desc='three translations in mm')
    rot_angles = traits.List(traits.Tuple(traits.Float, traits.Float, traits.Float),
                             mandatory=True, desc='three rotations in rad')
    fmt = traits.Enum('confounds', 'movpar_file', usedefault=True,
                      desc='type of resulting file')


class FormatHMCParamOutputSpec(TraitedSpec):
    out_file = File(exists=True, desc='written file path')

class FormatHMCParam(BaseInterface):
    input_spec = FormatHMCParamInputSpec
    output_spec = FormatHMCParamOutputSpec

    def __init__(self, **inputs):
        self._results = {}
        super(FormatHMCParam, self).__init__(**inputs)

    def _run_interface(self, runtime):
        self._results['out_file'] = _tsv_format(
            self.inputs.translations, self.inputs.rot_angles,
            fmt=self.inputs.fmt)
        return runtime

    def _list_outputs(self):
        return self._results


def _tsv_format(translations, rot_angles, fmt='confounds'):
    parameters = np.hstack((translations, rot_angles)).astype(np.float32)

    if fmt == 'movpar_file':
        out_file = op.abspath('movpar.txt')
        np.savetxt(out_file, parameters)
    elif fmt == 'confounds':
        out_file = op.abspath('movpar.tsv')
        np.savetxt(out_file, parameters,
                   header='X\tY\tZ\tRotX\tRotY\tRotZ',
                   delimiter='\t')
    else:
        raise NotImplementedError

    return out_file


def nii_concat(in_files):
    from nibabel.funcs import concat_images
    import os
    new_nii = concat_images(in_files, check_affines=False)

    new_nii.to_filename("merged.nii.gz")

    return os.path.abspath("merged.nii.gz")


def reorient(in_file):
    import os
    import nibabel as nb

    _, outfile = os.path.split(in_file)
    nii = nb.as_closest_canonical(nb.load(in_file))
    nii.to_filename(outfile)
    return os.path.abspath(outfile)


def prepare_roi_from_probtissue(in_file, epi_mask, epi_mask_erosion_mm=0,
                                erosion_mm=0, min_percent=9, max_percent=14):
    """ min_percent and max_percent defaults are based on results from BEAST with erosion_mm=0 and
    epi_mask_erosion_mm=10 """
    import os
    import nibabel as nb
    import scipy.ndimage as nd

    probability_map_nii = nb.load(in_file)
    probability_map_data = probability_map_nii.get_data()

    # thresholding
    probability_map_data[probability_map_data < 0.95] = 0
    probability_map_data[probability_map_data != 0] = 1

    epi_mask_nii = nb.load(epi_mask)
    epi_mask_data = epi_mask_nii.get_data()
    if epi_mask_erosion_mm:
        epi_mask_data = nd.binary_erosion(epi_mask_data,
                                      iterations=int(epi_mask_erosion_mm/max(probability_map_nii.header.get_zooms()))).astype(int)
        eroded_mask_file = os.path.abspath("erodd_mask.nii.gz")
        nb.Nifti1Image(epi_mask_data, epi_mask_nii.affine, epi_mask_nii.header).to_filename(eroded_mask_file)
    else:
        eroded_mask_file = epi_mask
    probability_map_data[epi_mask_data != 1] = 0

    # shrinking
    if erosion_mm:
        iter_n = int(erosion_mm/max(probability_map_nii.header.get_zooms()))
        probability_map_data = nd.binary_erosion(probability_map_data,
                                                 iterations=iter_n).astype(int)


    new_nii = nb.Nifti1Image(probability_map_data, probability_map_nii.affine,
                             probability_map_nii.header)
    new_nii.to_filename("roi.nii.gz")
    return os.path.abspath("roi.nii.gz"), eroded_mask_file

TBD=1 #######

def _check_brain_volume(in_WM, in_CSF, brain_mask, min_percent=TBD, max_percent=TBD):
    """ check that the brain volume indicated by the aCompCor mask (`acc_mask`) divided by the
    brain volume indicated by the brain_mask is between `min_percent` and `max_percent`, inclusive.
    `*_percent` is a value between 0 and 1. If it isn't, that suggests that the results of aCompCor
    will not perform well. return value `out_CSF` might be None """
    import warnings

    import nibabel as nb
    import numpy as np

    def _combine_masks(masks):
        target_sum = len(masks)

        combined_data = masks[0]
        for mask in masks[1:]:
            combined_data = combined_data.add(mask)

        combined_mask_data = np.zeroes_like(combined_data)
        combined_mask_data[combined_data == target_sum] = 1 # all masks had a 1
        return combined_mask_data

    def _percent_volume(mask):
        return mask.sum(axis=None) / brain_mask_volume

    def _check_volume(masks, min_percent, max_percent, roi_name):
        percent = _percent_volume(_combine_masks(masks))
        if percent < min_percent or percent > max_percent:
            return ('The {} ROI is too small or too big ({} percent of total brain '
                    'volume)').format(roi_name, percent)
        else:
            return 'good'

    for percent in [min_percent, max_percent]:
        assert percent >= 0
        assert percent <= 1

    wm_mask_data = nb.load(in_WM).get_data()
    csf_mask_data = nb.load(in_CSF).get_data()
    brain_mask_data = nb.load(brain_mask).get_data()

    assert wm_mask_data.shape == brain_mask_data.shape
    assert csf_mask_data.shape == brain_mask_data.shape

    valid = True
    brain_mask_volume = brain_mask_data.sum(axis=None)

    csf_volume_status = _check_volume([csf_mask_data], min_percent, max_percent, 'CSF')
    if csf_volume_status != 'good':
        warnings.warn(wm_volume_status + ' aCompCor will be calculated using white matter only.')
        out_CSF = None
        masks = [wm_mask_data]
    else:
        out_CSF = in_CSF
        masks = [wm_mask_data, csf_mask_data]

    roi_volume_status = _check_volume(masks, min_percent, max_percent, 'aCompCor')
    if roi_volume_status != 'good':
        warnings.warn(roi_volume_status)
        valid = False

    return in_WM, out_CSF, valid
