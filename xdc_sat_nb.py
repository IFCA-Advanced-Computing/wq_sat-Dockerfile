"""
XDC_sat notebook utils 

Author: Daniel Garcia Diaz
Date: August 2018
"""
#APIs
import os
import requests
import argparse
import json
from netCDF4 import Dataset
from osgeo import gdal, osr
import datetime
import matplotlib.pyplot as plt
import numpy as np

#Subfunctions
import utils_plot

#Map
from ipyleaflet import Map, basemaps, basemap_to_tiles, DrawControl

#widget
import ipywidgets as widgets
from ipywidgets import HBox, VBox, Layout
from ipywidgets import AppLayout, Button, GridspecLayout
from IPython.display import display
from IPython.display import clear_output

def get_coordinates(coord):
            
    W = np.round(coord[0][0] - 360, 3)
    S = np.round(coord[0][-1], 3)
    E = np.round(coord[2][0] - 360, 3)
    N = np.round(coord[2][-1], 3)

    coordinates = {}
    coordinates['W'], coordinates['S'] = W, S
    coordinates['E'], coordinates['N'] = E, N

    return coordinates

def load_regions():
    
    if os.path.isfile('regions.json'):
        
        #load the downloaded files
        with open('regions.json') as file:
            regions = json.load(file)
    
    else:
        regions = {"CdP":{"coordinates":{"W":-2.83, "S":41.82, "E":-2.67, "N":41.90}}, 
                   "Ebro":{"coordinates":{"W": -4.132, "S": 42.968, "E": -3.824, "N": 43.06}}, 
                   "ElVal":{"coordinates":{"W":-1.802, "S":41.875, "E":-1.791, "N":41.881}}}
        
        with open('regions.json', 'w') as file:
            json.dump(regions, file, indent=4)
            
    return regions

def get_access_token(url):
    
    if url is None:
        url = 'https://iam.extreme-datacloud.eu/token'
    
    #TODO manage exceptions
    access_token = os.environ['OAUTH2_AUTHORIZE_TOKEN']
    refresh_token = os.environ['OAUTH2_REFRESH_TOKEN']

    IAM_CLIENT_ID = os.environ['IAM_CLIENT_ID']
    IAM_CLIENT_SECRET = os.environ['IAM_CLIENT_SECRET']

    data = {'refresh_token': refresh_token, 
            'grant_type': 'refresh_token', 
            'client_id':IAM_CLIENT_ID, 
            'client_secret':IAM_CLIENT_SECRET}
    
    headers = {'Content-Type': 'application/json'}
    url = url + "?grant_type=refresh_token&refresh_token="
    url = url + refresh_token + '&client_id='
    url = url + IAM_CLIENT_ID + '&client_secret=' + IAM_CLIENT_SECRET
    url = url + "&scope=openid email profile offline_access fts:submit-transfer"

    r = requests.post(url, headers=headers) #GET token
    print("Requesting access token: %s" % r.status_code) #200 means that the resource exists
    access_token = json.loads(r.content)['access_token']
    
    return access_token


def launch_orchestrator_sat_job(sat_args):

    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+access_token}
    tosca_file = '.SAT_DATA_D.yml'

    with open(tosca_file, 'r') as myfile:
        tosca = myfile.read()
    
    sat = json.dumps(sat_args)
    sat = sat.replace(" ", "")
    
    data = {"parameters" : {
                "cpus" : 1,
                "mem" : "8192 MB",
                "onedata_provider" : "vm027.pub.cloud.ifca.es",
                "onedata_zone" : "https://onezone.cloud.cnaf.infn.it",
                "onedata_sat_space" : "XDC_LifeWatch",
                "onedata_mount_point": "/mnt/onedata",
                "sat_args" : sat,
                "region" : sat_args['region'],
                "start_date" : sat_args['start_date'],
                "end_date" : sat_args['end_date']
                 },
            "template" : tosca
            }
    print ('search parameters: {}'.format(data))

    url = 'https://xdc-paas.cloud.ba.infn.it/orchestrator/deployments/'
    r = requests.post(url, headers=headers,data=json.dumps(data)) #GET
    print("Status code SAT: %s" % r.status_code) #200 means that the resource exists
    print(r.headers)
    txt = json.loads(r.text)
    print (json.dumps(txt, indent=2, sort_keys=True))
    deployment_id = json.loads(r.content)['uuid']
    print("Deployment ID: %s" % deployment_id)
    return deployment_id
    
def orchestrator_job_status(deployment_id):
    #TODO manage exceptions
    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    url =  'https://xdc-paas.cloud.ba.infn.it/orchestrator/deployments/'+deployment_id
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+access_token}
    r = requests.get(url, headers=headers) #GET token
    print("Status code: %s" % r.status_code)
    txt = json.loads(r.text)
    print (json.dumps(txt, indent=2, sort_keys=True))
    #print(r.text)
    #print(r.reason)
    return r.content

def orchestrator_list_deployments(orchestrator_url):
    
    #TODO manage exceptions
    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    
    if orchestrator_url is None:
        orchestrator_url = 'https://xdc-paas.cloud.ba.infn.it/orchestrator/'
    
    url = orchestrator_url + 'deployments'
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+access_token}
    r = requests.get(url, headers=headers) #GET
    return json.loads(r.content)['content']

############################## MENU ##################################

######################################
#########  Data Ingestion  ###########
######################################

#Date picker to choose the initial date
ini_date = widgets.DatePicker(
    description='Initial Date',
    disabled=False)

#Date picker to choose the end date
end_date = widgets.DatePicker(
    description='End Date',
    disabled=False)

#To choose the satellite. Drop down to select one
satellite = widgets.Dropdown(
    options=['Sentinel2', 'Landsat8', 'All'],
    value='All',
    description='Satellite:',
    disabled=False)

#To choose the region. Slot to write the name
name = widgets.Text(
    value = None,
    description='Region:',
    disabled=False)

#Slider for the cloud coverage
cloud = widgets.IntSlider(
    description='Cloud Coverage',)

#Run
namebutton = widgets.Button(description='Run')
mapbutton = widgets.Button(description='Run')
out = widgets.Output()

#widget without map
box = HBox(children=[ini_date, end_date, satellite])
box2 = HBox(children=[name, cloud])
grid = GridspecLayout(3, 3)
grid[0, :], grid[1, :], grid[2,1] = box, box2, namebutton

ingestion = VBox(children=[grid, out])

#Map to select the coordinates
m = Map(center=(41.975381, 358.489681), basemap=basemaps.Esri.WorldStreetMap, zoom=5)
draw_control = DrawControl(rectangle = {"shapeOptions": {"fillColor": "#fca45d",
                                                        "color": "#fca45d",
                                                        "fillOpacity": 0.7}})

draw_control.clear_polygons()
m.add_control(draw_control)

#To group the widgets
tab = VBox(children=[ini_date, end_date, satellite, name, cloud, mapbutton])

#Create grid to fill it in with widgets
mapgrid = GridspecLayout(2, 2)
mapgrid[:, 0], mapgrid[:, 1] = m, tab

def namebutton_clicked(namebutton):

    #load the downloaded files
    regions = load_regions()
    
    if name.value in list(regions.keys()):
        
        coord = regions[name.value]["coordinates"]
        
        inidate = (ini_date.value).strftime('%Y-%m-%d')
        enddate = (end_date.value).strftime('%Y-%m-%d')
            
        sat_args ={"start_date":inidate,
                   "end_date":enddate,
                   "region":name.value,
                   "coordinates":coord,
                   "cloud":cloud.value,
                   "sat_type":satellite.value}
        
        launch_orchestrator_sat_job(sat_args)
    
    else:

        ingestion = VBox(children=[mapgrid, out])
        user_interface.children = [ingestion, status, visualization]

namebutton.on_click(namebutton_clicked)

def mapbutton_clicked(mapbutton):
    
    coord = get_coordinates(draw_control.last_draw['geometry']['coordinates'][0])

    inidate = (ini_date.value).strftime('%Y-%m-%d')
    enddate = (end_date.value).strftime('%Y-%m-%d')
            
    sat_args ={"start_date":inidate,
               "end_date":enddate,
               "region":name.value,
               "coordinates":coord,
               "cloud":cloud.value,
               "sat_type":satellite.value}

    launch_orchestrator_sat_job(sat_args)
    
mapbutton.on_click(mapbutton_clicked)

######################################
##############  Jobs  ################
######################################

job_list=[]
for e in orchestrator_list_deployments(None):
    job_list.append('ID: ' + e['uuid'] + ' | Creation time: ' + e['creationTime'] + ' | Status: ' + e['status'])

selection_jobs = widgets.Select(
    options=job_list,
    value=None,
    # rows=10,
    description='Job List',
    disabled=False,
    layout=Layout(width='90%'))

button2 = widgets.Button(
    description='Show deployment',)

out2 = widgets.Output()

@button2.on_click
def model_on_click(b):
    with out2:
        clear_output()
        jb = selection_jobs.value
        orchestrator_job_status(jb[jb.find('ID: ', 0)+len('ID: '):jb.find(' | ')])

status = VBox(children=[selection_jobs, button2, out2])

######################################
#######  Data Visualization  #########
######################################


######################################## Utils ##########################################

path = '/home/jovyan/datasets/XDC_LifeWatch'
        
paths = {'main_path': path}

##################################### Plot Functions #########################################

def band_on_change(v):

    dataset= Dataset(paths['file_path'], 'r', format='NETCDF4_CLASSIC')
    band = bands_desc[v['new']]
    data = dataset[band][:]
    vmin, vmax, mean, std = np.amin(data), np.amax(data), np.mean(data), np.std(data)
    stats = "min = {}, Max = {}".format(vmin, vmax)
    stats2 = "mean = {}, std = {}".format(mean, std)
    
    with out_plot:
        
        clear_output()
        
        plt.figure(figsize=(7,7))
        
        # Plot the image
        plt.imshow(data, vmin=vmin, vmax=vmax, cmap='Greys')

        # Add a colorbar
        plt.colorbar(label='Brightness', extend='both', orientation='vertical', pad=0.05, fraction=0.05)

        # Title axis
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.tick_params(axis='both', which='both', bottom=False, top=False, right=False, left=False, labelbottom=False, labelleft=False)

        # Add a title
        plt.title('{}'.format(v['new']), fontweight='bold', fontsize=10, loc='left')
        plt.suptitle(stats, x=0.90, y=0.90, fontsize='large')
        plt.suptitle(stats2, x=0.95, y=0.95, fontsize='large')
        
        # Show the image
        plt.show()        
        
def index_on_change(v):
    
    band_dict = utils_plot.load_bands(paths['file_path'], bands_desc)
   
    if file.startswith('LC'):    
        arr_index = utils_plot.landsat_wq(band_dict, v['new'])
    
    elif file.startswith('S2'):
        arr_index = utils_plot.sentinel_wq(band_dict, v['new'])
        
    vmin, vmax, mean, std = np.amin(arr_index), np.amax(arr_index), np.mean(arr_index), np.std(arr_index)
    stats = "min = {}, Max = {}".format(vmin, vmax)
    stats2 = "mean = {}, std = {}".format(mean, std)
    
    with out_plot:
        
        clear_output()
        
        plt.figure(figsize=(7,7))
        
        # Plot the image
        plt.imshow(arr_index, vmin=vmin, vmax=vmax, cmap='Greys')

        # Add a colorbar
        plt.colorbar(label='Brightness', extend='both', orientation='vertical', pad=0.05, fraction=0.05)

        # Title axis
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.tick_params(axis='both', which='both', bottom=False, top=False, right=False, left=False, labelbottom=False, labelleft=False)

        # Add a title
        plt.title('{}'.format(v['new']), fontweight='bold', fontsize=10, loc='left')
        plt.suptitle(stats, x=0.90, y=0.90, fontsize='large')
        plt.suptitle(stats2, x=0.95, y=0.95, fontsize='large')
        
        # Show the image
        plt.show()
    
    
        
def date_on_change(v):
    
    global out_plot, bands_desc, file   
    
    clear_output()
    
    file = str(folders[v['new']])
    file_path = os.path.join(paths['region_path'], file)
    paths['file_path'] = file_path
    
    if file.startswith('LC'):
                
        bands_desc = {'B1 [435nm-451nm]':'SRB1',
                     'B2 Blue [452nm-512nm]':'SRB2',
                     'B3 Green [533nm-590nm]':'SRB3',
                     'B4 Red [636nm-673nm]':'SRB4',
                     'B5 [851nm-879nm]':'SRB5',
                     'B6 [1566nm-1651nm]':'SRB6',
                     'B7 [2107nm-2294nm]':'SRB7',
                     'B8 [503nm-676nm]':'B8',
                     'B9 [1363nm-1384nm]':'SRB9',
                     'B10 [1060nm-1119nm]':'SRB10',
                     'B11 [1150nm-1251nm]':'SRB11'}
        
        index_list = ['chl', 'Turb', 'Temp']
        
    elif file.startswith('S2'):
        
        bands_desc = {'B1 [443 nm]':'SRB1',
                     'B2 Blue [490 nm]':'B2',
                     'B3 Green [560 nm]':'B3',
                     'B4 Red [665 nm]':'B4',
                     'B5 [705 nm]':'SRB5',
                     'B6 [740 nm]':'SRB6',
                     'B7 [783 nm]':'SRB7',
                     'B8 [842 nm]':'B8',
                     'B8A [865 nm]':'SRB8A',
                     'B9 [945 nm]':'SRB9',
                     'B10 [1375 nm]':'SRB10',
                     'B11 [1610 nm]':'SRB11',
                     'B12 [2190 nm]':'SRB12'}
        
        index_list = ['chl', 'Turb']
    
    bands = list(bands_desc.keys())
    
    b = widgets.ToggleButtons(options=[bands[n] for n in range(len(bands))],
                              description='Raw Bands',
                              value = None,
                              button_style='',)
    
    b.observe(band_on_change, names='value')
    
    R = widgets.Dropdown(options=[bands[n] for n in range(len(bands))],
                         value=bands[0],
                         description='R',
                         disabled=False,)
    
    G = widgets.Dropdown(options=[bands[n] for n in range(len(bands))],
                         value=bands[0],
                         description='G',
                         disabled=False,)
    
    B = widgets.Dropdown(options=[bands[n] for n in range(len(bands))],
                         value=bands[0],
                         description='B',
                         disabled=False,)
    
    RGB_button = widgets.Button(description='RGB Plot',)
    
    @RGB_button.on_click
    def RGB_on_click(b):
        with out_plot:
            clear_output()
            
            dataset= Dataset(paths['file_path'], 'r', format='NETCDF4_CLASSIC')            
            arr_R = dataset[bands_desc[R.value]][:]            
            arr_G = dataset[bands_desc[G.value]][:]            
            arr_B = dataset[bands_desc[B.value]][:]
            
            RGB_image = utils_plot.color_composite(arr_R, arr_G, arr_B)
            
            # Plot the image
            plt.figure(figsize=(7,7))
            plt.imshow(RGB_image)

            # Title axis
            plt.xlabel('Longitude')
            plt.ylabel('Latitude')
            plt.tick_params(axis='both', which='both', bottom=False, top=False, right=False, left=False, labelbottom=False, labelleft=False)

            # Show the image
            plt.show()
            
        
    index = widgets.ToggleButtons(options=index_list,
                                  description='index',
                                  value = None,
                                  button_style='',)
    
    index.observe(index_on_change, names='value')
        
    out_plot = widgets.Output()
    
    RGBbox = VBox([R, G, B, RGB_button])
    
    #Create grid to fill it in with widgets
    select_grid = GridspecLayout(2, 2)
    select_grid[0, :], select_grid[1, 0], select_grid[1,1] = b, RGBbox, index
    
    #Create grid to fill it in with widgets
    main_grid = GridspecLayout(2, 1)
    main_grid[0, 0], main_grid[1, 0] = select_grid, out_plot
   
    top_box = HBox([region, date])
    main_box = VBox([top_box, main_grid])

    user_interface.children = [ingestion, status, main_box]
    display(user_interface)

    
def region_on_change(v):
    
    global date, folders
    clear_output()
    
    region_path = os.path.join(path, v['new'])
    paths['region_path'] = region_path
    
    list_folders = os.listdir(region_path)
        
    folders = {}
    for f in list_folders:
        if f.startswith('LC'):
            year = f[9:13]
            day = f[13:16]
            date = datetime.datetime.strptime('{} {}'.format(year, day), '%Y %j')
            date = date.strftime('%d/%m/%Y')
            folders[date] = f
        elif f.startswith('S2'):
            date = datetime.datetime.strptime(f[11:19], '%Y%m%d').strftime('%m/%d/%Y')
            folders[date] = f
    
    list_dates = list(folders.keys())
    date = widgets.Dropdown(options=[list_dates[n] for n in range(len(list_dates))],
                            value = None,
                            description='Dates:',)
    
    date.observe(date_on_change, names='value')
        
    hbox = HBox([region, date])
    user_interface.children = [ingestion, status, hbox]
    display(user_interface)

#####################################################################################

def data_visualization():
    
    global region
    clear_output()
    
    #load the downloaded files
    regions = load_regions()
    regions = list(regions.keys())
    
    #Inicialización de widgets del menu
    #widgets para escoger region
    region = widgets.Dropdown(options=[regions[n] for n in range(len(regions))],
                              value = None,
                              description='Available Regions:',)

    region.observe(region_on_change, names='value')
    vbox = VBox([region]) 
    
    return vbox


wq_sat = data_visualization()
    
#Menu
user_interface = widgets.Tab()
user_interface.children = [ingestion, status, wq_sat]
user_interface.set_title(0,'Data Ingestion')
user_interface.set_title(1,'Job status')
user_interface.set_title(2, 'Wq Satellite')
user_interface
