FROM python:latest

EXPOSE 8501

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY dashboard.py .
COPY data_functions.py .

CMD streamlit run dashboard.py