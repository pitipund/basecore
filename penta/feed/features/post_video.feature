Feature: User can post video
    As a user

    Scenario: Post youtube video to feed page
        Given I logged in
          And I go to "/th/"
	      And I should see an element with id of "nav_master" within 3 seconds
          And I fill in "link" with "https://www.youtube.com/watch?v=0aU57V6VBW0"
         When I click element with id "sharevideo"
         Then I should see "Love Will Keep Us Together" within 3 seconds

    Scenario: Post unknown URL to feed page
        Given I logged in
          And I go to "/th/"
	      And I should see an element with id of "nav_master" within 3 seconds
          And I fill in "link" with "http://www.google.com/"
         When I click element with id "sharevideo"
         Then I should see an alert with text "เกิดความผิดพลาด กรุณาทดลองใหม่ภายหลัง"
          And I accept the alert
