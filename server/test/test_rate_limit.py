# THis script is created in order to test that our rate limiter is actually working as intended when we are running our own tests.
# So trying to turn it off and turn it on

from conftest import app

def test_rate_limit_blocks_after_500_requests(client):
    # Turn the limit back on only for this test
    app.config["RATE_LIMIT_ENABLED"] = True
    try:
        # 500 requests within 60 seconds are allowed, stated in the send request method in server.py
        for _ in range(500):
            assert client.get("/api/get-watermarking-methods").status_code == 200
        # Request number 501 must be refused with 429 Too Many Requests
        assert client.get("/api/get-watermarking-methods").status_code == 429
    finally:
        # Always turn it off again, even if the test fails, so the other tests are not blocked furhter down
        app.config["RATE_LIMIT_ENABLED"] = False