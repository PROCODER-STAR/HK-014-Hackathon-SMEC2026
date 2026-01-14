// My API Key
var apiKey = "fe4feefa8543e06d4f3c66d92c61b69c";

function checkLevel(value, limit1, limit2, limit3, limit4) {
  if (value < limit1) {
    return 1;
  } else if (value < limit2) {
    return 2;
  } else if (value < limit3) {
    return 3;
  } else if (value < limit4) {
    return 4;
  } else {
    return 5;
  }
}

// Get quality name from index
function getQuality(index) {
  if (index == 1) return "Good";
  if (index == 2) return "Fair";
  if (index == 3) return "Moderate";
  if (index == 4) return "Poor";
  if (index == 5) return "Very Poor";
}

function checkAirQuality() {
  var cityInput = document.getElementById("city");
  var cityName = cityInput.value;
  var outputDiv = document.getElementById("output");

  if (cityName == "") {
    outputDiv.innerHTML = "<p>Please enter a city name</p>";
    return;
  }

  outputDiv.innerHTML = "<p>Loading...</p>";

  var geoUrl = "https://api.openweathermap.org/geo/1.0/direct?q=" + cityName + "&limit=1&appid=" + apiKey;
  
  fetch(geoUrl)
    .then(function(response) {
      return response.json();
    })
    .then(function(geoData) {
      // Check if city found
      if (geoData.length == 0) {
        outputDiv.innerHTML = "<p>City not found. Please try another location.</p>";
        return;
      }

      var latitude = geoData[0].lat;
      var longitude = geoData[0].lon;
      var location = geoData[0].name;
      var countryName = geoData[0].country;

      var airUrl = "https://api.openweathermap.org/data/2.5/air_pollution?lat=" + latitude + "&lon=" + longitude + "&appid=" + apiKey;
      
      fetch(airUrl)
        .then(function(response) {
          return response.json();
        })
        .then(function(airData) {
          var pollutants = airData.list[0].components;
          
          var so2Value = pollutants.so2;
          var no2Value = pollutants.no2;
          var pm10Value = pollutants.pm10;
          var pm25Value = pollutants.pm2_5;
          var o3Value = pollutants.o3;
          var coValue = pollutants.co;

          var so2Level = checkLevel(so2Value, 20, 80, 250, 350);
          var no2Level = checkLevel(no2Value, 40, 70, 150, 200);
          var pm10Level = checkLevel(pm10Value, 20, 50, 100, 200);
          var pm25Level = checkLevel(pm25Value, 10, 25, 50, 75);
          var o3Level = checkLevel(o3Value, 60, 100, 140, 180);
          var coLevel = checkLevel(coValue, 4400, 9400, 12400, 15400);

          var worstLevel = so2Level;
          if (no2Level > worstLevel) worstLevel = no2Level;
          if (pm10Level > worstLevel) worstLevel = pm10Level;
          if (pm25Level > worstLevel) worstLevel = pm25Level;
          if (o3Level > worstLevel) worstLevel = o3Level;
          if (coLevel > worstLevel) worstLevel = coLevel;

          var qualityText = getQuality(worstLevel);

          var result = "<hr>";
          result = result + "<h2>Location: " + location + ", " + countryName + "</h2>";
          result = result + "<h3>Air Quality: " + qualityText + " (Index: " + worstLevel + ")</h3>";
          result = result + "<h4>Pollutant Concentrations (µg/m³)</h4>";
          result = result + "<p>SO2 (Sulfur Dioxide): " + so2Value.toFixed(2) + "</p>";
          result = result + "<p>NO2 (Nitrogen Dioxide): " + no2Value.toFixed(2) + "</p>";
          result = result + "<p>PM10 (Particulate Matter): " + pm10Value.toFixed(2) + "</p>";
          result = result + "<p>PM25 (Fine Particles): " + pm25Value.toFixed(2) + "</p>";
          result = result + "<p>O3 (Ozone): " + o3Value.toFixed(2) + "</p>";
          result = result + "<p>CO (Carbon Monoxide): " + coValue.toFixed(2) + "</p>";
          
          outputDiv.innerHTML = result;
        })
        .catch(function(error) {
          outputDiv.innerHTML = "<p>Error getting air quality data. Please try again.</p>";
          console.log(error);
        });
    })
    .catch(function(error) {
      outputDiv.innerHTML = "<p>Error finding city. Please try again.</p>";
      console.log(error);
    });
}

var cityInput = document.getElementById("city");
cityInput.addEventListener("keypress", function(event) {
  if (event.key == "Enter") {
    checkAirQuality();
  }
});