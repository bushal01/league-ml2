"""Module to support functions that pull data from Riot servers."""
import os
import requests
import time


MATCH_HISTORY_URL = 'api.riotgames.com/lol/match/v4/matchlists/by-account/'  # store this in env variable later
API_REQUEST_FUNCTIONS = {
    'match_history': pull_match_history,
    'match': pull_match
}

def pull_match_history(player_id, region):
    logger.info('Pulling match history for player ' + str(player_id))
    url = ('https://' + region + '.' + os.getenv('MATCH_HISTORY_URL') + str(player_id)
           + '?api_key=' + os.getenv('API_KEY'))
    return requests.get(url).json()


def pull_match(match_id, region):
    logger.info(f'Pulling match {str(match_id)}')
    url = ('https://' + region + '.' + os.getenv('MATCH_URL') + str(match_id)
               + '?api_key=' + os.getenv('API_KEY'))
    return requests.get(url).json()


def api_request(request_type, id, request_log, region='na1', request_error_log=[]):
    # Wait to make next request until under the rate limit
    time.sleep(rate_limit(request_log))
    request_log.append((id, time.time()))

    # Make request
    r = API_REQUEST_FUNCTIONS[request_type](id, region)

    # Validate request. If valid, return request. If invalid, handle error appropriately.  If max errors exceeded,
    # exit gracefully.
    if validate_request(r):
        return r, request_log
    else:
        return handle_invalid_request(r, request_type, id, request_log, region, request_error_log)


def validate_request(r):
    s = r['status']['status_code']
    if s in os.getenv('VALID_REQUEST_CODES'):  # valid request
        return True
    else:
        return False


def handle_invalid_request(r, request_type, id, request_log, region, request_error_log):
    if len(request_error_log) >= (os.getenv('MAX_ERRORS') - 1):
        logger.info('Max request errors reached.  Exiting')
        return 'EXIT'
    if r['status'] == '429':
        request_error_log.append('429', time.time())
        time.sleep(10)
        return api_request(request_type, id, request_log, region, request_error_log)
    else:
        time.sleep(10)
        return api_request(request_type, id, request_log, region, request_error_log)


def rate_limit(request_log):
    """Return the number of seconds to wait until a request can be made under the rate limit.  request_log is
    assumed to be a list of tuples (id, time_of_request)."""
    return 0
