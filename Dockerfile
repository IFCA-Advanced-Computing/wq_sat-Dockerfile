# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Base image
# Indigodatacloud/ubuntu-sshd:16.04
FROM indigodatacloud/ubuntu-sshd:16.04
RUN ls

MAINTAINER Daniel Garcia Diaz <garciad@ifca.unican.es>
LABEL version='0.0.1'
# A project to provide data from Sentinel-2 or Landsat 8 satellite

## Install pymysql
RUN  apt-get update && \
  apt-get install -y --reinstall build-essential && \
  apt-get install -y unixodbc-dev  unixodbc-bin && \
  apt-get install -y python-dev && \
  apt-get install -y freetds-dev && \
  apt-get install -y curl python3-setuptools python-pip

RUN pip install --upgrade pip
RUN apt-get install python3-pip

## Install ftp and Faker
RUN  apt-get update && \
  apt-get -y upgrade && \
  apt-get install -y ftp

RUN pip install opencv-python Faker
RUN pip3 install tqdm requests

## Install openstack client for python3
ENV TZ=Europe/Minsk
ENV DEBIAN_FRONTEND=noninteractive 
RUN apt-get update
RUN apt-get install -y libreadline-gplv2-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev

RUN apt-get install -y python python-pip python-tk

## Install tools for datamining
RUN apt-get install -y  libxml2-dev libxslt-dev

RUN apt-get update && apt-get install -y iputils-ping net-tools
RUN apt-get install gcc git build-essential mysql-client python3-setuptools libmysqlclient-dev python3-dev python3-numpy python3-pip libhdf5-serial-dev netcdf-bin libnetcdf-dev wget m4 -y

#RUN wget ftp://ftp.unidata.ucar.edu/pub/netcdf/netcdf-4.4.0.tar.gz && \
#    tar -zxvf netcdf-4.4.0.tar.gz && \
#    rm netcdf-4.4.0.tar.gz
#RUN cd netcdf-4.4.0 && ./configure --disable-netcdf-4 --prefix=/usr/local && make && make install
#RUN apt-get install gcc gfortran g++
#RUN apt-get install libnetcdf-dev libnetcdff-dev
#RUN apt-get install netcdf-bin
#RUN pip install netCDF4
RUN apt-get update -y
RUN apt-get install -y python3-netcdf4

ENV NETCDF_LIBS -I/usr/local/lib
ENV NETCDF_CFLAGS -I/usr/local/include
RUN apt-get install software-properties-common -y
RUN add-apt-repository ppa:ubuntugis/ubuntugis-unstable
RUN apt-get update -y
RUN apt-get install libnetcdf-dev gdal-bin python3-gdal libgdal20 rabbitmq-server -y

RUN ls

RUN exec 3<> /etc/apt/sources.list.d/onedata.list && \
    echo "deb [arch=amd64] http://packages.onedata.org/apt/ubuntu/1902 xenial main" >&3 && \
    echo "deb-src [arch=amd64] http://packages.onedata.org/apt/ubuntu/1902 xenial main" >&3 && \
    exec 3>&-
RUN apt-get update
RUN apt-get install sudo oneclient curl --allow-unauthenticated -y

RUN ls

RUN git clone https://github.com/IFCA/xdc_lfw_sat.git

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

