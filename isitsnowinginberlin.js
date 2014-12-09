// Copyright 2014 Jeremy Mayeres
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

var request = require('request');
var restify = require('restify');
var redis = require('redis');
var url = require('url');
var redisURL = url.parse(process.env.REDISCLOUD_URL);
var client = redis.createClient(redisURL.port, redisURL.hostname, {no_ready_check: true});
client.auth(redisURL.auth.split(":")[1]);
// Update delay in seconds (10 minutes)
var updateDelaySeconds = 600;

// Berlin city code for weather is 2950159
var weatherApiOptions = {
  url: "http://api.openweathermap.org/data/2.5/weather?id=2950159",
  headers: {"x-api-key": process.env.OWMAPIKEY}
};

var forecastWeatherApiOptions = {
  url: "http://api.openweathermap.org/data/2.5/forecast/daily?id=2950159&cnt=2",
  headers: {"x-api-key": process.env.OWMAPIKEY}
}

function saveCurrentToRedis(wx) {
  // Set the weather (expires automatically)
  client.set("cached-wx", wx);
  client.expire("cached-wx", updateDelaySeconds);
  // Keep it in non-expiring key (for debugging)
  client.set("last-wx", wx);
}

function saveForecastToRedis(forecast) {
  // Set the weather (expires automatically)
  client.set("cached-forecast", forecast);
  client.expire("cached-forecast", updateDelaySeconds);
  // Keep it in non-expiring key (for debugging)
  client.set("last-forecast", forecast);
}

function getWeather(callback) {
  client.get("cached-wx", function (err, reply) {
    if(reply) {
      wx = JSON.parse(reply);
      callback(wx);
      console.log("Used cache");
    }
    else {
      updateWeather(weatherApiOptions, saveCurrentToRedis, callback);
      console.log("Needed to update cache");
    }
  });
}

function getWeatherNoUpdate(callback) {
  client.get("last-wx", function (err, reply) {
    if(reply) {
      wx = JSON.parse(reply);
      callback(wx);
    }
  });
}

function getForecast(callback) {
  client.get("cached-forecast", function (err, reply) {
    if(reply) {
      forecast = JSON.parse(reply);
      callback(forecast);
      console.log("Used forecast cache");
    }
    else {
      updateWeather(forecastWeatherApiOptions, saveForecastToRedis, callback);
      console.log("Needed to update forecast cache");
    }
  });
}

function getForecastNoUpdate(callback) {
  client.get("last-forecast", function (err, reply) {
    if(reply) {
      forecast = JSON.parse(reply);
      callback(forecast);
    }
  });
}

function updateWeather(options, storeWx, callback) {
  request(options, function (error, response, body){
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

function someMainIsSnow(element, index, array){
  return "Snow" == element.main;
}

function isSnowing(wx) {
  // Check if some element from the weather array has snow
  return wx.weather.some(someMainIsSnow);
}

function willSnow(forecast) {
  // Check if some element from the forecast has snow
  return forecast.list.some(function (element, index, array){
    return element.weather.some(someMainIsSnow);
  });
}

function APIisSnowing(req, res, next) {
  getWeather(function (wx) {
    var snowCheck = isSnowing(wx);
    res.send({isSnowing: snowCheck, dataUpdated: wx.dt});
  });
  next();
}

function APIwillSnow(req, res, next) {
  getForecast(function (forecast) {
    var snowCheck = willSnow(forecast);
    res.send({willSnow: snowCheck, dataUpdated: forecast.list[0].dt});
  });
  next();
}

function APIgetRawWeather(req, res, next) {
  getWeather(function (wx){
    res.send(wx);
  });
  next();
}

function APIgetRawWeatherNoUpdate(req, res, next) {
  getWeatherNoUpdate(function (wx){
    res.send(wx);
  });
  next();
}

function APIgetRawForecast(req, res, next) {
  getForecast(function (forecast){
    res.send(forecast);
  });
  next();
}

function APIgetRawForecastNoUpdate(req, res, next) {
  getForecastNoUpdate(function (forecast){
    res.send(forecast);
  });
  next();
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
server.get("/api/isSnowing", APIisSnowing);
server.head("/api/isSnowing", APIisSnowing);
server.get("/api/willSnow", APIwillSnow);
server.head("/api/willSnow", APIwillSnow);
server.get("/api/rawWeather", APIgetRawWeather);
server.head("/api/rawWeather", APIgetRawWeather);
server.get("/api/noUpdate/rawWeather", APIgetRawWeatherNoUpdate);
server.head("/api/noUpdate/rawWeather", APIgetRawWeatherNoUpdate);
server.get("/api/rawForecast", APIgetRawForecast);
server.head("/api/rawWeather", APIgetRawForecast);
server.get("/api/noUpdate/rawForecast", APIgetRawForecastNoUpdate);
server.head("/api/noUpdate/rawWeather", APIgetRawForecastNoUpdate);
server.get("/tomorrow", restify.serveStatic({
  directory: __dirname,
  default: 'index.html'
}));
server.head("/tomorrow", restify.serveStatic({
  directory: __dirname,
  default: 'index.html'
}));
server.get("/static\/.+", restify.serveStatic({
  directory: '.',
}));
server.head("/static\/.+", restify.serveStatic({
  directory: '.',
}));
server.get("/", restify.serveStatic({
  directory: '.',
  default: 'index.html'
}));
server.head("/", restify.serveStatic({
  directory: '.',
  default: 'index.html'
}));


server.listen(process.env.PORT || 5000, function() {
  console.log('%s listening at %s', server.name, server.url);
});
