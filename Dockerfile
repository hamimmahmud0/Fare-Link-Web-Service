# Use a Python base image
FROM python:3.10

# Create a non-root user (Required by Hugging Face)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH
WORKDIR $HOME/app

# Install dependencies
COPY --chown=user . .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install supervisor

# Create a config for Supervisor to manage both processes
RUN echo '[supervisord]\n\
nodaemon=true\n\
\n\
[program:web]\n\
command=python app.py\n\
\n\
[program:worker]\n\
command=python worker.py' > supervisor.conf

# Hugging Face listens on port 7860 by default
EXPOSE 7860

# Start Supervisor (it will launch both your app and your worker)
CMD ["supervisord", "-c", "supervisor.conf"]