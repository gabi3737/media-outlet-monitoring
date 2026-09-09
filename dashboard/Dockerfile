FROM python:latest

EXPOSE 8501

COPY requirements.txt .
COPY dashboard.py .
COPY data.py .

RUN pip install -r requirements.txt

CMD streamlit run dashboard.py