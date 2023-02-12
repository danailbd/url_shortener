FROM python:3.8

# TODO
WORKDIR /app


# Install uvicorn
RUN pip install uvicorn
# RUN pip install psycopg2-binary

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the code
COPY . .

# Run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
