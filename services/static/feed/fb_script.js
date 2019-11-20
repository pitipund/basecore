window.fbAsyncInit = function(){
    FB.init({
        appId  :'571837776208476', // App ID from the app dashboard
        status :true,              // Check Facebook Login status
        xfbml  :true               // Look for social plugins on the page
    });
};
(function(){ // Load the SDK asynchronously
    if (document.getElementById('facebook-jssdk')) {return;}
    var firstScriptElement = document.getElementsByTagName('script')[0];
    var facebookJS = document.createElement('script'); 
    facebookJS.id = 'facebook-jssdk';
    facebookJS.src = '//connect.facebook.net/en_US/all.js';
    firstScriptElement.parentNode.insertBefore(facebookJS, firstScriptElement);
}());
    
function fb_publish(name, description, link, picture){
    FB.ui({
        method     :'feed',
        name       :name,
        caption    :window.location.host,
        description:(description),
        link       :link,
        picture    :picture
    },
    function(response){
        if(!response && !response.post_id){
            alert('Post was not published.');
        }
    });
}