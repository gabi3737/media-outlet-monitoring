FROM public.ecr.aws/lambda/python:latest

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
COPY extract.py .
COPY transform.py .
COPY load.py .

RUN pip install -r requirements.txt

CMD python3 extract.py && python3 transform.py && python3 load.py