# emacs: -*- mode: python; py-indent-offset: 4; indent-tabs-mode: nil -*-
# vi: set ft=python sts=4 ts=4 sw=4 et:

import os
import numpy as np
import tables

from brainDecTool.util import configParser
from brainDecTool.io import nifti as bdnifti
from brainDecTool.math import corr2_coef
import util as vutil

def roi2nifti(fmri_table):
    """Save ROI as a nifti file."""
    #-- load ROI mask
    l_v1_roi = fmri_table.get_node('/roi/v1lh')[:]
    r_v1_roi = fmri_table.get_node('/roi/v1rh')[:]
    l_v2_roi = fmri_table.get_node('/roi/v2lh')[:]
    r_v2_roi = fmri_table.get_node('/roi/v2rh')[:]
    l_v3_roi = fmri_table.get_node('/roi/v3lh')[:]
    r_v3_roi = fmri_table.get_node('/roi/v3rh')[:]
    l_v3a_roi = fmri_table.get_node('/roi/v3alh')[:]
    r_v3a_roi = fmri_table.get_node('/roi/v3arh')[:]
    # merge ROIs in both hemisphere
    roi_mask = l_v1_roi + r_v1_roi*2 + l_v2_roi*3 + r_v2_roi*4 + \
               l_v3_roi*5 + r_v3_roi*6 + l_v3a_roi*7 + r_v3a_roi*8
    nmask = vutil.convert2ras(roi_mask)
    bdnifti.save2nifti(np.around(nmask), 'nmask.nii.gz')

def gen_mean_vol(fmri_table):
    """Make a mean response map as a reference volume."""
    data = fmri_table.get_node('/rt')[:]
    # replace nan to zero
    data = np.nan_to_num(data)
    mean_data = np.mean(data, axis=1)
    vol = np.zeros((18, 64, 64))
    
    for i in range(data.shape[0]):
        c = vutil.idx2coord(i)
        vol[c[0], c[1], c[2]] = mean_data[i]
    
    nvol = vutil.convert2ras(vol)
    bdnifti.save2nifti(nvol, 'mean_vol.nii.gz')

def cross_modal_corr(fmri_ts, feat_ts):
    """Compute cross-modal correlation between fmri response and image
    features.
    """
    # to reduce computational burden, we compute Pearson's r iteratively
    fmri_size = fmri_ts.shape[0]
    feat_size = feat_ts.shape[0]
    corr_mtx = np.zeros((fmri_size, feat_size), dtype=np.float16)
    for i in range(feat_size):
        print 'Iter %s of %s' %(i, feat_size)
        tmp = feat_ts[i, :].reshape(1, -1)
        corr_mtx[:, i] = corr2_coef(fmri_ts, tmp)[:, 0]
    return corr_mtx

def retinotopic_mapping(data_dir, fmri_ts, feat_ts):
    """Make the retinotopic mapping using activation map from CNN."""
    retino_dir = os.path.join(data_dir, 'retinotopic')
    if not os.path.exists(retino_dir):
        os.mkdir(retino_dir, mode=0755)
    corr_mtx = cross_modal_corr(fmri_ts, feat_ts)
    corr_file = os.path.join(retino_dir, 'fmri_feat1_corr.npy')
    np.save(corr_file, corr_mtx)
    # TODO: find the maximum correlation coefficient across CNN features and
    # image spatial position.

if __name__ == '__main__':
    """Main function."""
    # config parser
    cf = configParser.Config('config')
    data_dir = cf.get('base', 'path')
    stim_dir = os.path.join(data_dir, 'cnn_rsp')

    tf = tables.open_file(os.path.join(data_dir, 'VoxelResponses_subject1.mat'))
    #tf.list_nodes
    #roi2nifti(tf)
    #gen_mean_vol(tf)

    # retinotopic mapping
    # load fmri response from validation dataset
    rv_ts = tf.get_node('/rv')[:]
    # data.shape = (73728, 540)
    rv_ts = np.nan_to_num(rv_ts)
    # load convolved cnn activation data
    feat1_file = os.path.join(stim_dir, 'feat1_trs.npy')
    # data.shape = (290400, 540)
    feat1_ts = np.load(feat1_file, mmap_mode='r')
    corr_mtx = retinotopic_mapping(data_dir, rv_ts, feat1_ts)


    tf.close()

    #roi = tf.get_node('/roi/v1lh')[:].flatten()
    #v1lh_idx = np.nonzero(roi==1)[0]
    #v1lh_resp = data[v1lh_idx]

