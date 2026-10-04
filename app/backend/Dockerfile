FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV REVIEWS_CSV=/data/processed/reviews_processed.csv
ENV TOPICS_JSON=/data/topics/topics_by_journey.json

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
