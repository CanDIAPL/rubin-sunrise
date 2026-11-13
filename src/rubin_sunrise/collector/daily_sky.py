"""
daily_sky.py: Populate file per day of daily visits for full sky

This module reads the Rubin Schedule viewer, locally stored database,
or locally stored simulated database, and populates a healpix array
with number of visits observed for each band

Public API
----------
- ``populate_sky`` - Populates the healpix array and saves file.

**Author:** Anna Ordog, for CanDIAPL
"""

import numpy as np
import healpy as hp
from astropy.io import fits
import os

from rubin_sunrise.collector.lsst import (
    rsv_service, 
    sim_service, 
    get_camera
)

BANDS = ('u', 'g', 'r', 'i', 'z', 'y')


def _set_up_healpix(nside):

    npix    = hp.nside2npix(nside)
    pix_all = np.arange(0,npix,1)
    coords  = hp.pix2ang(nside, pix_all, lonlat=True, nest=False)

    ra_all  = coords[0]
    dec_all = coords[1]

    return ra_all, dec_all, npix


def _make_hpx_masks(npix):

    hpx_masks = {}
    for band in BANDS:
        hpx_masks[band] = np.zeros(npix, dtype=np.float64)

    return hpx_masks

def _add_mask(hpx_masks, visits, idx_coord, camera, ra_all, dec_all):

    if visits['execution_status'][idx_coord] == 'Performed':

        idx_visit = camera(ra_all, dec_all, 
                        visits['s_ra'][idx_coord], 
                        visits['s_dec'][idx_coord], 
                        visits['rubin_rot_sky_pos'][idx_coord])

        dir1 = [visits['s_ra'][idx_coord], visits['s_dec'][idx_coord]]
        dir2 = [ra_all[idx_visit], dec_all[idx_visit]]
        ang_sep = hp.rotator.angdist(dir1, dir2, lonlat=True)*180/np.pi
        idx_visit = idx_visit[ang_sep < 10]

        band = visits['band'][idx_coord]

        hpx_masks[band][idx_visit] = hpx_masks[band][idx_visit]+1

    return hpx_masks

def _save_file(hpx_masks, nside, filepath, date):

    hdu = fits.PrimaryHDU()
    hdr = hdu.header

    hdr["PIXTYPE"] = ("HEALPIX", "HEALPIX pixelisation")
    hdr["ORDERING"] = ("RING", "Pixel ordering scheme: RING or NESTED")
    hdr["NSIDE"] = (nside, "Resolution parameter for HEALPIX")
    hdr["COORDSYS"] = ("C", "Coordinate system: G (Gal.), E (Ecl.), C (Eq.)")
    hdr["INDXSCHM"] = ("IMPLICIT", "Indexing: IMPLICIT or EXPLICIT")
    hdr["OBJECT"] = ("FULLSKY", "Sky coverage: FULLSKY or PARTIAL")

    for band in BANDS:
        filename = filepath + date+'_'+band+'.fits'
        print(filename)
        fits.writeto(filename, hpx_masks[band], header=hdr, overwrite=True)

    return


def populate_sky(nside, db_type, 
                 idx_day=None, date=None, save_file=False, filepath=None):

    ra_all, dec_all, npix = _set_up_healpix(nside)

    hpx_masks = _make_hpx_masks(npix)

    camera = get_camera()

    if db_type == 'sim':
        if idx_day == None:
            print("ERROR: simulated database needs day index!")
        visits = sim_service(idx_day)

    if db_type == 'rsv':
        if date == None:
            print("ERROR: RSV database needs date!")
        visits = rsv_service(date)

    for idx_coord in range(0,len(visits)):
        hpx_masks = _add_mask(hpx_masks, visits, idx_coord, camera, ra_all, dec_all)

    print(filepath)
    if save_file:
        if filepath == None:
            print("ERROR: Need file path to save!")
        _save_file(hpx_masks, nside, filepath, date)

    return hpx_masks


def loop_sky():

    dates = ['2026-11-06']

    for date in dates:
        populate_sky(128, 'rsv', 
                    idx_day=None, date=date, save_file=True, 
                    filepath= os.getenv('DATA_DIR', './data/'))

    return