/* Getting all document ids*/
var addplayerButton = document.getElementById("addplayer");
var player_form = document.getElementById("player_form");
var player_form_container = document.getElementById("player_form_container");
var playersGlobalDiv = document.getElementsByClassName("players")[0];
var primarySel = document.getElementsByClassName("primary_position")[0];
var secondarySel = document.getElementsByClassName("secondary_position")[0];
var coach_id = sessionStorage.getItem("coach_id");
var image_upload_button = document.getElementById("textfield8");
var document_uplaod_button = document.getElementById("textfield10");
var date_picker = document.getElementById("textfield4");
var gender_selector = document.getElementById("textfield3");
var cancelButton = document.getElementById("cancel-button");
gender_selector.onclick = function () {
  date_picker.value = "";
};

date_picker.onclick = function () {
  if (gender_selector.value == "") {
    alert("Specify player gender before selecting D.O.B");
    return;
  }
  date_picker.min = "2004-01-01";
};

var id_position_map = {};
var position_id_map = {};

var document_type_map = {};

var player_image = "";
var player_document = "";

var local_database = {};
/* got all doc ids*/

/*listeners and function calls*/
window.onload = function () {
  onloadFunctions();
};
addplayerButton.onclick = addplayer;
primarySel.onchange = function () {
  positionchange(this, secondarySel);
};
secondarySel.onclick = function () {
  if (primarySel.value) {
  } else {
    alert("Please Select Primary Position Before selecting Secondary Position");
  }
};

image_upload_button.onchange = getImage;
document_uplaod_button.onchange = getDocument;
cancelButton.onclick = cancel;

// runs when page is loaded
/*end of function calls and listeners*/

/*function definitions*/

async function onloadFunctions() {
  // this function is called when page is loaded
  const spinner = new Spinner();
  spinner.show();
  Promise.all([loadDocumentId(), datelimit(), loadPositions(), loadDatabase()])
    .then(function () {
      loadPlayers();
    })
    .then(() => spinner.hide());
  addErrorBlocks();
}

function loadPlayers() {
  for (var key in local_database) {
    addplayerFromDatabase(local_database[key]);
  }
}

function editPlayer(editButton) {
  //scroll to top
  addplayerButton.textContent = "Update Player";
  $("#cancel-button").show();
  $("html,body").animate(
    {
      scrollTop: $("#player_form").offset().top,
    },
    "slow"
  );

  var number_of_fields = player_form_container.children.length; //number of fields in the form + 1 button (add player)
  for (var i = 1; i < number_of_fields; i++) {
    var textfield = document.getElementById("textfield" + i);
    var player = $(editButton).parent().parent().parent();
    var fieldclass = ".textfield" + i;
    var player_card_text = $(player).find(fieldclass).text();
    if (i == 4) {
      //for dob
      player_card_text = $(player).find(fieldclass).attr("form-data");
    }
    if (i == 5 || i == 6) {
      player_card_text = position_id_map[player_card_text];
    }
    textfield.value = player_card_text;
  }

  var id = $(player).attr("id");
  player_form.setAttribute("player_id", id);
}

async function addplayer() {
  if (!valid()) return;
  var playerdetails = {};
  var number_of_fields = player_form_container.children.length; //number of fields in the form + 1 button (add player)
  for (var i = 1; i < number_of_fields; i++) {
    var textfield = document.getElementById("textfield" + i);
    playerdetails[textfield.name] = textfield.value;
    console.log(textfield.name + " " + textfield.value);
  }

  const spinner = new Spinner();
  spinner.show();
  await $.ajax({
    type: "POST",
    url: "checkage",
    data: {
      csrfmiddlewaretoken: csrftoken,
      coach_id: coach_id,
      dob: playerdetails["D.O.B"],
      gender: playerdetails["Gender"],
    },
    error: function (response) {
      alert(JSON.parse(response.responseText)["message"]);
      spinner.hide();
      return;
    },
  });

  id = player_form.getAttribute("player_id"); //to know if it is update or add and if id is there then update else add
  playerdetails["id"] = id;
  await addSinglePlayer(playerdetails).then(() => {
    spinner.hide();
    cancel();
  });
}

function cancel() {
  $(player_form)[0].reset();
  addplayerButton.textContent = "Add Player";
  player_form.setAttribute("player_id", "newplayer");
  $("#cancel-button").hide();
}

function valid() {
  var number_of_fields = player_form_container.children.length; //number of fields in the form

  var isvalid = true;
  for (var i = 1; i < number_of_fields; i++) {
    var textfield = document.getElementById("textfield" + i);
    var errortext = document.getElementById("errortext" + i);
    errortext.style.display = "none";
    if (textfield.required && empty(textfield.value)) {
      errortext.style.display = "block";
      isvalid = false;
    }
  }
  return isvalid;
}

async function addSinglePlayer(playerdetails) {
  if ($(playersGlobalDiv).find("#" + playerdetails["id"]).length == 0) {
    await postPlayerToDatabse(playerdetails);
  } else {
    var player;
    await updatePlayer({ player_data: playerdetails }).then((_) => {
      player = playerCard({
        fName: playerdetails["First Name"],
        id: playerdetails["id"],
        dob: playerdetails["D.O.B"],
        lName: playerdetails["Last Name"],
        gender: playerdetails["Gender"],
        phone: playerdetails["Phone No."],
        primary_position: id_position_map[playerdetails["Primary Position"]],
        secondary_position:
          id_position_map[playerdetails["Secondary Position"]],
        document_id_selected: playerdetails["Document Type"],
      });
      $("#" + playerdetails["id"]).replaceWith(player);
    });
  }
}

function addplayerFromDatabase(playerdetails) {
  var player = playerCard({
    fName: playerdetails["First Name"],
    id: playerdetails["id"],
    dob: playerdetails["D.O.B"],
    lName: playerdetails["Last Name"],
    gender: playerdetails["Gender"],
    phone: playerdetails["Phone No."],
    primary_position: id_position_map[playerdetails["Primary Position"]],
    secondary_position: id_position_map[playerdetails["Secondary Position"]],
    document_id_selected: playerdetails["Document ID"],
  });
  playersGlobalDiv.appendChild(player);
}

async function deletePlayer(deleteButton) {
  const spinner = new Spinner();
  spinner.show();
  var playerCard = $(deleteButton).parent().parent().parent();
  playerid = playerCard.attr("id");
  var url = "coachplayer?id=" + playerid;
  await fetch(url, {
    method: "DELETE",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken,
      id: playerid,
    },
  }).then((response) => {
    if (response.status == 200) {
      delete local_database[playerid];
      playerCard.remove();
      spinner.hide();
      alert("Player Deleted Successfully");
    } else {
      spinner.hide();
      alert("An error occured");
    }
  });
}

function empty(string) {
  return string == "" || string == null || string == undefined;
}

function errorTextMessageBlock(text, id) {
  var errorTextMessageBlock = document.createElement("span");
  errorTextMessageBlock.className = "mandatory";
  errorTextMessageBlock.id = id;
  errorTextMessageBlock.style.cssText = `display:none;font-style:italic;`;
  errorTextMessageBlock.innerHTML = text;
  return errorTextMessageBlock;
}

function addErrorBlocks() {
  var form_group = document.getElementsByClassName("form-group");
  for (var i = 0; i < form_group.length; i++) {
    form_group[i].appendChild(
      errorTextMessageBlock("This field cant be empty", `errortext${i + 1}`)
    );
  }
}

function deleteAllPlayers() {
  $("#allPlayers").empty();
}

function getImage() {
  const progressBar = new ProgressBar("#image-progress-bar");
  progressBar.show();
  const reader = new FileReader();
  reader.addEventListener("progress", handleEvent);
  reader.addEventListener("loadend", handleEvent);
  reader.onload = function (e) {
    player_image = reader.result.replace("data:", "").replace(/^.+,/, "");
    progressBar.hide();
  };
  reader.readAsDataURL(this.files[0]);

  function handleEvent(e) {
    if (e.lengthComputable) {
      console.log(e.loaded, e.total, "e.loaded/e.total");
      var percent = Math.round((e.loaded / e.total) * 100);
      progressBar.setProgress(percent);
    }
  }
}

function getDocument() {
  const progressBar = new ProgressBar("#doc-progress-bar");
  progressBar.show();
  const reader = new FileReader();
  reader.addEventListener("progress", handleEvent);
  reader.addEventListener("loadend", handleEvent);
  reader.onload = function (e) {
    player_document = reader.result.replace("data:", "").replace(/^.+,/, "");
    progressBar.hide();
  };
  reader.readAsDataURL(this.files[0]);

  function handleEvent(e) {
    if (e.lengthComputable) {
      var percent = Math.round((e.loaded / e.total) * 100);
      progressBar.setProgress(percent);
    }
  }
}

// -----------------ajax calls----------------

async function updatePlayer({ player_data } = {}) {
  const spinner = new Spinner();
  spinner.show();
  var data = JSON.parse(JSON.stringify(player_data));
  data["csrfmiddlewaretoken"] = csrftoken;
  data["player_image"] = player_image;
  data["player_document"] = player_document;
  await fetch("coachplayer", {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrftoken,
    },
    body: JSON.stringify(data),
  })
    .then((response) => {
      spinner.hide();
    })
    .catch((error) => {
      spinner.hide();
      alert("An error occured");
    });

  player_image = "";
  player_document = "";
}

function positionchange(self, doc) {
  doc.length = 1;
  if (self.value) {
    for (var x in id_position_map) {
      var position = id_position_map[x];
      var id = position_id_map[position];
      if (id == self.value) {
      } else {
        doc.options[doc.options.length] = new Option(position, id);
      }
    }
  }
}

async function loadPositions() {
  await $.ajax({
    type: "POST",
    url: "positiondata",
    data: { csrfmiddlewaretoken: csrftoken },

    success: function (result) {
      var positiondata = JSON.parse(result);
      for (var x in positiondata) {
        id_position_map[positiondata[x].id] = positiondata[x].value;
        position_id_map[positiondata[x].value] = positiondata[x].id;
      }

      var positiondata = JSON.parse(result);
      for (var x in positiondata) {
        primarySel.options[primarySel.options.length] = new Option(
          positiondata[x].value,
          positiondata[x].id
        );
        secondarySel.options[secondarySel.options.length] = new Option(
          positiondata[x].value,
          positiondata[x].id
        );
      }
    },
  });
}

async function loadDatabase() {
  local_database = {};
  var url = "coachplayer?coach_id=" + coach_id;
  await $.ajax({
    type: "GET",
    url: url,
    success: function (result) {
      local_database = JSON.parse(JSON.stringify(convertArrayToJSON(result)));
      // loadPlayers();
    },
  });
}

async function loadDocumentId() {
  await $.ajax({
    type: "GET",
    url: "documentid",
    success: function (result) {
      document_type_map = JSON.parse(JSON.stringify(result));
    },
  });
}

async function postPlayerToDatabse(player) {
  var data = JSON.parse(JSON.stringify(player));
  data["csrfmiddlewaretoken"] = csrftoken;
  data["coach_id"] = coach_id;
  data["player_image"] = player_image;
  data["player_document"] = player_document;
  console.log(data);
  await $.ajax({
    type: "POST",
    url: "coachplayer",
    data: data,
    success: function (result) {
      player["id"] = result["id"];
      local_database[result["id"]] = player;
      var player_card = playerCard({
        fName: player["First Name"],
        id: player["id"],
        dob: player["D.O.B"],
        lName: player["Last Name"],
        gender: player["Gender"],
        phone: player["Phone No."],
        primary_position: id_position_map[player["Primary Position"]],
        secondary_position: id_position_map[player["Secondary Position"]],
        document_id_selected: player["Document Type"],
      });
      playersGlobalDiv.appendChild(player_card);
    },
    error: function (result) {
      alert("An error occured");
      console.log(result);
    },
  });
}

function convertArrayToJSON(array) {
  var json = {};
  for (var i = 0; i < array.length; i++) {
    var player_data = {};
    player_data["id"] = array[i]["ikfuniqueid"];
    player_data["First Name"] = array[i]["first_name"];
    player_data["Last Name"] = array[i]["last_name"];
    player_data["D.O.B"] = array[i]["dob"];
    player_data["Phone No."] = array[i]["mobile"];
    player_data["Primary Position"] = array[i]["primary_position"];
    player_data["Secondary Position"] = array[i]["secondary_position"];
    player_data["Gender"] = array[i]["gender"];
    player_data["Document ID"] = array[i]["document_id_selected"];
    json[player_data["id"]] = player_data;
  }
  return json;
}

function proceed_to_payment() {
  $.ajax({
    type: "POST",
    url: "coachorder",
    data: {
      csrfmiddlewaretoken: csrftoken,
      coach_id: coach_id,
    },
    success: function (result) {
      result = JSON.parse(result);
      sessionStorage.setItem("order_id", result["order_id"]);
      alert("Order Placed Successfully");
      window.location.href = "coachpayment";
    },
    error: function (error) {
      alert("error occured");
    },
  });
}

//date limiter

async function datelimit() {
  await $.ajax({
    type: "POST",
    url: "limitdate",
    data: { season: "S02", csrfmiddlewaretoken: csrftoken },
    success: function (result) {
      date_picker.max = result["upperlimit"];
      date_picker.min = result["lowerlimit"];
    },
    error: function (error) {
      alert("API Error");
    },
  });
}

/*end function definitions*/

/* Card Design */

function playerCard({
  fName,
  lName,
  dob,
  phone,
  id,
  primary_position,
  secondary_position,
  gender,
  document_id_selected,
} = {}) {
  var formattedDob = dob.split("-").reverse().join("/");
  var player = document.createElement("div");
  player.className = "player-card";
  player.id = id;
  var player_image_url = "/media/images/" + id + ".png";
  var error_image_url =
    gender == "Female"
      ? "/static/img/player/default_profilepic_female.jpg"
      : "/static/img/player/default_profilepic_male.jpg";
  var player_document_url = "media/documents/" + id + ".png";
  var document_type = document_type_map[document_id_selected];
  var date = +new Date();
  player.innerHTML = `<div class="player-number">${fName} ${lName}</div>
  <div class="player-details">
    <div class="leading">
      <div class="player-name" style="display:none">
        Name :
        <span class="textfield1"
          >${fName}</span><span> </span><span class="textfield2">${lName}</span
        >
      </div>
      <div class="player-gender">
        Gender : <span class="textfield3">${gender}</span>
      </div>
      <div class="player-dob">
        DOB : <span class="textfield4" form-data=${dob}>${formattedDob}</span>
      </div>
      <div class="player-mobile">
      Phone No. : <span class="textfield7">${phone}</span>
    </div>
    </div>
    <div class="trailing">
      <div class="player-primary-position">
        Primary Position : <span class="textfield5">${primary_position}</span>
      </div>
      <div class="player-secondary-position">
        Secondary Position :
        <span class="textfield6">${secondary_position}</span>
      </div>

    </div>
  </div>
  <div class="player-pictures">
    <div class="player-image-container">
      <img
        src=${player_image_url}?lastmod=${date}
        alt=""
        onerror="this.onerror=null;this.src='${error_image_url}';"
      />
      <div class="image-title">Player Image</div>
    </div>
    <div class="player-image-container">
      <img
        src=${player_document_url}?lastmod=${date}
        alt=""
      />
      <div class="image-title" document_id="${document_id_selected}">${document_type}</div>
    </div>
  </div>
  <div class="text-center col-lg-12 col-md-12 col-sm-12 mt-3">
    <div class="form-group mb-0">
      <button class="btn login-btn" onclick="editPlayer(this)">Edit</button>
      <button class="btn login-btn bg-danger" onclick="deletePlayer(this)">
        Delete
      </button>
    </div>
  </div>`;
  player_document = "";
  player_image = "";
  return player;
}

// ---------------------Some USeful Classes-------------------

class Spinner {
  constructor() {
    this.loadingSpinner = $("#loader");
  }

  show() {
    this.loadingSpinner.show();
  }

  hide() {
    this.loadingSpinner.hide();
  }
}

class ProgressBar {
  constructor(id) {
    this.progressBar = $(id);
    this.progressBar.attr("value", 0);
  }

  show() {
    this.progressBar.show();
  }

  hide() {
    this.progressBar.attr("value", 0);
    this.progressBar.hide();
  }

  setProgress(percentage) {
    this.progressBar.attr("value", percentage);
  }
}
