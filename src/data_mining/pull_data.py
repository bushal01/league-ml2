"""Module to support functions that pull data from Riot servers."""
import os
import sys
import functools

import requests
import time
import logging
import json
from collections import deque

import dotenv
import pandas as pd

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stdout,
)


def api_request(request_function):
    """Decorator to wrap around API calls to faciliate logging, rate limits, and error handling."""

    @functools.wraps(request_function)
    def wrapper_api_request(*args, **kwargs):
        # Add request to log and wait if necessary
        args[0].request_log.add_request_after_wait(
            {
                "request_function": request_function.__name__,
                "request_kwargs": str(args[1:]) + str(kwargs),
                "time": time.time(),
                "datetime": str(pd.Timestamp.now()),
            }
        )
        r = request_function(*args, **kwargs)
        # Validate request. If valid, return request. If invalid, handle error appropriately.
        # If max errors exceeded, exit (gracefully?).
        if args[0].validate_request(r):
            return r.json()
        else:
            return args[0].handle_invalid_request(r, request_function, *args, **kwargs)

    return wrapper_api_request


class Requester:
    """Class to handle api requests."""

    RESPONSE_ERROR_CODES = {
        "400": "Bad request",
        "401": "Unauthorized",
        "403": "Forbidden",
        "404": "Data not found",
        "405": "Method not allowed",
        "415": "Unsupported media type",
        "429": "Rate limit exceeded",
        "500": "Internal server error",
        "502": "Bad gateway",
        "503": "Service unavailable",
        "504": "Gateway timeout",
    }

    RESPONSE_VALID_CODES = {200: "OK"}

    def __init__(
        self,
        api_key=None,
        rate_limits=[{"requests": 20, "seconds": 1}, {"requests": 100, "seconds": 120}],
        max_errors=100,
    ):
        dotenv.load_dotenv()
        self.api_key = os.getenv("API_KEY") if api_key is None else api_key
        # Store a queue of the most recent requests for rate limiting and debugging
        self.request_log = RequestLog(rate_limits)  # custom RequestLog object here
        self.request_error_log = []
        self.max_errors = max_errors

    @api_request
    def pull_match_history(self, puuid, region="americas", start=0, count=100):
        """Pull a match history based off player puuid.  Pulls the latest `count` matches where `count` <= 100.
        To pull more matches, set start to appropriate index (eg. start=5 will skip the first 5 matches).
        Note: region is new format (`americas`, `europe`, or `asia`)"""
        logging.info(f"Pulling match history for player {puuid}")
        match_history_url = "api.riotgames.com/lol/match/v5/matches/by-puuid/"
        url = f"https://{region}.{match_history_url}{puuid}/ids?start={start}&count={count}&api_key={self.api_key}"
        return requests.get(url)

    @api_request
    def pull_match(self, match_id, region="americas"):
        logging.info(f"Pulling match {str(match_id)}")
        match_url = "api.riotgames.com/lol/match/v5/matches/"
        url = f"https://{region}.{match_url}{match_id}?api_key={self.api_key}"
        return requests.get(url)

    @api_request
    def pull_summoner_by_name(self, summoner_name, region="na1"):
        """Given a summoner name, pulls the `id`, `accountId`, and `puuid`.  `puuid` is used for match history"""
        logging.info(f"Pulling summoner {summoner_name}")
        summoner_name_url = "api.riotgames.com/lol/summoner/v4/summoners/by-name/"
        url = f"https://{region}.{summoner_name_url}{summoner_name}?api_key={self.api_key}"
        return requests.get(url)

    @api_request
    def pull_players_in_division(
        self, queue="RANKED_SOLO_5x5", tier="GOLD", division="I", page=1, region="na1"
    ):
        """Pull all players in a given division.

        queue: RANKED_SOLO_5x5 or RANKED_FLEX_SR
        tier: name of tier in all caps
        division: I, II, III, IV
        page: lists come in pages, 205 summoners per page. a valid page is <= 1,000,001, but max is usually smaller
        region: old style region (na1, euw1, etc...)"""
        logging.info(f"Pulling players in {queue}, {tier} {division}, page {page}")
        league_url = "api.riotgames.com/lol/league-exp/v4/entries/"
        url = f"https://{region}.{league_url}{queue}/{tier}/{division}?page={page}&api_key={self.api_key}"
        return requests.get(url)

    def validate_request(self, r):
        if r.status_code in self.RESPONSE_VALID_CODES:  # valid request
            return True
        else:
            return False

    def handle_invalid_request(
        self, r, request_function, *args, retry_timer=2, **kwargs
    ):
        self.request_error_log.append(
            {
                "request_function": request_function.__name__,
                "request_kwargs": str(args) + str(kwargs),
                "status": r.status_code,
                "datetime": str(pd.Timestamp.now()),
            }
        )
        if len(self.request_error_log) >= self.max_errors:
            logging.error("Max request errors reached.  Exiting")
            self.write_error_log()
            sys.exit()
        else:
            logging.info(f"Request failed. Retrying request in {retry_timer} seconds")
            time.sleep(retry_timer)
            return request_function(*args, **kwargs)

    def write_error_log(self):
        pd.DataFrame.from_records(self.request_error_log).to_csv(
            f"logs/request_error_log_{str(pd.Timestamp.now())}.log"
        )


class RequestLog:
    def __init__(self, rate_limits):
        """Initialize a RequestLog object which is a list of deques that manage rate limiting for api requests.

        rate_limits is a list of dicts with keys `requests` and `seconds` symbolizing the number of requests that
        can be made of a period of seconds.

        The deques are expected to store requests which are dicts containing a time key which stores an int containing
        number of seconds since the epoch.
        """
        self.request_logs = []
        for rate_limit in rate_limits:
            self.request_logs.append(
                {
                    "request_queue": deque(maxlen=rate_limit["requests"]),
                    "num_seconds": rate_limit["seconds"],
                }
            )

    def num_seconds_to_wait(self):
        secs_to_wait = 0
        for request_log in self.request_logs:
            if len(request_log["request_queue"]) == request_log["request_queue"].maxlen:
                # compare current time to time of the first element in the queue
                # that time difference needs to be > request_log['num_seconds']
                # else, we need to wait request_log['num_seconds'] - that difference
                secs_since = time.time() - request_log["request_queue"][0]["time"]
                secs_to_wait = max(
                    secs_to_wait, request_log["num_seconds"] - secs_since
                )
        return secs_to_wait

    def add_request(self, request_log_entry):
        for request_log in self.request_logs:
            request_log["request_queue"].append(request_log_entry)

    def add_request_after_wait(self, request_log_entry):
        time_to_wait = self.num_seconds_to_wait()
        if time_to_wait > 0:
            logging.debug(f"Waiting {time_to_wait} seconds before making request")
            time.sleep(time_to_wait)
        logging.debug(f"Adding {request_log_entry} to request log")
        self.add_request(request_log_entry)

    def __str__(self):
        output_str = ""
        for request_log in self.request_logs:
            output_str += f"\n{request_log['request_queue'].maxlen} requests : {request_log['num_seconds']} seconds\n"
            output_str += "\n".join([str(x) for x in request_log["request_queue"]])
        return output_str


def test_request_log_class():
    print("========= Testing Request Log Class =========")
    tr = RequestLog([{"requests": 2, "seconds": 5}])
    tr.add_request_after_wait({"time": time.time(), "request": "dummy1"})
    tr.add_request_after_wait({"time": time.time(), "request": "dummy2"})
    tr.add_request_after_wait({"time": time.time(), "request": "dummy3"})
    print(tr)


def test_api_calls():
    print("========= Testing API Calls =========")
    req = Requester()
    # Test pulling all players in a division
    players = req.pull_players_in_division(
        tier="GOLD", division="I", page=1, region="na1"
    )
    print(len(players))
    print(json.dumps(players[0], sort_keys=True, indent=2))
    # Test pulling a summoner by name
    sn = req.pull_summoner_by_name(players[0]["summonerName"], "na1")
    print(sn)
    # Test pulling a match history
    mh = req.pull_match_history(sn["puuid"], "americas")
    print(mh)
    # Test pulling a match
    match = req.pull_match(mh[0])
    print(json.dumps(match))
    print("========== Request Log ===========")
    print(req.request_log)
    print("========== Request Error Log ===========")
    print(req.request_error_log)


def main():
    """Basic test for module"""
    test_api_calls()
    test_request_log_class()


if __name__ == "__main__":
    main()
