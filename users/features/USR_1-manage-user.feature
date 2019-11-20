Feature: จัดการ User
  :usecase: USR_1

  Scenario: Administrator can create new user
    Given I logged in as admin
      And I visit manage/users/
      And I click User
     When click button เพิ่ม ผู้ใช้
      And fill form username with newuser
      And fill form password1 with user1234
      And fill form password2 with user1234
      And click button บันทึก
     Then I see "newuser" was added successfully
     When fill form first_name with สมชาย
      And fill form last_name with สบายดี
      And fill form email with somchai@thevcgroup.com
      And click button บันทึก
     Then I see "newuser" was changed successfully

  Scenario: Administrator can edit existing user
    Given I logged in as admin
      And I visit manage/users/
      And I click User
     When click button เพิ่ม ผู้ใช้
      And fill form username with newuser
      And fill form password1 with user1234
      And fill form password2 with user1234
      And click button บันทึก
     Then I see "newuser" was added successfully
     When fill form first_name with สมชาย
      And fill form last_name with สบายดี
      And fill form email with somchai@thevcgroup.com
      And click button บันทึก
     Then I see "newuser" was changed successfully
     When click button newuser
     Then fill form first_name with ชื่อใหม่
      And click button บันทึก
     Then I see "newuser" was changed successfully

  Scenario: Administrator can delete existing user
    Given I logged in as admin
      And I visit manage/users/
      And I click User
     When click button เพิ่ม ผู้ใช้
      And fill form username with newuser
      And fill form password1 with user1234
      And fill form password2 with user1234
      And click button บันทึก
     Then I see "newuser" was added successfully
      And I see ลบ
      And click link ลบ
     Then I see คุณแน่ใจหรือที่จะลบ ผู้ใช้ "newuser"
     When click button ใช่, ฉันแน่ใจ
     Then I see ลบ ผู้ใช้ "newuser" เรียบร้อยแล้ว

#  Scenario: Administrator can setup LDAP
#    Given I logged in as admin
#      And I visit admin/
#     When I click Config
#     Then I see users_LDAP_ENABLED
#     When check users_LDAP_ENABLED
#      And fill form users_LDAP_HOST with 192.168.55.66
#      And fill form users_LDAP_DOMAIN with ad.thevcgroup.com
#      And click button บันทึก
#     Then I see Live settings updated successfully
