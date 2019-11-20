/*Select hour*/
function setHourSelect(master, id, result, sel_hour){
    var hour_p = document.createElement('span');
    hour_p.innerHTML = '&nbsp;&nbsp;&nbsp;&nbsp;Hr :&nbsp;&nbsp;&nbsp;&nbsp;';
    var hour_select = document.createElement('select');
    hour_select.id = id;
    hour_select.name = id;
    hour_select.className = 'my_select_time';
    hour_select.innerHTML = "";
    for(i in result) {
        if(result[i] == sel_hour){
            hour_select.innerHTML += "<option selected>"+result[i]+"</option>";
        }
        else{
            hour_select.innerHTML += "<option>"+result[i]+"</option>";
        }
    }
    master.appendChild(hour_p);
    master.appendChild(hour_select);
}

function setHourLoopSelect(master, id, sel_hour){ /*0-23*/
    var hour_p = document.createElement('span');
    hour_p.innerHTML = '&nbsp;&nbsp;&nbsp;&nbsp;Hr :&nbsp;&nbsp;&nbsp;&nbsp;';
    var hour_select = document.createElement('select');
    hour_select.id = id;
    hour_select.name = id;
    hour_select.className = 'my_select_time';
    hour_select.innerHTML = "";
    for(i=0;i<24;i++) {
        if(i == sel_hour){
            hour_select.innerHTML += "<option selected>"+i+"</option>";
        }
        else{
            hour_select.innerHTML += "<option>"+i+"</option>";
        }
    }
    master.appendChild(hour_p);
    master.appendChild(hour_select);
}

/*Select minute*/
function setMinuteLoopSelect(master, id, sel_min){ /*0-59*/
    var minute_p = document.createElement('span');
    minute_p.innerHTML = '&nbsp;&nbsp;&nbsp;&nbsp;Min :&nbsp;&nbsp;&nbsp;&nbsp;';
    var min_select = document.createElement('select');
    min_select.id = id;
    min_select.name = id;
    min_select.className = 'my_select_time';
    min_select.innerHTML = "";
    for(i=0;i<60;i++) {
        if(i == sel_min){
            min_select.innerHTML += "<option selected>"+i+"</option>";
        }
        else{
            min_select.innerHTML += "<option>"+i+"</option>";
        }
    }
    master.appendChild(minute_p);
    master.appendChild(min_select);
}