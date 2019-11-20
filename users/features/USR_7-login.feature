Feature: เข้าสู่ระบบ
  :usecase: USR_7

  Scenario: User successfully login to system
    Given superuser test with password 12345678
      And I visit main page
      And I wait for modal Login.active
     When I fill in Username with test
      And I fill in Password with 12345678
      And I click Login
     Then I see เปลี่ยนรหัสผ่าน
     Then I see Log out

  Scenario: User successfully login to system, and logout from system
    Given superuser test with password 12345678
      And I visit main page
      And I wait for modal Login.active
     When I fill in Username with test
      And I fill in Password with 12345678
      And I click Login
     Then I see เปลี่ยนรหัสผ่าน
     Then I see Log out
     When I click Log out
     Then I wait for modal Login.active
      And I see Username
      And I see Password
      And I see Login

  Scenario: User enter wrong username
    Given superuser test with password 12345678
      And I visit main page
      And I wait for modal Login.active
     When I fill in Username with wrong_username
      And I fill in Password with 12345678
      And I click Login
     Then I see กรุณาใส่ ชื่อผู้ใช้ และรหัสผ่านที่ถูกต้อง มีการแยกแยะตัวพิมพ์ใหญ่-เล็ก

  Scenario: User enter wrong password
    Given superuser test with password 12345678
      And I visit main page
      And I wait for modal Login.active
     When I fill in Username with test
      And I fill in Password with wrong_password
      And I click Login
     Then I see กรุณาใส่ ชื่อผู้ใช้ และรหัสผ่านที่ถูกต้อง มีการแยกแยะตัวพิมพ์ใหญ่-เล็ก

