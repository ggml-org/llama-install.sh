import sys
import time
from huggingface_hub import HfApi, set_client_factory, utils
from huggingface_hub.utils import httpx


class RetryTransport(httpx.BaseTransport):
    def __init__(self, transport, max_retries=5):
        self._transport = transport
        self._max_retries = max_retries

    def handle_request(self, request):
        for attempt in range(self._max_retries + 1):
            try:
                response = self._transport.handle_request(request)
                if response.status_code != 429 and response.status_code < 500:
                    return response
                if attempt == self._max_retries:
                    return response
                response.close()
            except httpx.TransportError:
                if attempt == self._max_retries:
                    raise
            time.sleep(min(2**attempt, 30))

    def close(self):
        self._transport.close()


utils.disable_progress_bars()

set_client_factory(lambda: httpx.Client(
    transport=RetryTransport(httpx.HTTPTransport()),
    follow_redirects=True,
    timeout=httpx.Timeout(timeout=30.0),
))

api = HfApi()

if len(sys.argv) == 2:
    api.sync_bucket("output", f"hf://buckets/{sys.argv[1]}")
