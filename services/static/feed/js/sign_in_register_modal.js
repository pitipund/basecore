// show guest dialog
$(document).ready(function() {

    $.fn.validateEmailForm = function() {

      var thisForm = $(this),
          thisFeedBack = thisForm.parent().find("span.glyphicon");

      function validateEmail(email) {
          var re = /^([\w-]+(?:\.[\w-]+)*)@((?:[\w-]+\.)*\w[\w-]{0,66})\.([a-z]{2,8}(?:\.[a-z]{2})?)$/i;
          return re.test(email);
      } 

      thisForm.on("input",function(){
        if($(this).val()==""){
          thisForm.parent().removeClass("has-error has-success");
          thisForm.parent().addClass("has-warning");
          thisFeedBack.removeClass("glyphicon-ok glyphicon-remove");
          thisFeedBack.addClass("glyphicon-asterisk");
          thisForm.data("status","warning")
        } else if(validateEmail($(this).val())) {
          thisForm.parent().removeClass("has-error has-warning");
          thisForm.parent().addClass("has-success");
          thisFeedBack.removeClass("glyphicon-asterisk glyphicon-remove");
          thisFeedBack.addClass("glyphicon-ok");
          thisForm.data("status","ok")
        } else {
          thisForm.parent().removeClass("has-success has-warning");
          thisForm.parent().addClass("has-error");
          thisFeedBack.removeClass("glyphicon-asterisk glyphicon-ok");
          thisFeedBack.addClass("glyphicon-remove");
          thisForm.data("status","invalid")
        }
      });

      return this;
    };

    $.fn.validateRequiredForm = function(){
      
      var thisForm = $(this),
          thisFeedBack = thisForm.parent().find("span.glyphicon");

      function validateForm(){
        return thisForm.val().length > 0;

      }

      thisForm.on("input",function(){
        if(validateForm()){
          thisForm.parent().removeClass("has-warning");
          thisForm.parent().addClass("has-success");
          thisFeedBack.removeClass("glyphicon-asterisk");
          thisFeedBack.addClass("glyphicon-ok")
          thisForm.data("status","ok")

        } else{
          thisForm.parent().removeClass("has-success");
          thisForm.parent().addClass("has-warning");
          thisFeedBack.removeClass("glyphicon-ok");
          thisFeedBack.addClass("glyphicon-asterisk")
          thisForm.data("status","warning")
        } 
      });

      return this;
    };

    $.fn.verifyForm = function(verifiedForm){

      var thisForm = $(this),
          verifiedForm = verifiedForm,
          thisFeedBack = thisForm.parent().find("span.glyphicon");

      function verifyForm(){
        return thisForm.val() == verifiedForm.val();
      }

      var updateUI = function(){
        if(verifyForm()){
          thisForm.parent().removeClass("has-warning");
          thisForm.parent().addClass("has-success");
          thisFeedBack.removeClass("glyphicon-asterisk");
          thisFeedBack.addClass("glyphicon-ok");
          thisForm.data("status","ok")

        } else{
          thisForm.parent().removeClass("has-success");
          thisForm.parent().addClass("has-warning");
          thisFeedBack.removeClass("glyphicon-ok");
          thisFeedBack.addClass("glyphicon-asterisk");
          thisForm.data("status","warning")
        } 
      };

      thisForm.on("input",updateUI);
      verifiedForm.on("input",updateUI);

      return this;
    };

    $("#signin-password").keypress(function(e){
      if(e.which==13) {
        $("#formSignInSubmit").click();  
      }
    });

    var registrationForm = [];
    registrationForm.push($("input#register-first_name").validateRequiredForm());
    registrationForm.push($("input#register-last_name").validateRequiredForm());
    registrationForm.push($("input#register-email").validateEmailForm());
    registrationForm.push($("input#register-password").validateRequiredForm());
    registrationForm.push($("input#verify-password").verifyForm($("input#register-password")));

    $("#leftbar a, .btn-share, .btn-save, #follow-button, .likestatus, #sharevideo, .btn-subscribe, .btn-fb-share").removeAttr("data-target")
             .removeAttr("data-toggle")
             .removeAttr("onclick")
             .attr('href', '#')
             .off('click')
             .click(function() {
      $("#guestModal").modal();
      return false;
    });
    $(".room-link").off('click').attr('href', '/th/room/');

    $("#formSignInSubmit").click(function () {
        $(this).button("loading");
        var sign_in_form = $("#signin-form");
        sign_in_form.ajaxSubmit({
            url: "https://accounts.thevcgroup.com/apis/v1/login/",
            type: 'POST',
            success: onDone,
            error: onFail
        });

        function onDone (responseText, status) {
            console.log(responseText);
            var data = responseText;
            console.log(data.email);
            console.log(data.redirect_url);
            window.location.href = data.redirect_url;
        }
        function onFail (response, status, xhr) {
            var detail = JSON.parse(response.responseText).detail;
            if (detail == "Authentication fails") {
                alert($("#text_invalid_email_or_password").val());
            } else {
                alert(detail);
            }
            $(".btn-login").button("reset");
        }
    });

    $("#formRegisterSubmit").click(function () {
        $(this).button("loading");
        for(index in registrationForm) {
          currentForm = registrationForm[index];
          currentForm.trigger("input");
          if(currentForm.data("status")!="ok"){
            alert(currentForm.data("alertText"));
            $(this).button("reset");
            return;
          }
        }

        var data = {
            first_name: $("#register-first_name").val(),
            last_name: $("#register-last_name").val(),
            email: $("#register-email").val(),
            password: $("#register-password").val(),
            login_url: $("#login_url").val(),
        };

        $.each(registrationForm, function(index, form){
          form.attr("readonly","readonly");
        });

        $.ajax({
            url: "https://accounts.thevcgroup.com/apis/v1/new_user/",
            type: 'POST',
            dataType: 'json',
            contentType: "application/json; charset=utf-8",
            headers: {
                Authorization: 'ApiKey pentachannel:f6176e857b7f99c91609f2c618114bff7f8b92ef',
                'Content-Type': 'application/json'
            },
            data: JSON.stringify(data),
            success: onDone,
            error: onFail
        });

        function onDone (responseText, status) {
            console.log(responseText);
            var data = responseText;
            console.log(data.email);
            console.log(data.redirect_url);
            window.location.href = data.redirect_url;
        }
        function onFail (response, status, xhr) {
            console.log(response);
            $("#formRegisterSubmit").button("reset");
            $.each(registrationForm, function(index, form){
              form.removeAttr("readonly");
            });
            
            var data = JSON.parse(response.responseText);
            var detail = data.detail;
            if (detail == 'Missing required fields (email, password)') {
              alert($("#text_missing_require_field").val());
            } else if (detail.match('already registered')) {
              alert($("#text_email_used").val());
            } else {
              alert($("#text_unknown_error").val());
            }
        }
    });

    $(".btn-login").click(function(){
      $(this).button("loading");
    });

    $(".btn-register").click(function () {
        $('#guestModal').modal('hide');
        $('#guestModalRegister').modal('show');
    });

    $(".btn-to-login").click(function(){
        $('#guestModalRegister').modal('hide');
        $('#guestModal').modal('show');
        
    })
});
