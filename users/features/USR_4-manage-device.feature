Feature: ตั้งค่าหน่วยงานของเครื่องคอมพิวเตอร์
  :usecase: USR_4

  Background: Administrator setup location for division
    Given I logged in as admin
      And I visit manage/users/
      And click button Location
     When click button เพิ่ม location
      and fill form name with อาคารหลัก
      and click button บันทึก
     Then I see location "อาคารหลัก" was added successfully
    Given I visit manage/users/
      And click button Location
     When click button เพิ่ม location
      and fill form name with หอผู้ป่วย
      and click button บันทึก
     Then I see location "หอผู้ป่วย" was added successfully

  Scenario: Administrator can create new device
    Given I visit manage/users/
      And click button Device
     When click button เพิ่ม device
      and fill form computer_name with COM0
      and select อาคารหลัก from location
      and select [REG] เวชระเบียน from division
      and click button บันทึก
     Then I see device "COM0" was added successfully
