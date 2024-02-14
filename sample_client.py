import requests

ipv4 = '127.0.0.1'  # local host
port = 8080         # default port


def send_windsaloft_request(region=None, low_altitude=None, high_altitude=None, flight_time=None, flight_date=None):
    """Sends a winds aloft request and prints results"""
    parameters = {}
    if region:
        parameters["region"] = region
    if low_altitude:
        parameters["low_altitude"] = low_altitude
    if high_altitude:
        parameters['high_altitude'] = high_altitude
    if flight_time:
        parameters['flight_time'] = flight_time     # HHMM format
    if flight_date:
        parameters["flight_date"] = flight_date     # formatted as YYYY-MM-DD

    response = requests.get(f'http://{ipv4}:{port}/get_windsaloft', params=parameters)
    if response.status_code == 200:
        # print result chart to console
        # print headers
        for label in response.json()['labels']:
            # pad values to get them to line in stdout
            while len(label) < 6:
                label = label + ' '
            print(f"{label}", end="\t") # new tab instead of newline
        print("")   # print newline
        for row in response.json()['data']:
            if len(row) < len(response.json()['labels']):
                pass
            for value in row:
                # pad values to get them to line in stdout
                while len(value) < 6:
                    value = value + ' '
                print(f"{value}", end="\t")
            print("")

    elif response.status_code == 400:
        print(response.json()['error'])

    else:
        # Unrecognized Response Code
        print(response.status_code)
        raise NotImplementedError


if __name__ == '__main__':
    # Example 1
    send_windsaloft_request()   # default request with no params, returns all regions, all alts, and 6 hour forecast

    # Example 2
    # The below request returns info for the sfo region, between 18,000 - 30,000 feet, using the forecast data that is
    # closest to 2200 utc on Feb 14, 2024. Any combination of arguments can be used, except that flight time and
    # flight date must both be used together or neither must be used.
    send_windsaloft_request(region='sfo',
                            low_altitude='18000',
                            high_altitude='30000',
                            flight_time='2200',         # formatted as HHMM
                            flight_date='2024-02-14'   # formatted as YYYY-MM-DD
                            )

    # Example 3
    send_windsaloft_request(region='sfo',
                            low_altitude='18000',
                            )
