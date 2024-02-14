# A simple wrapper for the aviation weather
from datetime import datetime, timezone
import requests
from flask import Flask, jsonify, request
from Errors import BadAPICall, BadAPIParams

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
    response = requests.get('https://aviationweather.gov/api/data/windtemp', params=parameters)
    # print(f"Response: {response.text}")
    if response.status_code == 200:
        if response.text == 'No Data Available':
            raise BadAPIParams
        return response.text
    else:
        print(response.status_code)
        raise BadAPICall


def parse_data_string(response_string):
    """Takes a response string, parses it and returns the data in a dictionary """
    # response does not return json format only string, split by line returns
    response_lines = response_string.split('\n')
    # find header_line
    headers = 0
    for line in response_lines:
        if line[:2] == 'FT':
            break
        headers += 1
    labels = response_lines[headers].split(' ')      # data start
    labels = [i for i in labels if i != '']   # remove excess blank spaces in header line
    data = []
    # for each row create a list of values where the return value corresponds to the index in the header row and
    # append to master list
    for row in response_lines[headers + 1:]:
        new_row = [i for i in row.split(' ') if i != '']    # remove blanks and transform into list
        while len(new_row) < len(labels):
            new_row.insert(1, '')   # insert blank space to account for forecast levels too low to ground
        data.append(new_row)
    return {'labels': labels, 'data': data}


def merge_responses(response1, response2):
    """takes two responses and merges data into response 1"""
    # merge header labels
    header1 = response1['labels']
    header2 = response2['labels']
    for i in header2:
        if i != 'FT':
            header1.append(i)
    data1 = response1['data']
    station_dict1 = {}           # create a dictionary to keep track of forecast stations
    for i in range(len(data1)):
        station_dict1[response1['data'][i][0]] = i
    data2 = response2['data']
    # append 45000 and 53000 to low level station forecast if available
    for forecast_area in range(len(data2)):
        station = data2[forecast_area][0]
        if station in station_dict1:
            station_index = station_dict1[station]
            for forecast_alt in range(len(data2[forecast_area])):
                if forecast_alt != 0:
                    data1[station_index].append(data2[forecast_area][forecast_alt])
    # append empty values to low level stations without high level forecast
    for row in data1:
        while len(row) < len(header1):
            row.append('')


@windsaloft_server.route('/get_windsaloft', methods=['GET'])
def return_winds_aloft():
    """Receives winds aloft request and returns data"""
    try:
        print(f'Received Request: {request.method} {request.path}?{request.query_string.decode("utf-8")}')
        bad_request = False
        request_error = ""
        region = 'all'
        low_alt = None
        high_alt = None
        flight_time = None
        flight_date = None
        fcst = '06'
        if request.args:
            # All parameters are optional, uses all regions, low altitude, and 06 hour forecast as default
            if 'region' in request.args:
                region = request.args['region']
            if 'low_altitude' in request.args:
                low_alt = int(request.args['low_altitude'])
            if 'high_altitude' in request.args:
                high_alt = int(request.args['high_altitude'])
            # Times are formatted as utc 24 hour times (i.e. 1530)
            if 'flight_time' in request.args:                  # formatted as HHMM (0624)
                flight_time = request.args['flight_time']
            if 'flight_date' in request.args:                     # formatted as YYYY-MM-DD (2024-02-12)
                flight_date = request.args['flight_date']
        # catch flight time / flight date miss matches
        if (flight_time and not flight_date) or (not flight_time and flight_date):
            return jsonify({'error': "Missing Flight Time or Date"}), 400
        try:
            # calculate appropriate weather forecast for flight time.
            if flight_time and flight_date:
                # calculate time delta
                flight_datetime = datetime(int(flight_date[:4]), int(flight_date[5:7]), int(flight_date[8:]), int(flight_time[:2]),
                                           int(flight_time[2:]), 0)
                flight_datetime = flight_datetime.replace(tzinfo=timezone.utc)
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

        if bad_request:
            print(f'Returning Error: {request_error}')
            return jsonify({'error': request_error}), 400

        else:
            print('Query Aviation Weather API...')
            response1 = query_aviation_weather_api(region, 'low', fcst)
            # print(response1)
            response1 = parse_data_string(response1)
            # submit high level
            response2 = query_aviation_weather_api(region, 'high', fcst)
            # print(response2)
            response2 = parse_data_string(response2)
            # Merge Data between high and low altitudes
            print('Formatting Data')
            merge_responses(response1, response2)
            # print(response1)
            # remove altitudes outside of user requested altitude ranges
            filter_columns = []
            for i in range(len(response1['labels'])):
                if i == 0:
                    continue
                if low_alt:
                    if int(response1['labels'][i]) < low_alt:
                        filter_columns.append(i)
                if high_alt:
                    if int(response1['labels'][i]) > high_alt:
                        filter_columns.append(i)
            filter_columns.sort(reverse=True)
            for col_num in filter_columns:
                del response1['labels'][col_num]
                for lst in response1['data']:
                    del lst[col_num]
            # check that all data was not deleted
            if len(response1['labels']) <= 1:
                print('Requested Altitude Range Contains no altitudes')
                return jsonify({'error': 'No altitudes in given altitude range, widen range and try again'}), 400
            # send response
            print('Sending Response')
            return jsonify(response1)
    except Exception as e:
        return jsonify({'error': f"Unexpected Error: {e}"}), 400


if __name__ == "__main__":
    # print(query_aviation_weather_api())  # test aviation weather call
    print(f"Winds Aloft Server Listening on {ipv4}, port {port}")
    windsaloft_server.run(host=ipv4, port=port, debug=False)


