var request = require('request');
var restify = require('restify');
var redis = require('redis');
var url = require('url');
var redisURL = url.parse(process.env.REDISCLOUD_URL);
var client = redis.createClient(redisURL.port, redisURL.hostname, {no_ready_check: true});
client.auth(redisURL.auth.split(":")[1]);
// Update delay in seconds
var updateDelaySeconds = 60;

// Berlin city code for weather is 2950159
var weatherApiOptions = {
  url: "http://api.openweathermap.org/data/2.5/weather?id=2950159",
  headers: {"x-api-key": process.env.OWMAPIKEY}
};

function saveToRedis(wx) {
  // Set the weather (expires automatically)
  client.set("cached-wx", wx);
  client.expire("cached-wx", updateDelaySeconds);
  // Keep it in non-expiring key (for debugging)
  client.set("last-wx", wx);
}

function getWeather(callback) {
  client.get("cached-wx", function (err, reply) {
    if(reply) {
      wx = JSON.parse(reply);
      callback(wx);
      console.log("Used cache");
    }
    else {
      updateWeather(saveToRedis, callback);
      console.log("Needed to update cache");
    }
  });
}

function updateWeather(storeWx, callback) {
  request(weatherApiOptions, function (error, response, body){
    if(!error && response.statusCode == 200){
      wx = JSON.parse(body);
      storeWx(body);
      callback(wx);
    }
    else {
      console.error(error);
    }
  });
};

function isSnowing(wx) {
  return wx.weather.reduce(function(previousValue, currentValue, index, array){
    // If the previousValue is true, no need to check, keep passing true
    if(previousValue) return previousValue;
    // Check if the current value shows snow
    return "Snow" == currentValue.main;
  }, false);
}

function APIisSnowing(req, res, next) {
  getWeather(function (wx) {
    if(isSnowing(wx))
      res.send({isSnowing: true});
    else
      res.send({isSnowing: false});
  });
}

function APIgetRawWeather(req, res, next) {
  getWeather(function (wx){
    res.send(wx);
  });
}

function respond(req, res, next) {
  getWeather(function (wx) {
    var body = "<html><head><title>Is it snowing in Berlin?</title><body><h1 style=\"text-align: center\">";
    if(isSnowing(wx))
      body += "Yes"
    else
      body += "No"
    body += "</h1><p>Data last updated: " + new Date(wx.dt * 1000).toString() + "</p></body></html>"
    res.writeHead(200, {
      'Content-Length': Buffer.byteLength(body),
      'Content-Type': 'text/html'
    });
    res.write(body);
    res.end();
  })

  next();
}
console.log("Getting initial value: ");
getWeather(console.log);

var server = restify.createServer();
server.get("/", respond);
server.head("/", respond);
server.get("/api/isSnowing", APIisSnowing);
server.head("/api/isSnowing", APIisSnowing);
server.get("/api/rawWeather", APIgetRawWeather);
server.head("/api/rawWeather", APIgetRawWeather);

server.listen(process.env.PORT || 5000, function() {
  console.log('%s listening at %s', server.name, server.url);
});
