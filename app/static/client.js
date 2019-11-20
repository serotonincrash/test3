var el = x => document.getElementById(x);


function analyze() {
  alert("button pressed!")

  el("analyze-button").innerHTML = "Analyzing...";
  var xhr = new XMLHttpRequest();
  var loc = window.location;
  var enteredText = el("enteredText")
  let formData = new FormData(enteredText.id,enteredText.value)
  xhr.open("POST", `${loc.protocol}//${loc.hostname}:${loc.port}/analyze`,
    true);
  xhr.onerror = function() {
    alert(xhr.responseText);
  };
  xhr.onload = function(e) {
    if (this.readyState === 4) {
		alert("the thing is done")
        alert(e.target.response)
        var response = JSON.parse(e.target.response);
        el("result-label").innerHTML = `Result = ${response["result"]}`;
    }
    el("analyze-button").innerHTML = "Analyze";
  };
  xhr.send(formData)
}
