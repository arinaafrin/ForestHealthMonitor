*** Settings ***
Library    RequestsLibrary
Library    Collections

*** Variables ***
${BASE_URL}    http://localhost:8000

*** Keywords ***
Connect To The Forest API
    Create Session    forest_api    ${BASE_URL}

Register A Test Region
    [Arguments]    ${region_name}
    ${p1}=    Create List    ${-122.45}    ${37.75}
    ${p2}=    Create List    ${-122.44}    ${37.75}
    ${p3}=    Create List    ${-122.44}    ${37.76}
    ${p4}=    Create List    ${-122.45}    ${37.75}
    ${ring}=    Create List    ${p1}    ${p2}    ${p3}    ${p4}
    ${coords}=    Create List    ${ring}
    ${border}=    Create Dictionary    type=Polygon    coordinates=${coords}
    ${request_body}=    Create Dictionary    name=${region_name}    border_shape_geojson=${border}
    ${response}=    POST On Session    forest_api    /regions    json=${request_body}    expected_status=any
    RETURN    ${response}