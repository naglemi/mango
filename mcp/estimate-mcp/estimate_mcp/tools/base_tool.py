"""
Base tool class for Estimate MCP tools.
"""

from typing import Any, Dict, Generic, Type, TypeVar
from pydantic import BaseModel, create_model

# Type variable for input schema
I = TypeVar('I', bound=BaseModel)
# Type variable for output schema
O = TypeVar('O', bound=BaseModel)

class BaseTool(Generic[I, O]):
    """
    Base class for all Estimate MCP tools.

    All tools should inherit from this class and implement the _run method.
    """

    # These should be overridden by subclasses
    input_schema: Type[I] = None
    output_schema: Type[O] = None

    def __init__(self):
        """Initialize the tool."""
        if self.input_schema is None:
            # Create an empty input schema if none is provided
            self.input_schema = create_model('EmptyInputSchema', __base__=BaseModel)

        if self.output_schema is None:
            # Create an empty output schema if none is provided
            self.output_schema = create_model('EmptyOutputSchema', __base__=BaseModel)

    def run(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the tool with the given arguments.

        Args:
            args: A dictionary of arguments to pass to the tool.

        Returns:
            A dictionary containing the tool's output.
        """
        # Parse input using the input schema
        input_obj = self.input_schema(**args)

        # Run the tool implementation
        output = self._run(input_obj)

        # If output is already a dict, return it
        if isinstance(output, dict):
            return output

        # Otherwise, convert to dict using the output schema
        if isinstance(output, BaseModel):
            return output.model_dump()

        # If output is not a BaseModel instance, wrap it in the output schema
        return self.output_schema(**output).model_dump()

    def _run(self, input_obj: I) -> O:
        """
        Implement this method in subclasses to define the tool's behavior.

        Args:
            input_obj: An instance of the input schema.

        Returns:
            An instance of the output schema or a dictionary.
        """
        raise NotImplementedError("Subclasses must implement _run method")
