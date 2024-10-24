When an operation is started it will load all .json files inside the [project_directory]/custom/api_definitions/ directory.
They will be validated and if they pass the validation they will be loaded into the OM CLI system, otherwise an error will be thrown.

## JSON Structure

The JSON structure of the API definition contains 6 base attributes:

- **name**: The display name of the API.
- **id**: The ID to identify the API if using multiple API configurations (Not yet used, but still required).
- **request_timeout**: Seconds to wait before the REST request should timeout.
- **custom_variables**: Variables that can be used to replace placeholders inside the `api_endpoints` definitions.
    - Use the format: `{{variable_name}}` in the API endpoint properties and name the custom variable accordingly.
    - See the example structure below.
- **description**: A description field to be used as needed.
- **api_endpoints**: A list of API endpoint definitions.

### API Endpoint Definition

- **name**: Name to refer to in the operation tree when the API endpoint should be used.
- **request_type**: The type of request to be made (GET, POST, PUT, DELETE).
- **url**: The URL to make the request to.
- **headers**: Headers to be included in the request.
- **data**: Data to be included in the request body.
- **params**: Query parameters to be included in the request.
- **response_variables**: A dictionary that maps response variable names to their locations in the response.
    - This is optional and only present for some endpoints.
    - Use a '.' to represent the root of the response object.
    - Used to extract values from the response and pass them to other actions.

The endpoint definitions can also contain placeholders with one `{}` pair, which will be replaced with the value from the OMParameter with the specified parameter name when the endpoint is called.

### Usage in Operations

In the operation tree, the API endpoint can be called by using the `API_REQUEST` action type.
The `API_REQUEST` action type requires the `name` of the action to be set to the API `id` followed by a `.` and then the `name` of the endpoint from the api_endpoint config parameter to be set to the name of the API endpoint to call.

#### Usage validation
When the Menu tree is loaded the OM CLI will validate the API endpoint names used in the OM Tree and check if there is a corresponding API endpoint definition for the API endpoint being called, if not the validation will fail.

### Example 1
    
```json
...
    { "type": "API_REQUEST", "name": "test_api.get_all_registries" }
...
```

### Example Structure

```json
{
    "name": "Test API",
    "id": "test_api",
    "request_timeout": 10,
    "custom_variables": {
        "BASE_URL": "http://127.0.0.1:8080/api"
    },
    "description": "REST API for testing",
    "api_endpoints": [
        {
            "name": "get_all_registries",
            "request_type": "GET",
            "url": "{{BASE_URL}}/registries/",
            "headers": {},
            "data": null,
            "params": null,
            "response_variables": {
                "registries_json": "."
            }
        },
        {
            "name": "get_registry",
            "request_type": "GET",
            "url": "{{BASE_URL}}/registries/{registry_id}",
            "headers": {},
            "data": null,
            "params": null,
            "response_variables": {
                "identifier": "id",
                "registry_json": "data"
            }
        },
        {
            "name": "create_registry",
            "request_type": "POST",
            "url": "{{BASE_URL}}/registries/",
            "headers": { "user": "{user}" },
            "data": "{registry}",
            "params": null,
            "response_variables": null
        },
```