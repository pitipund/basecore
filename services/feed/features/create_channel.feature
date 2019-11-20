# Created by napat at 6/12/15
Feature: User creates new channel
  # Enter feature description here

  Scenario: Anonymous user should log in first
    Given I go to "/"
      And I should see "แชนแนลของฉัน" within 3 seconds
     Then I click element with id "plusCreateChannel"
      And I should see "Login เข้าสู่ Penta Channel" within 3 seconds


  Scenario: Create channel without tag and icon
    Given I logged in
      And I go to "/"
      And I should see "dev4" within 3 seconds
      And I should see "แชนแนลของฉัน" within 3 seconds
     Then I click element with id "plusCreateChannel"
     When In modal
          And I fill in "name" with "Test A"
          And I fill in "detail" with "test test test test"
          Then I click element with id "createChannelButton"
      And Modal close
     Then I should see "Test A" within 3 seconds
