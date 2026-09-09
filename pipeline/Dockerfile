FROM public.ecr.aws/lambda/python:latest

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
COPY extract.py .
COPY transform.py .
COPY load.py .

RUN pip install -r requirements.txt

CMD [ "load.lambda_handler" ]
