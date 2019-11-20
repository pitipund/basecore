$(document).ready(function(){
    set_first(image);
});

function set_first(image){
    var username_label = lib_createObj(null, "p", "form-control-static");
    username_label.innerHTML = username;
    var username_master = document.getElementById('username_div');
    username_master.appendChild(username_label);
    var img_master = document.getElementById('image_div');
    if(image != ""){
        var currentImg_label = lib_createObj(null, "p", "form-control-static");
        currentImg_label.innerHTML = current_text+": ";
        var currentImg_a = lib_createObj(null, "a", "form-control-static");
        currentImg_a.innerHTML = image;
        currentImg_a.setAttribute("href", image);
        var change_label = lib_createObj(null, "p", "form-control-static");
        change_label.innerHTML = change_text+":";
        img_master.appendChild(currentImg_label);
        currentImg_label.appendChild(currentImg_a);
        img_master.appendChild(change_label);
        
    }
    var file_input = lib_createObj("image_input" ,"input", null);
    file_input.type = "file";
    img_master.appendChild(file_input);
}

function submit_profile(){
    //if(document.getElementById('url_nameInput').value == "admin"){
    //    alert(error_text);
    //}
    //else{
        set_spinner('spinnerbar', 'submitBtn', 'cancelBtn');
        document.forms['profile_update_form'].submit()
    //}
}