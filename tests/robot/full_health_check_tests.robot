*** Settings ***
Documentation    Tests the complete project, start to finish, like a real user.
Resource         resources.robot
Suite Setup      Connect To The Forest API

*** Test Cases ***
A Registered Region Can Be Health Checked
    ${region}=    Register A Test Region    Full Flow Grove ${{ $RANDOM }}
    ${region_id}=    Set Variable    ${region.json()}[id]

    ${request_body}=    Create Dictionary
    ...    start_date=2026-06-01
    ...    end_date=2026-06-30
    ...    max_cloud_percent=${20.0}

    ${response}=    POST On Session    forest_api    /regions/${region_id}/health-check    json=${request_body}

    Should Be Equal As Integers    ${response.status_code}    200
    Should Not Be Empty    ${response.json()}[status]
    Should Be True    ${response.json()}[greenness_score] >= -1.0

Health Check On A Missing Region Returns Not Found
    ${request_body}=    Create Dictionary
    ...    start_date=2026-06-01
    ...    end_date=2026-06-30
    ...    max_cloud_percent=${20.0}

    ${response}=    POST On Session    forest_api
    ...    /regions/00000000-0000-0000-0000-000000000000/health-check
    ...    json=${request_body}    expected_status=404

    Should Be Equal As Integers    ${response.status_code}    404