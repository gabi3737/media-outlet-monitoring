FROM public.ecr.aws/lambda/python:latest

WORKDIR ${LAMBDA_TASK_ROOT}

RUN python -m spacy download en_core_web_md --target-dir ${LAMBDA_TASK_ROOT}/models

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY extract.py .
COPY transform.py .
COPY load.py .

CMD [ "load.lambda_handler" ]
