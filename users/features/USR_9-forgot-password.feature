Feature: ลืมรหัสผ่าน
  :usecase: USR_9

  Scenario: User successfully reset his password
    Given user test with email test@mail.com
      And I visit main page
      And I click ลืมรหัสผ่าน?
     When fill form email with test@mail.com
      And click button ตั้งรหัสผ่านของฉันใหม่
     Then I see We've emailed you instructions for setting your password
      And I got email
      And email was sent to test@mail.com
      And click reset password link from email
     Then I see ยืนยันการเปลี่ยนรหัสผ่าน
     When fill form new_password1 with pa$$word
      And fill form new_password2 with pa$$word
      And click button เปลี่ยนรหัสผ่านของฉัน
     Then I see รหัสผ่านของคุณได้รับการตั้งค่าแล้ว
     When I click เข้าสู่ระบบ
      And I wait for modal Login.active
     When I fill in Username with test
      And I fill in Password with pa$$word
      And I click Login
     Then I see เปลี่ยนรหัสผ่าน
     Then I see Log out
