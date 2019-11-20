Feature: In /th will show welcome box for 
	user that follow fewer than 3 channels

	Scenario: Check Welcome box has been shown
	   Given: I logged in
	   	 And: I go to "/th/"
	   	 And: I should see "ยินดีต้อนรับสู่ Penta Channel!" within 3 seconds
