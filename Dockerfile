FROM ubuntu:20.04

# Install python3 and pip3
RUN apt-get update
RUN apt-get install -y python3
RUN apt-get install -y python3-pip


# install Python modules needed by the Python app
COPY requirements.txt /usr/src/app/
RUN pip3 install --upgrade setuptools

RUN pip3 install --no-cache-dir -r /usr/src/app/requirements.txt
RUN pip3 install google-cloud-storage -q
RUN pip3 install google-cloud -q
RUN pip3 install matplotlib -q
RUN pip3 install numpy -q
RUN pip3 install fpdf -q

# copy files required for the app to run
COPY app.py /usr/src/app/
COPY templates /usr/src/app/templates/
COPY static usr/src/app/static/
# tell the port number the container should expose
EXPOSE 5000

# run the application
RUN pwd
# RUN python3 /usr/src/app/app.py
CMD ["python3", "/usr/src/app/app.py"]
