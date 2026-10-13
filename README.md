# tatou
A web platform for pdf watermarking. This project is intended for pedagogical use, and contain security vulnerabilities. Do not deploy on an open network.

## Instructions

The following instructions are meant for a bash terminal on a Linux machine. If you are using something else, you will need to adapt them.

To clone the repo, you can simply run:

```bash
git clone https://github.com/nharrand/tatou-2026.git
```

Note that you should probably fork the repo and clone your own repo.


### Set up

```bash
cd tatou/server

# Create a python virtual environement
python3 -m venv .venv

# Activate your virtual environement
. .venv/bin/activate

# Install the necessary dependencies
python -m pip install -e ".[dev]"
```

### Run the unit tests

Tests for the watermarking methods.

```bash
python -m pytest test/test_watermarking_*.py test/test_fuzz_*watermarking*.py
```

### Run the API tests

Requests against the API routes, using Flask's test client and an in-memory SQLite database.

```bash
python -m pytest test/test_api.py test/test_auth_required.py test/test_*_idor.py test/test_*_logging.py test/test_rate_limit.py test/test_fuzz_api.py
```

To run all tests: `python -m pytest`

### Run coverage analysis

```bash
python -m pytest --cov=src --cov-report=term-missing
```

### Deploy

The RMAP keys are kept outside the repository, in `../tatou-rmap/soft-sec-keys` (the server's private key `group21-private.asc` and the groups' public keys in `clients/`).

From the root of the directory:

```bash
# Create a file to set environement variables like passwords.
cp sample.env .env

# Edit .env and pick the passwords you want, and set RMAP_DOCUMENT_ID,
# RMAP_WATERMARK_METHOD, RMAP_WATERMARK_KEY and RMAP_PRIVATE_KEY_PASSPHRASE

# Rebuild the docker image and deploy the containers
docker compose up --build -d

# Monitor logs in realtime 
docker compose logs -f

# Test if the API is up
http -v :5000/healthz

# Open your browser at 127.0.0.1:5000 to check if the website is up.
```
