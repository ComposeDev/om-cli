# src/om_cli/handlers/api_handler.py

"""
This module contains the API handling logic for the OM CLI.
"""

import json
from unittest.mock import Mock

import requests
from rich.json import JSON

from src.om_cli.helpers.text_helpers import debug_print_text
from src.om_cli.logger import logger, logging
from src.om_cli.models.om_parameter import OMParameter, OMParameterType
from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.models.result_object import ResultObject
from src.om_cli.services.custom_components_processing import CustomComponents


class APIHandler:
    """
    A class that handles API requests based on the given API definitions.

    Attributes:
        custom_components (CustomComponents): An instance of the CustomComponents class containing the api definitions and mock api responses.
    """

    def __init__(self, custom_components: CustomComponents):
        self.custom_components = custom_components
        self.mock_responses = custom_components.get_mock_api_responses()

    def process_api_request(
        self,
        endpoint_name: str,
        endpoint_parameters: OMParameterList,
        action_index: int,
    ):
        """
        Processes an API request based on the given endpoint name and parameters.

        Args:
            endpoint_name (str): The name of the API endpoint to process.
            endpoint_parameters (list): A list of OMParameter objects containing the endpoint parameters.
            action_index (int): The index of the current action in the operation.

        Returns:
            ResultObject: A ResultObject containing the result of the API request.
        """
        # Convert the response data to a Python dictionary
        # TODO: Change so that it returns if it succeeded as well

        def assign_response_variables(response, endpoint) -> OMParameterList:
            om_parameters = OMParameterList()
            if response.status_code == 200 and response.text == "":
                logger.debug("The request was successful with an empty response")

                om_parameters.add_parameter(
                    OMParameter(
                        name="api_result",
                        value=f"The {endpoint_name} API call succeeded",
                        action_index=action_index,
                    )
                )

                return om_parameters
            else:
                return (
                    om_parameters
                    if response.status_code >= 400
                    else self._extract_values_from_response(
                        response, endpoint.get("response_variables", {}), action_index
                    )
                )

        try:
            current_api_definition, current_api_endpoint = (
                self.custom_components.get_api_endpoint_and_definition(endpoint_name)
            )

            if not current_api_endpoint:
                raise ValueError(f"Unknown endpoint {endpoint_name}")

            timeout = current_api_definition.get("request_timeout", 10)

            url, headers, data, params = self._replace_placeholders(
                current_api_endpoint, endpoint_parameters
            )

            logger.debug(
                "Performing %s request to %s with headers: %s, data: %s, params: %s, request timeout: %s",
                current_api_endpoint["request_type"],
                url,
                headers,
                data,
                params,
                timeout,
            )

            request_method = {
                "GET": requests.get,
                "POST": requests.post,
                "PUT": requests.put,
                "DELETE": requests.delete,
            }.get(current_api_endpoint["request_type"])

            if not request_method:
                raise ValueError(f"Unknown request type {current_api_endpoint['request_type']}")

            if not self.mock_responses:
                # Only include data for POST and PUT requests
                response = request_method(
                    url,
                    headers=headers,
                    params=params,
                    timeout=timeout,
                    **(
                        {"data": data}
                        if current_api_endpoint["request_type"] in ["POST", "PUT"]
                        else {}
                    ),
                )
            else:
                response = self._get_mock_response(url, headers, params, timeout)

            response_variables = assign_response_variables(response, current_api_endpoint)

            return ResultObject(
                response.status_code < 400,
                (
                    ""
                    if response.status_code < 400
                    else f"{str(response.status_code)} | {response.text}"
                ),
                response,
                response_variables,
            )
        except requests.exceptions.RequestException as ex:
            return ResultObject(
                success=False,
                text=f"An error occurred during the API request: {ex}",
                response=None,
                parameters=OMParameterList(),
            )
        except Exception as ex:
            return ResultObject(
                success=False,
                text=f"An unexpected error occurred while processing the request: {ex}",
                response=None,
                parameters=OMParameterList(),
            )

    def _replace_placeholders(self, endpoint, endpoint_parameters: OMParameterList):
        """
        Replaces placeholders in the API endpoint URL, headers, data, and params with the corresponding parameter values.

        Args:
            endpoint (dict): The API endpoint configuration.
            endpoint_parameters (list): A list of OMParameter objects containing the endpoint parameters.

            Returns:
            tuple: A tuple containing the updated URL, headers, data, and params.

        """
        url = endpoint.get("url", "") or ""
        headers = endpoint.get("headers", {}) or {}
        data = endpoint.get("data", "") or ""
        params = endpoint.get("params", "") or ""

        for om_parameter in endpoint_parameters:
            key = om_parameter.api_parameter_name or om_parameter.name
            value = str(om_parameter.value)
            placeholder = "{" + key + "}"
            url = url.replace(placeholder, value)
            headers = {
                k: v.replace(placeholder, value) if isinstance(v, str) else v
                for k, v in headers.items()
            }
            data = data.replace(placeholder, value)
            params = params.replace(placeholder, value)

        return url, headers, data, params

    def _extract_values_from_response(self, response, response_variables, action_index: int):
        """
        Extracts values from a response object based on the provided response variables.

        Args:
            response (object): The response object.
            response_variables (dict): A dictionary containing the response variables and their corresponding paths.
            action_index (int): The index of the current action in the operation.

        Returns:
            list: A list of extracted values as OMParameter objects.

        Raises:
            ValueError: If the response data cannot be decoded as JSON.
            Exception: If an error occurs while extracting values from the response.
        """
        try:
            response_data = response.json()
        except ValueError:
            logger.error("Failed to decode JSON from response")
            return []

        extracted_om_parameters = OMParameterList()

        try:
            if not response_variables:
                return extracted_om_parameters
            type_mapping = {
                str: OMParameterType.STRING,
                bool: OMParameterType.BOOLEAN,
                int: OMParameterType.INTEGER,
                dict: OMParameterType.STRING,
                list: OMParameterType.STRING,
            }
            for variable, path in response_variables.items():
                value = None
                value_type = OMParameterType.STRING
                logger.debug("Extracting value for variable %s from path %s", variable, path)
                found_value = self._get_value_from_path(response_data, path)
                if found_value is None:
                    logger.error(
                        "Failed to extract variable '%s' from response using path '%s'",
                        variable,
                        path,
                    )
                elif isinstance(found_value, (str, int, float, bool)):
                    value_type = type_mapping.get(type(found_value), OMParameterType.STRING)
                    if value_type is not None:
                        value = str(found_value)
                elif isinstance(found_value, (dict, list)):
                    value_type = type_mapping.get(type(found_value), OMParameterType.STRING)
                    value = json.dumps(found_value)
                else:
                    raise ValueError("The value type is not yet supported")

                om_parameter = OMParameter(
                    type=value_type,
                    name=variable,
                    value=value,
                    action_index=action_index,
                )
                extracted_om_parameters.add_parameter(om_parameter)
                if logger.level == logging.DEBUG:
                    logger.debug("Extracted value for the parameter %s:", om_parameter.name)
                    debug_print_text(om_parameter.value)
        except Exception as ex:
            logger.error("An error occurred while extracting values from the response: %s", ex)

        return extracted_om_parameters

    def _get_value_from_path(self, data, path: str):
        """
        Retrieves the value from a nested dictionary or list based on the given path.

        Args:
            data (dict or list): The nested dictionary or list to search for the value.
            path (str): The path to the value, using dot notation to indicate nested levels.

        Returns:
            The value found at the specified path, or None if the path is not valid.

        Example:
            data = {
                'person': {
                    'name': 'John',
                    'age': 30,
                    'address': {
                        'street': '123 Main St',
                        'city': 'New York'
                    }
                }
            }
            path = 'person.address.city'
            value = get_value_from_path(data, path)
            print(value)  # Output: 'New York'
        """
        try:
            if path == ".":
                return data
            keys = path.split(".")
            for key in keys:
                if data is None:
                    return None
                if isinstance(data, list):
                    data = [
                        sub_data.get(key, None) if isinstance(sub_data, dict) else None
                        for sub_data in data
                    ]
                else:
                    data = data.get(key, None)
        except Exception as ex:
            logger.error(
                "An error occurred while retrieving the value from the API response path: %s",
                ex,
            )
            return None
        return data

    def _get_mock_response(self, url: str, headers: dict, params: dict, timeout: int):
        response = Mock(spec=requests.Response)
        response.json = self._get_predefined_responses(url, headers, params, timeout)
        response.text = json.dumps(response.json)
        response.json = Mock(return_value=response.json)
        response.headers = {"Content-Type": "application/json"}
        response.status_code = 200
        return response

    def _get_predefined_responses(self, url: str, headers: dict, params: dict, timeout: int):
        if mock_response := self.mock_responses.get(url, None):
            logger.debug("Found a predefined response for the URL: %s", url)
            json_text = JSON.from_data(data=mock_response, indent=4, highlight=True).text
            logger.debug("Mock response JSON: %s", json_text)
            return mock_response
        else:
            logger.warning("No predefined response found for the URL: %s", url)
            return {"message": "No predefined response found."}
