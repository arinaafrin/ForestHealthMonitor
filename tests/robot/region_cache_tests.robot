*** Settings ***
Documentation    Checks that asking for the same region twice still works,
...              and gives the same answer both times, using the cache.
Resource         resources.robot
Suite Setup      Connect To The Forest API

*** Test Cases ***
Asking for the same region twice gives the same answer
    ${rand}=    Evaluate    random.randint(1000, 9999)    modules=random
    ${created}=    Register A Test Region    Cache Test Grove ${rand}
    ${region_id}=    Set Variable    ${created.json()}[id]

    ${first_answer}=    GET On Session    forest_api    /regions/${region_id}
    ${second_answer}=    GET On Session    forest_api    /regions/${region_id}

    Should Be Equal As Integers    ${first_answer.status_code}    200
    Should Be Equal As Integers    ${second_answer.status_code}    200
    Should Be Equal    ${first_answer.json()}[name]    ${second_answer.json()}[name]

Looking up a region that does not exists returns not found
    ${response}=    GET On Session    forest_api    /regions/00000000-0000-0000-0000-000000000000    expected_status=404
    Should Be Equal As Integers    ${response.status_code}    404