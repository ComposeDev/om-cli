# custom/action_packs/kafka_pack.py

from confluent_kafka import KafkaException, Producer

from src.om_cli.models.om_parameter import OMParameter
from src.om_cli.models.om_parameter_list import OMParameterList
from src.om_cli.models.result_object import ResultObject

PARAMETER_DEFINITIONS = {
    "massage_data_to_kafka": {
        "topic": {"direction": "input", "type": "STRING"},
        "key": {"direction": "input", "type": "STRING"},
        "data": {"direction": "input", "type": "STRING"},
        "value": {"direction": "output", "type": "STRING"},
    },
    "send_message_to_kafka": {
        "topic": {"direction": "input", "type": "STRING"},
        "key": {"direction": "input", "type": "STRING"},
        "value": {"direction": "input", "type": "STRING"},
        "kafka_server_path": {"direction": "input", "type": "STRING"},
    },
}


def massage_data_to_kafka(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for potentially massaging data to be sent to Kafka if needed.

    OMParameters used:
        - data: The data to massage (Read)
        - topic: The topic to send the message to (Read)
        - key: The key of the message (Read)
        - value: The value of the message, tha value from the data OMParameter (Created).

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If the data parameter value is missing.
        Exception: If an unexpected error occurs while massaging the data.
    """

    def extract_parameter_value(name: str, default=None):
        found, parameter = action_parameters.get_om_parameter(name, action_index)
        return parameter.value if found else default

    try:
        # topic = extract_parameter_value("topic")
        # key = extract_parameter_value("key")
        data = extract_parameter_value("data")

        if not data:
            raise ValueError("Missing data")

        om_parameters = OMParameterList()
        om_parameters.add_parameter(
            OMParameter(
                name=action_parameters.override_internal_action_parameter_name(
                    "value", action_index
                ),
                value=data,
                action_index=action_index,
            )
        )

        result_object = ResultObject(True, "Data massaged", None, om_parameters)
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while massaging the data: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


def send_message_to_kafka(
    result_object: ResultObject, action_parameters: OMParameterList, action_index: int
) -> ResultObject:
    """
    Action for sending a message to Kafka.

    OMParameters used:
        - topic: The topic to send the message to.
        - key: The key of the message.
        - value: The value of the message.
        - kafka_server_path: The Kafka server path.

    Args:
        result_object (ResultObject): The result object from the previous action and the variable to store the result of the current action.
        action_parameters (OMParameterList): Accumulated parameters from previous actions.
        action_index (int): The index of the current action in the operation.

    Returns:
        ResultObject: The updated result object.

    Raises:
        ValueError: If any of the required parameters (topic, key, value) are missing.
        Exception: If an unexpected error occurs while sending the message to Kafka.
    """

    def extract_parameter(name: str, default=None):
        found, parameter = action_parameters.get_om_parameter(name, action_index)
        return parameter.value if found else default

    try:
        topic_parameter = extract_parameter("topic")
        key_parameter = extract_parameter("key")
        value_parameter = extract_parameter("value")
        kafka_server_path_parameter = extract_parameter("kafka_server_path")

        if not topic_parameter or not key_parameter or not value_parameter:
            raise ValueError("Missing topic, key, or value")

        if kafka_server_path_parameter:
            kafka_server_path = kafka_server_path_parameter

        if not kafka_server_path:
            raise ValueError("No kafka_server_path provided")

        kafka_result = _produce_kafka_message(
            kafka_server_path, topic_parameter, str(value_parameter), key_parameter
        )
        result_object = kafka_result
    except Exception as ex:
        result_object = ResultObject(
            False,
            f"An unexpected error occurred while sending a message to Kafka: {ex}",
            None,
            OMParameterList(),
        )

    return result_object


"""
Helper functions
"""


def _produce_kafka_message(server_path: str, topic: str, value: str, key: str) -> ResultObject:
    """
    Produce a message to a Kafka topic.

    Args:
        server_path (str): The Kafka server path.
        topic (str): The topic to send the message to.
        value (str): The value of the message.
        key (str): The key of the message.
    """

    try:
        if server_path != "TEST":
            producer = Producer({"bootstrap.servers": server_path})
            producer.produce(topic, value, key)
            producer.flush(timeout=10)
        result_object = ResultObject(
            True, "Kafka message produced successfully", None, OMParameterList()
        )
    except KafkaException as ex:
        result_object = ResultObject(
            False, f"Failed to produce Kafka message: {ex}", None, OMParameterList()
        )

    return result_object
