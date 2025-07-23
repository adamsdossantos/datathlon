# Builder stage
FROM python:3.10-slim as builder

WORKDIR /app

# Install uv
RUN pip install uv

# Copy all requirements.txt files
COPY api/requirements.txt api/requirements.txt
COPY streamlit_app/requirements.txt streamlit_app/requirements.txt
COPY livekit/requirements.txt livekit/requirements.txt

# Install all dependencies
RUN uv pip install -r api/requirements.txt
RUN uv pip install -r streamlit_app/requirements.txt
RUN uv pip install -r livekit/requirements.txt

# App stage
FROM python:3.10-slim as app

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the rest of the application
COPY . .

# Expose ports
EXPOSE 8000 8501 7880

# Start the applications
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port 8000 & streamlit run streamlit_app/app.py & python livekit/main.py"]