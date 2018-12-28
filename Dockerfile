FROM python:2.7

# Add sample application
ADD application.py /tmp/application.py

# Install any needed packages specified in requirements.txt
# RUN pip install boto3==1.9.71
# RUN pip install botocore==1.12.71

COPY requirements.txt /tmp/
RUN pip install --requirement /tmp/requirements.txt

EXPOSE 8000

# Run it
ENTRYPOINT ["python", "/tmp/application.py"]
