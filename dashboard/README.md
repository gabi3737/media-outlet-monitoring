# Dashboard

## This dashboard will provide a visual representation of the data collected from various media outlets using streamlit, to analyze media coverage trends effectively.

To install requirements:

```bash
pip install -r requirements.txt
```

To run the dashboard:

```bash
streamlit run app.py
```

To Dockerise the dashboard:

```bash
docker buildx build -t dashboard .
```

To run the dashboard on Docker:

```bash
docker run -p 8501:8501 dashboard
```