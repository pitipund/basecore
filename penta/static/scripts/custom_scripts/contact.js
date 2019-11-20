function showSpinner(){
    var target = document.getElementById('spinnerbar');
    var spinner = new Spinner().spin();
    target.appendChild(spinner.el);
    document.getElementById('sendBtn').className = 'btn btn-success disabled';
    document.forms['contactForm'].submit();
}

///////////////////////////////////////////////////////////////////
// Powered By MapsEasy.com Maps Generator                        
// Please keep the author information as long as the maps in use.
// You can find the free service at: http://www.MapsEasy.com     
///////////////////////////////////////////////////////////////////
function LoadGmaps() {
    var myLatlng = new google.maps.LatLng(13.7218678,100.4995579);
    var myOptions = {
        zoom: 16,
        center: myLatlng,
        disableDefaultUI: true,
        navigationControl: true,
        navigationControlOptions: {
            style: google.maps.NavigationControlStyle.ZOOM_PAN
        },
        mapTypeControl: true,
        mapTypeControlOptions: {
            style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR
        },
        streetViewControl: true,
        mapTypeId: google.maps.MapTypeId.ROADMAP
    };
    var map = new google.maps.Map(document.getElementById("MyGmaps"), myOptions);
    var marker = new google.maps.Marker({
        position: myLatlng,
        map: map,
        title:"13.721873,100.499547"
    });
    var infowindow = new google.maps.InfoWindow({
        content: "TheVCGroup"
    });
    google.maps.event.addListener(marker, "click", function() {
        infowindow.open(map, marker);
    });
}
