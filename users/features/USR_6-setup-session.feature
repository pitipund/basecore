Feature: ตั้งค่า Session
  :usecase: USR_6

  Scenario: Administrator setup session settings
    Given I logged in as admin
      And I visit manage/constance/
      And click button Config: users
      And I see users_MAXIMUM_SESSION_PER_USER
     When fill form users_MAXIMUM_SESSION_PER_USER with 1
      And fill form users_INACTIVITY_TIMEOUT with 2
      And fill form users_SESSION_TIMEOUT with 60
     Then click button บันทึก
