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


def get_access_token(url):
    if url is None:
        url = 'https://iam.extreme-datacloud.eu/token'
    #TODO manage exceptions
    access_token = os.environ['OAUTH2_AUTHORIZE_TOKEN']
    refresh_token = os.environ['OAUTH2_REFRESH_TOKEN']

    IAM_CLIENT_ID = os.environ['IAM_CLIENT_ID']
    IAM_CLIENT_SECRET = os.environ['IAM_CLIENT_SECRET']

    data = {'refresh_token': refresh_token, 'grant_type': 'refresh_token', 'client_id':IAM_CLIENT_ID, 'client_secret':IAM_CLIENT_SECRET}
    headers = {'Content-Type': 'application/json'}
    url = url+"?grant_type=refresh_token&refresh_token="+refresh_token+'&client_id='+IAM_CLIENT_ID+'&client_secret='+IAM_CLIENT_SECRET

    r = requests.post(url, headers=headers) #GET token
    print("Rquesting access token: %s" % r.status_code) #200 means that the resource exists
    access_token = json.loads(r.content)['access_token']
    return access_token


def launch_orchestrator_sat_job(sat_args):

    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+access_token}
    tosca_file = '.SAT_DATA.yml'

    with open(tosca_file, 'r') as myfile:
        tosca = myfile.read()
    
    sat = json.dumps(sat_args)
    sat = sat.replace(" ", "")
    
    data = {"parameters" : {   
                "cpus" : 1,
                "mem" : "8192 MB",
                "onedata_provider" : "cloud-90-147-75-163.cloud.ba.infn.it",
                "sat_space_name" : "LifeWatch",
                "sat_args" : sat,
                "region" : sat_args['region'],
                "start_date" : sat_args['start_date'],
                "end_date" : sat_args['end_date'],
                "onedata_zone" : "https://onezone.cloud.cnaf.infn.it"
                 },
            "template" : tosca
            }
    print (data)

    url = 'https://xdc-paas.cloud.ba.infn.it/orchestrator/deployments/'
    r = requests.post(url, headers=headers,data=json.dumps(data)) #GET
    print("Status code SAT: %s" % r.status_code) #200 means that the resource exists
    print(r.headers)
    txt = json.loads(r.text)
    print ('txt: {}'.format(txt))
    print (json.dumps(txt, indent=2, sort_keys=True))
#    #print(r.text)
#    #print(r.reason)
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
    
    url = orchestrator_url + 'deployments?createdBy=' + os.environ['JUPYTERHUB_USER'] + '@https://iam.extreme-datacloud.eu/'
    headers = {'Content-Type': 'application/json', 'Authorization': 'Bearer '+access_token}
    r = requests.get(url, headers=headers) #GET
    return json.loads(r.content)['content']


def find_dataset_type(start_date,end_date,typ,onedata_token):
    
    access_token = get_access_token('https://iam.extreme-datacloud.eu/token')
    
    headers = {"X-Auth-Token": onedata_token}
    url = 'https://cloud-90-147-75-163.cloud.ba.infn.it/api/v3/oneprovider/spaces/17d670040b30511bc4848cab56449088'
    r = requests.get(url, headers=headers)
    space_id = json.loads(r.content)['spaceId']
    print('Onedata space ID: %s' % space_id)
    index_name = 'region_type__query'
    onedata_cdmi_api = 'https://cloud-90-147-75-163.cloud.ba.infn.it/cdmi/cdmi_objectid/'
    url = 'https://cloud-90-147-75-163.cloud.ba.infn.it/api/v3/oneprovider/spaces/'+space_id+'/indexes/'+index_name+'/query'
    r = requests.get(url, headers=headers)
    response = json.loads(r.content)
    result = []
    for e in response:
        if typ in e['key']['dataset']:
            print(e['key']['dataset'])
            if check_date(start_date,end_date,e['key']['beginDate'], e['key']['endDate']):
                print({'beginDate': e['key']['beginDate'], 'endDate': e['key']['endDate'], 'file':e['key']['dataset']})
                result.append({'beginDate': e['key']['beginDate'], 'endDate': e['key']['endDate'], 'file':e['key']['dataset']})
    return result

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
    with open('regions.json') as file:
        regions = json.load(file)
    
    if name.value in regions:
        
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

path = '/home/jovyan/datasets/LifeWatch'
        
paths = {'main_path': path}

##################################### Functions for display Monochromatic band #########################################

def plot_on_change(v):

    dataset= Dataset(paths['band_path'], 'r', format='NETCDF4_CLASSIC')
    data = dataset[v['new']][:]
    vmin, vmax, mean, std = np.amin(data), np.amax(data), np.mean(data), np.std(data)
    stats = "STATS; min = {}, Max = {}, mean = {}, std = {}".format(vmin, vmax, mean, std)
    
    plt.figure(figsize=(7,7))
    
    with out_plot:
        
        clear_output()
        
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
        plt.suptitle(stats, x=0.92, y=0.92, fontsize='large')
        
        # Show the image
        plt.show()        

        
def file_on_change(v):
    
    global out_plot
    clear_output()
    
    list_files = os.listdir(paths['file_path'])
    file = widgets.Dropdown(options=[list_files[n] for n in range(len(list_files))],
                            value = v['new'],
                            description='files:',)
    
    file.observe(file_on_change, names='value')
    
    top_box = HBox([date, file])
        
    band_path = os.path.join(paths['file_path'], v['new'])    
    paths['band_path'] = band_path
    
    dataset= Dataset(paths['band_path'], 'r', format='NETCDF4_CLASSIC')
    variables = dataset.variables
    variables = list(variables.keys())
    
    var = []
    for e in variables:
        if e not in ('lat', 'lon', 'spatial_ref'):
            var.append(e)
    
    bands = widgets.ToggleButtons(options=[var[n] for n in range(len(var))],
                                  description='Bands:',
                                  value = None,
                                  button_style='',)
    
    bands.observe(plot_on_change, names='value')
    
    out_plot = widgets.Output()
    
    bottom_box = HBox([bands])
    vbox = VBox([region, top_box, bottom_box, out_plot])
    visualization.children = [vbox, RGB_image, animation]
    user_interface.children = [ingestion, status, visualization]
    display(user_interface)
    

def date_on_change(v):
    
    clear_output()
    
    file_path = os.path.join(paths['region_path'], folders[v['new']])
    paths['file_path'] = file_path
    
    list_files = os.listdir(paths['file_path'])
    file = widgets.Dropdown(options=[list_files[n] for n in range(len(list_files))],
                            value = None,
                            description='files:',)
    
    file.observe(file_on_change, names='value')
    
    top_box = HBox([date, file])

    vbox = VBox([region, top_box])
    visualization.children = [vbox, RGB_image, animation]
    user_interface.children = [ingestion, status, visualization]
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
    
#    with output_band:
    
    hbox = HBox([region, date])
    visualization.children = [hbox, RGB_image, animation]
    user_interface.children = [ingestion, status, visualization]
    display(user_interface)
    
#    with output_RGB:
#        
#        hbox = HBox([region, date])
#        visualization.children = [Band, hbox, animation]
#        user_interface.children = [ingestion, status, visualization]
#        display(user_interface)
    
#################################################################################
    
def Monochromatic_band(reg):
    
    global region
        
    #Drop down to choose the available region
    region = widgets.Dropdown(options=[reg[n] for n in range(len(reg))],
                              value = None,
                              description='Available Regions:',)

    region.observe(region_on_change, names='value')
    vbox = VBox([region]) 
    
    return vbox


def RGB(reg):
    
    global region
        
    #Inicialización de widgets del menu
    #widgets para escoger region
    region = widgets.Dropdown(options=[reg[n] for n in range(len(reg))],
                              value = None,
                              description='Available Regions:',)
    
    region.observe(region_on_change, names='value')
    vbox = VBox([region]) 
    
    return vbox


def clip(reg):
            
    #Inicialización de widgets del menu
    #widgets para escoger region
    region = widgets.Dropdown(options=[reg[n] for n in range(len(reg))],
                              value = None,
                              description='Available Regions:',)

    vbox = VBox([region]) 
    
    return vbox

#####################################################################################

def data_visualization():
    
    global visualization, Band, RGB_image, animation
    clear_output()
    
    reg = os.listdir(paths['main_path'])
    
    Band = Monochromatic_band(reg)
    RGB_image = RGB(reg)
    animation = clip(reg)
    
    #Menu
    visualization = widgets.Tab()
    visualization.children = [Band, RGB_image, animation]
    visualization.set_title(0, 'Monochromatic Band')
    visualization.set_title(1, 'RGB image')
    visualization.set_title(2, 'Animations')
    
    return visualization


visualization = data_visualization()
    
#Menu
user_interface = widgets.Tab()
user_interface.children = [ingestion, status, visualization]
user_interface.set_title(0,'Data Ingestion')
user_interface.set_title(1,'Job status')
user_interface.set_title(2, 'Data Visualization')
user_interface
