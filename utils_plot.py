import os
import numpy as np
from netCDF4 import Dataset

def load_bands(datepath, band_list):
    """
    Retrieve a dict of band arrays from a date path
    """
    
    arr_band = Dataset(datepath, 'r', format='NETCDF4_CLASSIC')
    
    band_dict = {}
    for band in band_list:
        b = band_list[band]
        try:
            band_dict[b] = arr_band.variables[b][:] # band array
        except:
            continue
        
    return band_dict

def color_composite(b0, b1, b2, clip=True):
    """
    Compose an image from three different bands

    Parameters
    ----------
    clip: bool
        Clip very low/high pixels to make the image brighter (another possibility
        would be to take the logarithm)
    """
    if clip:
        b0 = np.clip(b0, np.percentile(b0, 2.5), np.percentile(b0, 97.5))
        b1 = np.clip(b1, np.percentile(b1, 2.5), np.percentile(b1, 97.5))
        b2 = np.clip(b2, np.percentile(b2, 2.5), np.percentile(b2, 97.5))

    im = np.array([b0, b1, b2])
    im = im * 255 / np.amax(im)
    im = np.moveaxis(im, 0, -1)
    return im.astype('uint8')

def landsat_wq(band_dict, index):
        
    #Water mask
    ndwi = (band_dict['SRB3'] - band_dict['SRB5']) / (band_dict['SRB3'] + band_dict['SRB5'])
    ndwi[ndwi <=0] = np.nan #replace 0's with Nan's
    ndwi = np.ma.masked_where(condition=np.isnan(ndwi), a=ndwi)
            
    if index == 'chl':
        
        chl = (band_dict['SRB5'] - band_dict['SRB4']) / (band_dict['SRB2'] + band_dict['SRB3'])
        chl[ndwi.mask] = np.nan
        chl = np.ma.masked_where(condition=np.isnan(chl), a=chl)
        
        return chl
    
    elif index == 'Temp':
        
        Temp = band_dict['SRB10']
        Temp[ndwi.mask] = np.nan
        Temp = np.ma.masked_where(condition=np.isnan(Temp), a=Temp)
        
        return Temp
    
    elif index == 'Turb':
        
        # NDTI = Red - Green / Red + Green
        ndti = (band_dict['SRB4'] - band_dict['SRB3']) / (band_dict['SRB4'] + band_dict['SRB3'])
        ndti[ndwi.mask] = np.nan
        ndti = np.ma.masked_where(condition=np.isnan(ndti), a=ndti)
        
        return ndti
    
def sentinel_wq(band_dict, index):
        
    # NDWI = Green - NIR / Green + NIR -> B3 - B8 / B3 + B8
    ndwi = (band_dict['B3'] - band_dict['B8']) / (band_dict['B3'] + band_dict['B8'])
    ndwi[ndwi <=0] = np.nan #replace 0's with Nan's
    ndwi = np.ma.masked_where(condition=np.isnan(ndwi), a=ndwi)
    
    if index == 'chl':
        
        chl = (band_dict['SRB8A'] - band_dict['B4']) / (band_dict['B2'] + band_dict['B3'])
        chl[ndwi.mask] = np.nan
        chl = np.ma.masked_where(condition=np.isnan(chl), a=chl)
        
        return chl
    
    elif index == 'Turb':
        
        # NDTI = Red - Green / Red + Green
        ndti = (band_dict['B4'] - band_dict['B3']) / (band_dict['B4'] + band_dict['B3'])
        ndti[ndwi.mask] = np.nan
        ndti = np.ma.masked_where(condition=np.isnan(ndti), a=ndti)
        
        return ndti