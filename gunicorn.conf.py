# Gunicorn configuration file
bind = "0.0.0.0:5000"
worker_class = "uvicorn.workers.UvicornWorker"
workers = 1
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
timeout = 30
keepalive = 2