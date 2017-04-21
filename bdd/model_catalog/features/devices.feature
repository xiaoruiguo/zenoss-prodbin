
Feature: Devices are indexed in model catalog


Background: Connections to zodb and model catalog are available
    Given I can connect to "zodb"
    and I can connect to "model catalog"


Scenario Outline: /Server/Linux device is properly indexed
    Given the mock "/Server/Linux" device with ip "111.111.111.111" is in Zenoss
    When I search for all the device's "<OBJECT_TYPE>" in model catalog
    Then I get all the device's "<OBJECT_TYPE>"

    Examples:
        |     OBJECT_TYPE     |
        |     components      |