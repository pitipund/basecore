Feature: เปลี่ยนรหัสผ่าน
  :usecase: USR_8

  Scenario: User successfully changed his password
    Given I logged in as user
      And I visit main page
     When I click เปลี่ยนรหัสผ่าน
      And fill form old_password with user
      And fill form new_password1 with pa$$word
      And fill form new_password2 with pa$$word
      And click button เปลี่ยนรหัสผ่านของฉัน
     Then I see รหัสผ่านของคุณถูกเปลี่ยนไปแล้ว

  Scenario: User enter invalid old password
    Given I logged in as user
      And I visit main page
     When I click เปลี่ยนรหัสผ่าน
      And fill form old_password with wrong_password
      And fill form new_password1 with pa$$word
      And fill form new_password2 with pa$$word
      And click button เปลี่ยนรหัสผ่านของฉัน
      And I see ใส่รหัสผ่านเก่าผิด กรุณาใส่รหัสผ่านอีกครั้ง

  Scenario: New password does not match its confirmation
    Given I logged in as user
      And I visit main page
     When I click เปลี่ยนรหัสผ่าน
      And fill form old_password with user
      And fill form new_password1 with pa$$word
      And fill form new_password2 with SOMETHING_ELSE
      And click button เปลี่ยนรหัสผ่านของฉัน
     Then I see รหัสผ่านไม่ตรงกัน

  Scenario: New password is too short
    Given I logged in as user
      And I visit main page
     When I click เปลี่ยนรหัสผ่าน
      And fill form old_password with user
      And fill form new_password1 with 11
      And fill form new_password2 with 11
      And click button เปลี่ยนรหัสผ่านของฉัน
     Then I see รหัสผ่านนี้สั้นเกินไป

  Scenario: User reuse old password
    Given I logged in as user
      And I visit main page
     When I click เปลี่ยนรหัสผ่าน
      And fill form old_password with user
      And fill form new_password1 with pa$$word
      And fill form new_password2 with pa$$word
      And click button เปลี่ยนรหัสผ่านของฉัน
     Then I see รหัสผ่านของคุณถูกเปลี่ยนไปแล้ว
      And click button กลับสู่หน้าหลัก
     When I click เปลี่ยนรหัสผ่าน
      And fill form old_password with pa$$word
      And fill form new_password1 with user
      And fill form new_password2 with user
      And click button เปลี่ยนรหัสผ่านของฉัน
     Then I see ไม่สามารถตั้งรหัสผ่านซ้ำกับรหัสผ่านที่เคยใช้ได้

  Scenario: User reuse current password
    Given I logged in as user
      And I visit main page
     When I click เปลี่ยนรหัสผ่าน
      And fill form old_password with user
      And fill form new_password1 with pa$$word
      And fill form new_password2 with pa$$word
      And click button เปลี่ยนรหัสผ่านของฉัน
     Then I see รหัสผ่านของคุณถูกเปลี่ยนไปแล้ว
      And click button กลับสู่หน้าหลัก
     When I click เปลี่ยนรหัสผ่าน
      And fill form old_password with pa$$word
      And fill form new_password1 with pa$$word
      And fill form new_password2 with pa$$word
      And click button เปลี่ยนรหัสผ่านของฉัน
     Then I see รหัสผ่านใหม่ต้องไม่ซ้ำกับรหัสผ่านเก่า
