"use strict";

/**
 *
 * @param type "playlist" or "live"
 * @param id playlist_id or live_id
 * @param action ["play"|"pause"|"seek"|"finish"]
 * @param time in second (int)
 */
function heatmap_log(type, id, action, time) {
    var b = document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)'),
        csrftoken = b ? b.pop() : '',
        xmlHttp = new XMLHttpRequest(),
        body;

    xmlHttp.open( "POST", "/api/v2/heatmap/log", false ); // false for synchronous request
    xmlHttp.setRequestHeader("Content-type", "application/json");
    xmlHttp.setRequestHeader("X-CSRFTOKEN", csrftoken);
    body = {
        type: type,
        id: id,
        action: action,
        time: time
    };
    xmlHttp.send(JSON.stringify(body));
}
