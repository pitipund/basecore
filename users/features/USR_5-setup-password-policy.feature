Feature: ตั้งค่านโยบายรหัสผ่าน
  :usecase: USR_5

  Scenario: Administrator setup password policy
    Given I logged in as admin
      And I visit manage/constance/
      And click button Config: users
      And I see users_PASSWORD_AGE
     When fill form users_PASSWORD_AGE with 20
      And fill form users_PASSWORD_MIN_LENGTH with 200
      And fill form users_PASSWORD_HISTORY with 33
     Then click button บันทึก
    Given I visit main page
      And I click เปลี่ยนรหัสผ่าน
     Then I see รหัสผ่านต้องมีความยาวอย่างน้อย 200 ตัวอักษร
      And I see รหัสผ่านของคุณต้องไม่ซ้ำกับรหัสผ่านที่เคยใช้ล่าสุด 33 ครั้ง
