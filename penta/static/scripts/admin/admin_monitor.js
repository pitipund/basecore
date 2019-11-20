function monitor_confirm(id, action){
	switch(action){
        case 'R':
        	confirmMsg = confirm('Are you sure you want to submit action restart?');
        	break;
        case 'B':
        	confirmMsg = confirm('Are you sure you want to submit action bad?');
        	break;
    }
    if(confirmMsg){
        send_monitor_log(id, action);
    }
}

function send_monitor_log(id, action){
    var btn = document.getElementById(action+'btn_'+id);
    btn.className = btn.className+' disabled'
    var player = document.getElementById(id);
    $.get(SEND_MONITOR_LOG_URL+'?id='+id+'&action='+action, function(data) {
        if(data.msg==true){
            set_span(id, action, data.status, data.update_at);
            switch(data.command){
                case 'stop':
                    if(action=='B'){
                        set_new_player(player, data.id, data.url, id, false)
                    }
                    else if(action=='G'){
                        player.sendEvent("STOP");
                    }
                    break;
                case 'replay':
                    player.sendEvent("PLAY");
                    break;
                case 'play':
                    set_new_player(player, data.id, data.url, id, true)
                    break;
            }
        }
        else{
            alert(data.result);
            player.sendEvent("PLAY");
        }
    });
}

function set_span(id, action, status, time){
    var span = document.getElementById('status_'+id)
    switch(status){
        case 'G':
            span.className = "label label-success pull-right";
            var span_time = 'Good at ';
            break;
        case 'R':
            span.className = "label label-danger pull-right";
            var span_time = 'Restart at ';
            break;
        case 'B':
            span.className = "label label-default pull-right";
            var span_time = 'Bad at ';
            break;
    }
    span.innerHTML = '';
    span.innerHTML = span_time+time;
    var btn = document.getElementById(action+'btn_'+id);
    btn.className = btn.className.replace(' disabled', '');
}

function set_new_player(player, newid, newurl, oldid, isstart){
    player.remove();
    $("#div_"+oldid).append('<embed id="'+newid+'" name="'+newid+'" type="application/x-shockwave-flash" src="'+MEDIA_URL+'jwplayer/player.swf" quality="low" allowscriptaccess="always" allowfullscreen="false" flashvars="autostart='+isstart+'&file='+newurl+'&provider=http&http.startparam=start&stretching=exactfit" style="padding:5px;" width="100%" height="100%">');
    var gbtn = document.getElementById('Gbtn_'+oldid);
    gbtn.setAttribute("onclick", "send_monitor_log("+"'"+newid+"'"+", 'G')");
    gbtn.id = 'Gbtn_'+newid;
    var rbtn = document.getElementById('Rbtn_'+oldid);
    rbtn.setAttribute("onclick", "send_monitor_log("+"'"+newid+"'"+", 'R')");
    rbtn.id = 'Rbtn_'+newid;
    var bbtn = document.getElementById('Bbtn_'+oldid);
    bbtn.setAttribute("onclick", "send_monitor_log("+"'"+newid+"'"+", 'B')");
    bbtn.id = 'Bbtn_'+newid;
    document.getElementById('status_'+oldid).id = 'status_'+newid;
    document.getElementById('div_'+oldid).id = 'div_'+newid;
}