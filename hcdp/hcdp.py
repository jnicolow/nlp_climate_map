"""
This scrip has code to download data using the Hawaii Climate Data Portals APIs

Joel Nicolow, Coastal Research Collaborative 2025
"""


import os
import requests
from io import BytesIO
import rasterio
from rasterio.io import MemoryFile
import matplotlib.pyplot as plt
import numpy as np
from datetime import date
import calendar

class FileDownloadAPI:
    """
    Find API documentation here: https://docs.google.com/document/d/1XlVR6S6aCb7WC4ntC4QaRzdw0i6B-wDahDjsN1z7ECk/edit?tab=t.0
    after base url is: <product type>/<aggregation>/<period>/<extent>[/<fill>]/<filetype>/<year>[/<month>]/rainfall_<production>_<period>_<extent>[_<fill>]_<filetype>_<year>_<month>[_<day>].<extension>
    e.g. file
    """
    def __init__(self,  
            product_type: str,  # Product type can either be 'rainfall' or 'temperature'
            year: str,           # Year as a 4-digit integer or string (e.g. 2022)
            month: str = None,   # Month as a 2-digit string or integer (optional)
            day: str = None,     # Day as a 2-digit string or integer (optional)
            aggregation: str = "mean"  # Aggregation type ('min', 'max', or 'mean')
            
        ):
        """
        :param product_type: str, "rainfall" or "temperature"
        :param year: str or int, 4-digit year (e.g., 2022)
        :param month: str or int, 2-digit month (optional)
        :param day: str or int, 2-digit day (optional)
        :param aggregation: str, "min", "max", or "mean"
        """
        if not product_type in ['rainfall', 'temperature']: raise ValueError("product_type should be rainfall or temperature")
        self.product_type = product_type # this is rainfall or temperature

        if int(year) >= 1990: production = 'new'
        else: production = 'legacy'
        # if not production in ['new', 'legacy']: raise ValueError("production should be new (1990-present) or legacy (1920-2012)")
        self.production = production

        if not aggregation in ["min", 'max', 'mean']: raise ValueError("aggregation should be min max or mean")
        self.aggregation = aggregation

        # if not period in ['month', 'day']: raise ValueError("period should be 'month' or 'day'")
        self.period = 'month'

        # if not extent in ['statewide', 'bi', 'ka', 'mn', 'oa']: raise ValueError("extent should be statewide, bi (big island), ka (Kauai County), mn (Maui County), or oa (Honolulu County)")
        self.extent = 'statewide' # NOTE only statewide is avaible

        # if not fill in ['raw', 'partial', None]: raise ValueError('fill should be raw (no QAQC) or partial (QAQC missing values filled)')
        # self.fill = fill
        self.fill = None # str or None, 'raw' or 'partial' (optional)
        if self.fill is None: self.fill = '' # its optional so can not include it in the url


        # if self.product_type == 'rainfall' and not filetype in ['data_map', 'se', 'anom', 'anom_se', 'metadata', 'station_data']: raise ValueError("incorrect filetype, for rainfall filetypes are: 'data_map', 'se', 'anom', 'anom_se', 'metadata', 'station_data'")
        # if self.product_type == 'temperature' and not filetype in ['data_map', 'se', 'metadata', 'station_data']: raise ValueError("incorrect filetype, for temperature filetypes are: 'data_map', 'se', 'metadata', 'station_data'")
        self.filetype = 'data_map'  # Filetype for the data ('data_map', 'se', 'anom', 'anom_se', 'metadata', 'station_data')


        extention_dict = {'data_map':'tif', 'se':'tif', 'anom':'tif', 'anom_se':'tif', 'metadata':'txt', 'station_data':'csv'}
        self.extention = extention_dict[self.filetype] # this wil be like 'csv' for example

        if product_type == 'new' and not int(year) >= 1990: raise ValueError("if production is 'new' year must be >= 1990")
        if product_type == 'legacy' and (not int(year) >= 1920 or not int(year) <= 2012) and not int: raise ValueError("if production is 'legacy' year must be 1920 to 2012")
        self.year = year

        if not month is None and int(month) > 12: raise ValueError('month must be 0 to 12')
        self.month = month
        if not self.month is None: self.month = f"{int(self.month):02d}"

        if not day is None and int(day) > 31: raise ValueError('day must be <= 31')
        self.day = day
        if self.day is None: self.day = '' # its optional so can not include it in the url
        else: self.day = f"{int(self.day):02d}"

        # check if date is valid
        today = date.today()
        y = int(self.year)
        m = int(self.month) if self.month else 12  # default to Dec if missing so that we make sure whole year is there (doesnt really matter cuz month cannot be none)
        d = int(self.day) if self.day else calendar.monthrange(y, m)[1]     # default to 31 if missing
        input_date = date(y, m, d)

        if input_date > today:
            raise ValueError(f'This date ({input_date}) has not occured yet ({today}) cannot querry data')
      

        self.base_url = "https://ikeauth.its.hawaii.edu/files/v2/download/public/system/ikewai-annotated-data/HCDP/production/"    
        # NOTE the format that actually work is slightly different than that fiven on the API documentation page    
        if self.product_type == 'rainfall':
            url_extension = f'{self.product_type}/{self.production}/{self.period}/{self.extent}/{self.fill}/{self.filetype}/{self.year}/{self.product_type}_{self.production}_{self.period}_{self.extent}_{self.fill}_{self.filetype}_{self.year}_{self.month}_{self.day}.{self.extention}'
        else:
            print(self.aggregation)
            url_extension = f'{self.product_type}/{self.aggregation}/{self.period}/{self.extent}/{self.fill}/{self.filetype}/{self.year}/{self.product_type}_{self.aggregation}_{self.period}_{self.extent}_{self.fill}_{self.filetype}_{self.year}_{self.month}_{self.day}.{self.extention}'
        url_extension = url_extension.replace('//', '/').replace('__', '_').replace('_.', '.')
        print(url_extension)

        self.url = f'{self.base_url}{url_extension}'

        self.dataset = None # NOTE this is defined with get_data



    def download_file(self, save_path):
        response = requests.get(self.url, verify=False)  # verify=False if you want to ignore SSL verification
    
        if response.status_code == 200:
            # Save the file content to the specified output filename
            with open(save_path, 'wb') as file:
                file.write(response.content)
            print(f"File downloaded successfully: {save_path}")
        else:
            print(f"Failed to download file. HTTP Status code: {response.status_code}")


    def get_data(self):
        if self.month is None:
            # NOTE then we need to get a year average
            return get_year_avg(product_type=self.product_type, year=self.year, aggregation=self.aggregation)

        response = requests.get(self.url, verify=False)

        if response.status_code == 200:
            file_bytes = BytesIO(response.content)
            dataset = rasterio.open(file_bytes)
            self.dataset = dataset
            return dataset
        else:
            raise Exception(f"Failed to download file. HTTP Status code: {response.status_code}")
        
    def plot_raster(self):
        if self.dataset is None:
            print('Call get_data to define dataset first')
        else:
            plot_raster_band(self.dataset)

            



def plot_raster_band(dataset, invalid_threshold=-1e+20, missing_val=-1):
    band1 = dataset.read(1)  # read the first and only band

    # fill the water as value -1
    band1[band1 < invalid_threshold] = missing_val

    # get the non water area
    valid_mask = band1 > missing_val

    # scale only the islands (leave out the water surface which is a hugely negatice number -3.4e+38)
    min_val = np.min(band1[valid_mask])
    max_val = np.max(band1[valid_mask])
    band1_scaled = np.full_like(band1, missing_val)
    band1_scaled[valid_mask] = (band1[valid_mask] - min_val) / (max_val - min_val)
    # band1_scaled = band1

    plt.figure(figsize=(10, 8))
    plt.imshow(band1_scaled, cmap='viridis')
    plt.colorbar(label='Normalized Value')
    plt.title("Scaled Raster (Masked Fill Values)")
    plt.xlabel("Pixel X")
    plt.ylabel("Pixel Y")
    plt.tight_layout()
    plt.show()



def create_in_memory_raster(mean_image, src):
    memfile = MemoryFile()  # This creates the memory file that will hold the GeoTIFF
    
    dataset_in_memory = memfile.open(driver='GTiff', 
                                    height=mean_image.shape[0], 
                                    width=mean_image.shape[1], 
                                    count=1, 
                                    dtype=mean_image.dtype, 
                                    crs=src.crs, 
                                    transform=src.transform)
    
    dataset_in_memory.write(mean_image, 1)
    
    return dataset_in_memory

def get_year_avg(product_type:str, year:int, aggregation:str='mean'):
    """
    :param product_type: rainfall or temperature
    :param year: int or str 4-digit year
    :param aggregation: min mean or max
    """
    images = []

    # Loop through each month and download the raster data
    for month in range(1, 13):
        test = FileDownloadAPI(product_type, year=year, month=month, aggregation=aggregation)
        dataset = test.get_data()
        image_data = dataset.read(1)  # Read the first band (assuming one band per image)
        images.append(image_data)

    stacked_images = np.stack(images, axis=0)
    mean_image = np.mean(stacked_images, axis=0)
    return create_in_memory_raster(mean_image, dataset)