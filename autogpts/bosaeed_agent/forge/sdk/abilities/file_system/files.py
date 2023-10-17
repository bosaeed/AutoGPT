from typing import List

from ..registry import ability


@ability(
    name="list_files",
    description="List files in a directory use to know name of avaliable files",
    parameters=[
        {
            "name": "path",
            "description": "Path to the directory ,use '/' for current directory",
            "type": "string",
            "required": True,
        }
    ],
    output_type="list[str]",
)
async def list_files(agent, task_id: str, path: str) -> List[str]:
    """
    List files in a workspace directory
    """
    try:
        output = agent.workspace.list(task_id=task_id, path=path)
    except Exception as e:
        return "file or directory not exist"

    return "avaliable files: " + (" , ".join(str(element) for element in output))


@ability(
    name="write_file",
    description="create file and Write data to it",
    parameters=[
        {
            "name": "file_path",
            "description": "Path to the file",
            "type": "string",
            "required": True,
        },
        {
            "name": "data",
            "description": "Data to write to the file",
            "type": "string",
            "required": True,
        },
        # {
        #     "name": "is_last_step",
        #     "description": "true if it last step or false if not",
        #     "type": "string",
        #     "enum": ["True", "False"],
        #     "required": True,
        # },
    ],
    output_type="None",
)
async def write_file(agent, task_id: str, file_path: str, data: bytes ) -> str:
    """
    Write data to a file
    """
    if isinstance(data, str):
        data = data.encode()

    agent.workspace.write(task_id=task_id, path=file_path, data=data)
    await agent.db.create_artifact(
        task_id=task_id,
        file_name=file_path.split("/")[-1],
        relative_path=file_path,
        agent_created=True,
    )

    return f"writing to file done successfully"


@ability(
    name="read_file",
    description="Read data from a file",
    parameters=[
        {
            "name": "file_path",
            "description": "Path to the file (should be provided real file provided by user or get from list_file function)",
            "type": "string",
            "required": True,
        },
        # {
        #     "name": "is_last_step",
        #     "description": "true if it last step or false if not",
        #     "type": "string",
        #     "enum": ["True", "False"],
        #     "required": True,
        # },
    ],
    output_type="bytes",
)
async def read_file(agent, task_id: str, file_path: str  ) -> bytes:
    """
    Read data from a file
    """
    try:
        output = agent.workspace.read(task_id=task_id, path=file_path).decode()
    except Exception as e:
        output = "File Not found may need create one first"
    return output
