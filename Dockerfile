check all errors and bugs an run frontend plus backent withh neogotiotion handling # Use official Python image
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["python", "app.py"] 