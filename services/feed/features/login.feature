Feature: User can login with email account and Facebook
    As a guest

    Scenario: Login with correct email & password
        Given I go to "/"
          And I should see "Login" within 3 seconds
         When I click "Login"
          And In modal
              And I should see "ด้วย Email" within 3 seconds
              And I fill in "Email" with "dev4@test.com"
              And I fill in "Password" with "dev"
              And I click "Login"
          And Modal close
          And I should see "dev4" within 3 seconds

    Scenario: After Login, redirected back to the same page
        Given I go to "/th/channelplay/2/"
          And I should see "Login" within 3 seconds
          And I click "Login"
          And In modal
              And I should see "ด้วย Email" within 3 seconds
              And I fill in "Email" with "dev4@test.com"
              And I fill in "Password" with "dev"
              And I click "Login"
          And Modal close
          And I should see an element with id of "navbarSavedVideoButton" within 3 seconds
          And I should be at "/th/channelplay/2/"

    Scenario: Login with incorrect email or password
        Given I go to "/"
          And I should see "Login" within 3 seconds
         When I click "Login"
          And In modal
              And I should see "ด้วย Email" within 3 seconds
              And I fill in "Email" with "asdfasdf"
              And I fill in "Password" with "asdfasdf"
              And I click "Login"
          And Modal close
         Then I should see an alert with text "Invalid email or password"
          And I accept the alert

    Scenario: Login with facebook
        Given I go to "/"
          And I should see "Login" within 3 seconds
         When I click "Login"
          And In modal
              And I should see "ด้วย Facebook" within 3 seconds
              And I click "Login with Facebook"
          And Modal close
          And I fill in "email" with "natt+n@thevcgroup.com"
          And I fill in "pass" with "powerall"
         Then I press "เข้าสู่ระบบ" 
          And I should see "Natt" within 10 seconds

