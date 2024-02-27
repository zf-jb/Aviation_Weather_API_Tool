This project contains a microservice python wrapper for the AviationWeather.gov windsaloft forecast service.
The microservice runs as a flask server on the local host. The two required modules for the microservices are
flask and requests. The server takes standard http get requests with five optional parameters.

The parameters are as follows:
1. region (defaults to all, used to filter results)
2. low_altitude (defaults to surface, used to filter results)
3. high_altitude (defaults to highest available altitude, used to filter results)
4. flight_time (requires flight date if used. defaults to the standard 6 hour forecast. Used to select must pertinent forecast information)
5. flight_date (requires flight time if used. defaults to the standard 6 hour forecast. Used to select must pertinent forecast information)

The server returns a 200 code if executed correctly with a json object with the following arguments:
1. labels, contains the headers for the table. label[0] is always the region name, labels[1] + contains the altitudes for the forecast winds
and temperatures.
2. data, contains a list of rows with each row corresponding to each region. the 1st item in each lsit contains the reigon name and the nth item in each row contains the 
forecast corresponding to the nth altitude in the label row.

The server returns a 400 code if an error is encountered. Information about the error is provided a json object with the following parameter:
1. error, contains a brief description of the error encountered by the server program.

An example https request with no arguments on a local server would be:
http://127.0.0.1:8080/get_windsaloft

And an example request with arguments would be:
http://127.0.0.1:8080/get_windsaloft?region=sfo&low_altitude=15000&high_altitude=30000&flight_time=1533&flight_date=2024-02-29

![image](https://github.com/zf-jb/Aviation_Weather_API_Tool/assets/136113091/4ed3c946-d578-43cb-ad0a-8186090d4e92)
