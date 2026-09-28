from pydantic import BaseModel

from core.tool import Tool, ToolResult


class EchoInput(BaseModel):
    text: str


class EchoTool(Tool[EchoInput]):
    name = "echo"
    description = "Return the provided text."
    input_model = EchoInput

    def execute(self, input: EchoInput) -> ToolResult:
        return ToolResult(success=True, output=input.text)


def test_tool_definition_and_execution() -> None:
    definition = EchoTool.definition()
    result = EchoTool().execute(EchoInput(text="hello"))

    assert definition["name"] == "echo"
    assert definition["input_schema"]["properties"]["text"]["type"] == "string"
    assert result.success is True
    assert result.output == "hello"
