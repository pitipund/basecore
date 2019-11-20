Feature: Nav Bar function for guest and member

	Scenario: 1 PentaChannel logo redirect user to room page as guest
	    Given I go to "/"
	      And I should see an element with id of "nav_master" within 3 seconds
	      And I click logo
	     Then The browser's URL should contain "/th/"

	Scenario: PentaChannel logo redirect user to room page as member
	    Given I logged in
	      And I should see an element with id of "nav_master" within 3 seconds
	      And I click logo
	     Then The browser's URL should contain "/th/"

	Scenario: Search box use to search channel as guest
		Given I go to "/"
	      And I should see an element with id of "nav_master" within 3 seconds
	  	 When I search with text "EDM for Life"
         Then I should see "ผลลัพธ์จากการค้นหา" within 3 seconds

    Scenario: Search box use to search channel as member
		Given I logged in
	      And I should see an element with id of "nav_master" within 3 seconds
	  	 When I search with text "EDM for Life"
         Then I should see "ผลลัพธ์จากการค้นหา" within 3 seconds

    Scenario: 5 Profile button link to user share channel, SavedVideo link to saved channel play and Room button link user to room
    	Given I logged in
    	  And I go to "/th/"
	      And I should see an element with id of "nav_master" within 3 seconds
    	  And I click element with id "navbarShareChannelButton"
    	 Then The browser's URL should contain "/th/channel/"
    	  And I click element with id "navbarSavedVideoButton"
    	 Then The browser's URL should contain "/th/channelplay/"
    	  And I click element with id "navbarRoomButton"
    	 Then The browser's URL should contain "/th/room/"

    Scenario: Dropdown button show menu after clicked
    	Given I logged in
    	  And I go to "/th/"
	      And I should see an element with id of "nav_master" within 3 seconds
    	  And I click element with id "navbarDropdown"
    	 Then I should see "โปรไฟล์" within 1 seconds
    	  And I should see "เปลี่ยนภาษา"
      	  And I should see "คู่มือการใช้งาน"
      	  And I should see "ลงชื่อออก"

    Scenario: Anonymous name links to login modal
        Given I go to "/"
          And I should see "Anonymous" within 3 seconds
          And I click element with id "userTitle-left"
         Then In modal
          And Modal close 

    Scenario: As anonymouse Save video links to login modal
        Given I go to "/"
          And I should see "วิดีโอที่เก็บไว้ดู" within 10 seconds
          And I click element with id "savedVideo-left"
         Then In modal
          And Modal close 

