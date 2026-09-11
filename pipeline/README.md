# Pipeline Folder Contents
`requirements.txt` - Contains all required libraries for this folder
`extract.py` - Extracts and scrapes news articles from RSS feeds
`transform.py` - Transforms scraped data into a usable format and analyses the data to find insights.
`load.py` - Loads the scraped data into the Dynamo DB
`test_.py` - Three separate files containing tests for each phase of the ETL pipeline
`Dockerfile` - Dockerfile used to take an Image of the pipeline folder


## This pipeline will handle the extraction, transformation, and loading (ETL) to a DynamoDB database of data collected from various media outlets.

To install requirements:

```bash
pip install -r requirements.txt
```

To run the pipeline:

```bash
python3 load.py
```

## Command line Arguments:

```bash
python3 load.py --help
```

Skip loading to DB:

```bash
python3 load.py --no-db
```

Only run extraction step:

```bash
python3 load.py --extract-only
```

Save data locally:

```bash
python3 load.py --save-local
```

Choose between JSON and CSV format:

```bash
python3 load.py --format
```

## Update ECR Image

To build and push the Docker Image to the ECR:
- Authenticate your Docker client and AWS CLI to your registry. 

Build the Image:

``` bash
docker build --platform linux/amd64 --provenance=false --sbom=false -t c25-gabi-extract-lambda .
```

Tag the Image:

``` bash
docker tag c25-gabi-extract-lambda:latest 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c25-gabi-extract-lambda:latest
```

Push the Image:

``` bash
docker push 129033205317.dkr.ecr.eu-west-2.amazonaws.com/c25-gabi-extract-lambda:latest
```
