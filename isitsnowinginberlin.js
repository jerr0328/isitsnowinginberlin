var request = require('request');
var restify = require('restify');

var lastUpdateTime = new Date(0);
var isSnowing = false;
var lastWx = 0;

// Berlin city code for weather is 2950159
var weatherApiOptions = {
	url: "http://api.openweathermap.org/data/2.5/weather?id=2950159",
	headers: {"x-api-key": "39a5b0283a8385e239fe8ce89d5a9b76"}
};

function needsUpdating() {
	return (new Date() - lastUpdateTime) > 1000
};

function updateWeather() {
	request(weatherApiOptions, function (error, response, body){
		if(!error && response.statusCode == 200){
			lastWx = JSON.parse(body);
			isSnowing = "Snow" == lastWx.weather[0].main;
			lastUpdateTime = new Date();
			console.log("Got weather " + lastWx.weather[0].main + " at " + lastUpdateTime.toString());
		}
		else {
			console.error(error);
		}
	});
};

function respond(req, res, next) {
	if(needsUpdating()) {
		updateWeather();
	}
	var body = "<html><head><title>Is it snowing in Berlin?</title><body><h1>";
	if(isSnowing)
		body += "Yes"
	else
		body += "No"
	body += "</h1></body></html>"
	res.writeHead(200, {
		'Content-Length': Buffer.byteLength(body),
		'Content-Type': 'text/html'
	});
	res.write(body);
	res.end();
	next();
}

updateWeather();

var server = restify.createServer();
server.get("/", respond);
server.head("/", respond);

server.listen(process.env.PORT || 5000, function() {
  console.log('%s listening at %s', server.name, server.url);
});
