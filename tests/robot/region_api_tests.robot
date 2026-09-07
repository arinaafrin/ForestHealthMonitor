*** Settings ***
Documentation    These tests check the API from outside, like a real user would.
Resource         resources.robot
Suite Setup      Connect To The Forest API

*** Test Cases ***

A New Region Can Be Registered Through The API
    ${rand}=    Evaluate    random.randint(1000, 9999)    modules=random
    ${response}=    Register A Test Region    Robot Test Grove ${rand}
    Should Be Equal As Integers    ${response.status_code}    201
    Should Not Be Empty    ${response.json()}[id]

A Newly Registered Region Shows Up In The Region List
    ${rand}=    Evaluate    random.randint(1000, 9999)    modules=random
    ${new_region}=    Register A Test Region    Robot List Grove ${rand}
    ${response}=    GET On Session    forest_api    /regions
    Should Be Equal As Integers    ${response.status_code}    200
    ${names}=    Create List
    FOR    ${region}    IN    @{response.json()}
        Append To List    ${names}    ${region}[name]
    END
    List Should Contain Value    ${names}    ${new_region.json()}[name]
        