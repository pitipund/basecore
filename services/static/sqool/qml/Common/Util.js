function getAge (birthdate) {
    var today = new Date();

    let [bday, bmonth, byear] = birthdate.split("/");
    byear = (byear - 543 >= 0)? (byear - 543) : byear;
    var age = diffDate(today, new Date([byear, bmonth, bday].join("-")));

    return age["years"] + " ปี " + age["months"] + " เดือน " + age["days"] + " วัน";
}

function diffDate (date1, date2) {
    var m = moment(date1);
    var years = m.diff(date2, 'years');
    m.add(-years, 'years');
    var months = m.diff(date2, 'months');
    m.add(-months, 'months');
    var days = m.diff(date2, 'days');

    return {years: years, months: months, days: days};
}

function setCookie (cname, cvalue, exdays) {
    var d = new Date();
    d.setTime(d.getTime() + (exdays*24*60*60*1000));
    var expires = "expires="+ d.toUTCString();
    document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie (cname) {
    var name = cname + "=";
    var decodedCookie = decodeURIComponent(document.cookie);
    var ca = decodedCookie.split(';');
    for(var i = 0; i < ca.length; i++) {
        var c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}
function formatPrice(val) {
    var value = formatComma(val);
    return '<div style="text-align: right; ">' + value + '</div>';
}
function formatComma(val){
    return !isNaN(parseFloat(val)) ? parseFloat(val).toFixed(2).toString().replace(/\B(?=(?:\d{3})+(?!\d))/g, ",") : val;
}

function sleep(milliseconds) {
  var start = new Date().getTime();
  for (var i = 0; i < 1e7; i++) {
    if ((new Date().getTime() - start) > milliseconds){
      break;
    }
  }
}


function submitForm() {
    var input, file;

    // (Can't use `typeof FileReader === "function"` because apparently
    // it comes back as "object" on some browsers. So just see if it's there
    // at all.)
    if (!window.FileReader) {
        alert("The file API isn't supported on this browser yet.");
    }

    form = document.getElementById('mainForm');
    input = document.getElementById('contentFile');
    if (!input) {
        alert("Um, couldn't find the fileinput element.");
    }
    else if (!input.files) {
        alert("This browser doesn't seem to support the `files` property of file inputs.");
    }
    else if (!input.files[0]) {
        alert("Please select a file before clicking 'upload'");
    }
    else {
        file = input.files[0];
        if(file.size > 20971520){
            alert(file.name + " exceed limited 20 MB file size (" + (file.size/1048576).toFixed(2) + " MB found)");
        }
        else{
            form.submit()
            return true
        }
    }
    return false
}
