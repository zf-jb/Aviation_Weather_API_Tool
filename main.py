# A simple wrapper for the aviation weather
from datetime import datetime, timezone
import requests
from flask import Flask, jsonify, request

windsaloft_server = Flask(__name__)
ipv4 = '127.0.0.1'  # local host
port = 8080         # default port


def query_aviation_weather_api(region='all', level='low', fcst='06'):
    """sends a query with the following parameters to the Aviation Weather API"""
    print("sending Query to Aviation Weather")
    parameters = {
        "region": region,
        "level": level,
        "fcst": fcst,
    }
    response = requests.get('https://aviationweather.gov/api/data/windsaloft')
    print(f"Response: {response.json()}")
    return response.json()


def parse_data_string(response_string):
    """Takes a response string, parses it and returns the data in a dictionary """
    # response does not return json format only string, split by line returns
    response_lines = response_string.split('\n')
    headers = response_lines[7].split(' ')      # data starts at line 7
    headers = [i for i in headers if i != '']   # remove excess blank spaces in header line
    data = []
    # for each row create a list of values where the return value corresponds to the index in the header row and
    # append to master list
    for row in response_lines[8:]:
        data.append(row.split(' '))
    return {'headers': headers, 'data': data}


def merge_responses(response1, response2):
    """takes two responses and merges data into response 1"""
    header1 = response1['headers']
    header2 = response2['headers']
    for i in header2:
        if i != 'FT':
            header1.append(i)
    data1 = response1['data']
    data2 = response2['data']
    for forecast_area in range(len(data2)):
        for forecast_alt in range(len(data2[forecast_area])):
            if forecast_alt != 0:
                data1[forecast_area].append(data1[forecast_area][forecast_alt])


@windsaloft_server.route('/get_windsaloft', methods=['GET'])
def return_winds_aloft():
    """Receives winds aloft request and returns data"""
    print(f'Received Request: {request.method} {request.path}?{request.query_string.decode("utf-8")}')
    bad_request = False
    request_error = ""
    region = 'all'
    level = 'low'
    both_level_requests = False
    low_alt = None
    high_alt = None
    flight_time = None
    flight_date = None
    fcst = '06'
    if request.args:
        # All parameters are optional, uses all regions, low altitude, and 06 hour forecast as default
        if request.args['region']:
            region = request.args['region']
        # level argument overrides any request altitudes
        if request.args['level']:
            level = request.args['level']
        if request.args['low_altitude']:
            low_alt = request.args['low_altitude']
        if request.args['high_altitude']:
            high_alt = request.args['high_altitude']
        # Times are formatted as utc 24 hour times (i.e. 1530)
        if request.args['z_time']:                  # formatted as HHMM (0624)
            flight_time = request.args['z_time']
        if request.args['date']:                    # formatted as YYYY-MM-DD (2024-02-12)
            flight_date = request.args['date']
        # if forecast is present it overrides zulu times, expects 06, 12 or 24 hours.
        if request.args['fcst']:
            fcst = request.args['fcst']
    try:
        # calculate appropriate weather forecast for flight time.
        if flight_time and flight_date and not request.args['fcst']:
            flight_datetime = datetime(flight_date[:4], flight_time[5:7], flight_date[8:], flight_time[:2], flight_time[2:], 0)
            current_ztime = datetime.now(timezone.utc)
            timedelta = flight_datetime - current_ztime
            timedelta_hours = (timedelta.days * 24) + (timedelta.seconds / 3600)
            if timedelta_hours < -1:
                bad_request = True
                request_error = 'Flight time is more than one hour old'
            elif timedelta_hours <= 9:
                fcst = '06'
            elif timedelta_hours <= 18:
                fcst = '12'
            elif timedelta_hours > 18:
                fcst = '24'
    except TypeError:
        bad_request = True
        request_error = 'Bad Date or Time Format'
    if low_alt and high_alt:
        if high_alt > 39000 and low_alt < 39000:
            both_level_requests = True
    elif low_alt and not high_alt:
        if low_alt < 39000:
            both_level_requests = True
    elif high_alt and not low_alt:
        if high_alt > 39000:
            both_level_requests = True
    if bad_request:
        return jsonify({'error': request_error}), 400
    else:
        response1 = query_aviation_weather_api(region, level, fcst)
        print(response1)
        response1 = parse_data_string(response1)
        # submit second level request if required
        if both_level_requests:
            response2 = query_aviation_weather_api(region, 'high', fcst)
            print(response2)
            response2 = parse_data_string(response2)
            # Merge Data
            merge_responses(response1, response2)
        # TODO add logic for altitude filtering

        # TODO build and send response
        return jsonify({'Example': "Example Response"})


if __name__ == "__main__":
    # query_aviation_weather_api()
    windsaloft_server.run(host=ipv4, port=port, debug=False)
    print(f"Winds Aloft Server Listening on {ipv4}, port {port}")

