Feature: จัดการ Location
  :usecase: USR_3

  Scenario: Administrator can create new location
    Given I logged in as admin
      And I visit manage/users/
      And click button Location
     When click button เพิ่ม location
      and fill form name with อาคารหลัก
      and click button บันทึก
     Then I see location "อาคารหลัก" was added successfully

  Scenario: Administrator can edit existing location
    Given I logged in as admin
      And I visit manage/users/
      And click button Location
     When click button เพิ่ม location
      and fill form name with อาคารหลัก
      and click button บันทึก
     Then I see location "อาคารหลัก" was added successfully
     When click button อาคารหลัก
      and fill form name with อาคารรอง
      and click button บันทึก
     Then I see "อาคารรอง" was changed successfully

  Scenario: Administrator can delete existing location
    Given I logged in as admin
      And I visit manage/users/
      And click button Location
     When click button เพิ่ม location
      and fill form name with อาคารหลัก
      and click button บันทึก
     Then I see location "อาคารหลัก" was added successfully
     When click button อาคารหลัก
      and click button ลบ
     Then I see คุณแน่ใจหรือที่จะลบ location "อาคารหลัก"
     When click button ใช่, ฉันแน่ใจ
     Then I see ลบ location "อาคารหลัก" เรียบร้อยแล้ว
