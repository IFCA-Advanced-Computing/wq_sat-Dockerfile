# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Base image
# osgeo/gdal:ubuntu-full-latest
# This file is available at the option of the licensee under:
# Public domain
# or licensed under X/MIT (LICENSE.TXT) Copyright 2019 Even Rouault <even.rouault@spatialys.com>
# https://github.com/OSGeo/gdal/blob/master/gdal/docker/ubuntu-small/Dockerfile
FROM osgeo/gdal:ubuntu-full-latest

MAINTAINER Daniel Garcia Diaz <garciad@ifca.unican.es>
LABEL version='0.0.1'
## A project to provide data from Sentinel-2 or Landsat 8 satellite
## A project to perform super-resolution on satellite imagery


## Install
RUN  apt-get update && \
  apt-get install -y --reinstall build-essential && \
    apt-get install -y git && \
    apt-get install -y curl python3-setuptools python3-pip


## Install netCDF4
RUN apt-get update -y
RUN apt-get install -y python3-netcdf4


## Onedata
RUN exec 3<> /etc/apt/sources.list.d/onedata.list && \
    echo "deb [arch=amd64] http://packages.onedata.org/apt/ubuntu/1902 xenial main" >&3 && \
    echo "deb-src [arch=amd64] http://packages.onedata.org/apt/ubuntu/1902 xenial main" >&3 && \
    exec 3>&-
RUN curl http://packages.onedata.org/onedata.gpg.key | apt-key add -
RUN apt-get update && curl http://packages.onedata.org/onedata.gpg.key | apt-key add -
RUN apt-get install oneclient -y

# What user branch to clone (!)
ARG branch=master

RUN ls

## git clone and Install sat package
RUN git clone -b $branch https://github.com/IFCA/xdc_lfw_sat.git

## Create config file
RUN exec 3<> ./xdc_lfw_sat/sat_modules/config.py && \
    echo "#imports apis" >&3 && \
    echo "import os" >&3 && \
    echo "" >&3 && \
    echo "" >&3 && \
    echo "#Sentinel credentials" >&3 && \
    echo "sentinel_pass = {'username':\"lifewatch\", 'password':\"xdc_lfw_data\"}" >&3 && \
    echo "" >&3 && \
    echo "#Landsat credentials" >&3 && \
    echo "landsat_pass = {'username':\"lifewatch\", 'password':\"xdc_lfw_data2018\"}" >&3 && \
    echo "" >&3 && \
    echo "" >&3 && \
    echo "#available regions" >&3 && \
    echo "regions = {'CdP': {\"id\": 210788, \"coordinates\": {\"W\":-2.830, \"S\":41.820, \"E\":-2.690, \"N\":41.910}}, 'Cogotas': {\"id\": 214571, \"coordinates\": {\"W\":-4.728, \"S\":40.657, \"E\":-4.672, \"N\":40.731}}, 'Sanabria': {\"id\": 211645, \"coordinates\": {\"W\":-6.739, \"S\":42.107, \"E\":-6.689, \"N\":42.136}}}"  >&3 && \
    echo "" >&3 && \
    exec 3>&-


## api installation
RUN cd ./xdc_lfw_sat && \
    python3 setup.py install

## Install requests
RUN pip3 install requests
