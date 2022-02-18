"""Module to support functions that pull data from Riot servers."""
import os
import requests
import time
import logging


class MatchCrawler:
    """Class to handle match crawling.
    Class variables: api_key, match_history_url, match_url, request_log, and request_error_log.
    Class methods: pull_match_history, pull_match, api_request, validate_request, handle_invalid_request, rate_limit
        Contains methods to pull matches, match history"""
    def __init__(self, api_key=None, match_history_url=None, match_url=None, request_log=[], request_error_log=[]):
        self.api_key = os.getenv('API_KEY') if api_key is None else api_key
        self.request_log = request_log
        self.request_error_log = request_error_log
        self.match_history_url = os.getenv('MATCH_HISTORY_URL') if match_history_url is None else match_history_url
        self.match_url = os.getenv('MATCH_URL') if match_url is None else match_url
        self.API_REQUEST_FUNCTIONS = {
            'match_history': self.pull_match_history,
            'match': self.pull_match
        }

    def pull_match_history(self, player_id, region):
        logging.info(f'Pulling match history for player {player_id}')
        url = f'https://{region}.{self.match_history_url}{player_id}?api_key={self.api_key}'
        return requests.get(url).json()

    def pull_match(self, match_id, region):
        logging.info(f'Pulling match {str(match_id)}')
        url = f'https://{region}.{self.match_url}{match_id}?api_key={self.api_key}'
        return requests.get(url).json()

    def api_request(self, request_type, rid, request_log, region='na1', request_error_log=[]):
        # Wait to make next request until under the rate limit
        time.sleep(self.rate_limit(request_log))
        request_log.append((rid, time.time()))

        # Make request
        r = self.API_REQUEST_FUNCTIONS[request_type](rid, region)

        # Validate request. If valid, return request. If invalid, handle error appropriately.  If max errors exceeded,
        # exit gracefully.
        if self.validate_request(r):
            return r, request_log
        else:
            return self.handle_invalid_request(r, request_type, rid, request_log, region, request_error_log)

    def validate_request(self, r):
        s = r['status']['status_code']
        if s in os.getenv('VALID_REQUEST_CODES'):  # valid request
            return True
        else:
            return False

    def handle_invalid_request(self, r, request_type, rid, request_log, region, request_error_log):
        if len(request_error_log) >= (os.getenv('MAX_ERRORS') - 1):
            logging.info('Max request errors reached.  Exiting')
            return 'EXIT'
        if r['status'] == '429':
            request_error_log.append('429', time.time())
            time.sleep(10)
            return self.api_request(request_type, rid, request_log, region, request_error_log)
        else:
            time.sleep(10)
            return self.api_request(request_type, rid, request_log, region, request_error_log)

    def rate_limit(self, request_log):
        """Return the number of seconds to wait until a request can be made under the rate limit.  request_log is
        assumed to be a list of tuples (rid, time_of_request)."""
        return 0
