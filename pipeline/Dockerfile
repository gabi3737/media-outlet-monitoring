FROM public.ecr.aws/lambda/python:latest

WORKDIR ${LAMBDA_TASK_ROOT}


COPY requirements.txt .
RUN pip install -r requirements.txt
RUN python -m spacy download en_core_web_md --target tmp/models

COPY extract.py .
COPY transform.py .
COPY load.py .

CMD [ "load.lambda_handler" ]
