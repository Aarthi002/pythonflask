FROM alpine:3.5

# Install python3 and pip3
RUN apk update
RUN apk add python3
RUN apk add py3-pip

# install Python modules needed by the Python app
COPY requirements.txt /usr/src/app/
RUN pip3 install --no-cache-dir -r /usr/src/app/requirements.txt

# copy files required for the app to run
COPY app.py /usr/src/app/
COPY templates /usr/src/app/templates/
COPY static usr/src/app/static/
# tell the port number the container should expose
EXPOSE 5000

# run the application
CMD ["python3", "/usr/src/app/app.py"]