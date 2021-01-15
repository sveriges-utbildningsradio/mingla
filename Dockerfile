# set base image (host OS)
FROM python:3.9 AS builder

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY requirements.txt .
COPY setup.py .
COPY README.md .

# install dependencies
RUN pip install --user -e .

# second unnamed stage
FROM python:3.9-alpine
WORKDIR /code

# copy only the dependencies installation from the 1st stage image
COPY --from=builder /root/.local /root/.local
COPY --from=builder /code .

# copy the content of the local src directory to the working directory
COPY . .

# update PATH environment variable
ENV PATH=/root/.local:$PATH

# command to run on container start
CMD [ "python", "mingla" ]