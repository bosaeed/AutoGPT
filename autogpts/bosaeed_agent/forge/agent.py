import json
import pprint
import os

from forge.sdk import (
    Agent,
    AgentDB,
    Step,
    StepRequestBody,
    Workspace,
    ForgeLogger,
    Task,
    TaskRequestBody,
    PromptEngine,
    chat_completion_request,
    ChromaMemStore
)

# from forge.sdk.abilities import Planner

LOG = ForgeLogger(__name__)

# MODEL = "gpt-3.5-turbo"
MAX_STEPS = 4

class ForgeAgent(Agent):
    """
    The goal of the Forge is to take care of the boilerplate code, so you can focus on
    agent design.

    There is a great paper surveying the agent landscape: https://arxiv.org/abs/2308.11432
    Which I would highly recommend reading as it will help you understand the possabilities.

    Here is a summary of the key components of an agent:

    Anatomy of an agent:
         - Profile
         - Memory
         - Planning
         - Action

    Profile:

    Agents typically perform a task by assuming specific roles. For example, a teacher,
    a coder, a planner etc. In using the profile in the llm prompt it has been shown to
    improve the quality of the output. https://arxiv.org/abs/2305.14688

    Additionally, based on the profile selected, the agent could be configured to use a
    different llm. The possibilities are endless and the profile can be selected
    dynamically based on the task at hand.

    Memory:

    Memory is critical for the agent to accumulate experiences, self-evolve, and behave
    in a more consistent, reasonable, and effective manner. There are many approaches to
    memory. However, some thoughts: there is long term and short term or working memory.
    You may want different approaches for each. There has also been work exploring the
    idea of memory reflection, which is the ability to assess its memories and re-evaluate
    them. For example, condensing short term memories into long term memories.

    Planning:

    When humans face a complex task, they first break it down into simple subtasks and then
    solve each subtask one by one. The planning module empowers LLM-based agents with the ability
    to think and plan for solving complex tasks, which makes the agent more comprehensive,
    powerful, and reliable. The two key methods to consider are: Planning with feedback and planning
    without feedback.

    Action:

    Actions translate the agent's decisions into specific outcomes. For example, if the agent
    decides to write a file, the action would be to write the file. There are many approaches you
    could implement actions.

    The Forge has a basic module for each of these areas. However, you are free to implement your own.
    This is just a starting point.
    """

    def __init__(self, database: AgentDB, workspace: Workspace):
        """
        The database is used to store tasks, steps and artifact metadata. The workspace is used to
        store artifacts. The workspace is a directory on the file system.

        Feel free to create subclasses of the database and workspace to implement your own storage
        """
        

        self.debug = False
        # self.planner = Planner()
        super().__init__(database, workspace)

    async def create_task(self, task_request: TaskRequestBody) -> Task:
        """
        The agent protocol, which is the core of the Forge, works by creating a task and then
        executing steps for that task. This method is called when the agent is asked to create
        a task.

        We are hooking into function to add a custom log message. Though you can do anything you
        want here.
        """
        # self.chat_history = []
        # self.plan_history = []
        # self.previous_actions = []
        self.current_steps_num = 0
        self.is_last_step = False
        self.plan = ""
        task = await super().create_task(task_request)
        LOG.info(
            f"📦 Task created: {task.task_id} input: {task.input[:40]}{'...' if len(task.input) > 40 else ''}"
        )
        # self.planner.create_task(self ,task , task.input )

        return task

    async def execute_step(self, task_id: str, step_request: StepRequestBody) -> Step:
        """
        For a tutorial on how to add your own logic please see the offical tutorial series:
        https://aiedge.medium.com/autogpt-forge-e3de53cc58ec

        The agent protocol, which is the core of the Forge, works by creating a task and then
        executing steps for that task. This method is called when the agent is asked to execute
        a step.

        The task that is created contains an input string, for the benchmarks this is the task
        the agent has been asked to solve and additional input, which is a dictionary and
        could contain anything.

        If you want to get the task use:

        ```
        task = await self.db.get_task(task_id)
        ```

        The step request body is essentially the same as the task request and contains an input
        string, for the benchmarks this is the task the agent has been asked to solve and
        additional input, which is a dictionary and could contain anything.

        You need to implement logic that will take in this step input and output the completed step
        as a step object. You can do everything in a single step or you can break it down into
        multiple steps. Returning a request to continue in the step output, the user can then decide
        if they want the agent to continue or not.
        """
        # An example that
        self.is_last_step = False
        self.current_steps_num += 1 
        task = await self.db.get_task(task_id)

        step = await self.db.create_step(
            task_id=task_id, input=step_request, is_last=False
        )
        LOG.info(pprint.pformat(step_request))

        try:
            files = self.workspace.list(task_id=task.task_id, path="/")
        except:
            files=[]


        if self.current_steps_num < 2:
            self.task_prompt_args = {
                "constraints":[],
                "best_practices":[],
                "resources":[],
                "avaliable_files":files,
            }
            LOG.info( f"************Planning*************")
            # await self.plan_gpt(task)
            self.plan = await self.plan_gpt(task)
            LOG.info( f"{self.plan}")
            # self.plan = await self.planner.update_plan(self,task , self.chat_history)
            LOG.info( f"****************************************")
            # LOG.info( f"{self.plan}")
            output = self.plan
            # await self.db.create_artifact(
            #     task_id=task_id,
            #     file_name=file_path.split("/")[-1],
            #     relative_path=file_path,
            #     agent_created=True,
            # ) 

        else:
            output = ""
            output = await self.ask_gpt(task,used_functions=self.abilities.list_non_planning_abilities_names() , plan=self.plan)


        if self.current_steps_num > MAX_STEPS :
            self.is_last_step = True

        step.is_last = self.is_last_step
        step.output = output

        if self.is_last_step:
            LOG.info(f"\t✅ Final Step num {self.current_steps_num} completed: {step.step_id}")
        else:
            LOG.info(f"\t✅Step num {self.current_steps_num} completed: {step.step_id}")
        

        return step

    def get_functions(self, abilities: dict , use_only:list = None) -> list:
        functions = []
        for ability in abilities:
            if(use_only != None and ability.name not in use_only):
                continue

            # abi = {
            #     'name': ability.name,
            #     'description': ability.description,
            #     'parameters': {
            #         'type': 'object',
            #         'properties': { 
            #         },
            #         'required':[]
            #     }
            # }

            abi = f"# {ability.name}: {ability.description}\n  ## arguments: \n"

            for par in ability.parameters:
                # abi['parameters']['properties'][par.name] = {}
                # abi['parameters']['properties'][par.name]['type'] = par.type
                # abi['parameters']['properties'][par.name]['description'] = par.description
                # if(par.required):
                #     abi['parameters']['required'].append(par.name)
                abi += f"  * {par.name}: {par.description}, type: {par.type}\n"

           
            functions.append(str(abi))        

        return functions

    def str2bool(self,v):
        if(not v):
            return False
        if(type(v)== type(True)):
            return v

        return v.lower() in ("yes", "true", "t", "1" , "finish")

    async def ask_gpt(self , task , used_functions = None , function_call = "auto" , plan = None):

        model =  os.getenv('SMART_LLM', "gpt-3.5-turbo")
        self.prompt_engine = PromptEngine("gpt-3.5-turbo" , self.debug)
        system_prompt = self.prompt_engine.load_prompt("system-format-2")


        p_actions = await self.db.get_previous_action_history(task.task_id)
        # LOG.info(pprint.pformat(p_actions))
        # Specifying the task parameters
        task_kwargs = {
            "task": task.input,
            # "abilities": self.abilities.list_non_planning_abilities_names(),
            "abilities": self.get_functions(self.abilities.list_abilities().values() , used_functions),
            "plan":plan,
            "previous_actions":p_actions,
            **self.task_prompt_args,
            
        }
        # LOG.info(pprint.pformat(task_kwargs))
        # Then, load the task prompt with the designated parameters
        task_prompt = self.prompt_engine.load_prompt("task-step-by-plan", **task_kwargs)
        #messages list:
        messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task_prompt}
                ]
      
        try:
            # for msg in self.chat_history:
            #     messages.append(msg)

            messages.extend(await self.db.get_chat_history(task.task_id))
            # for msg in self.plan_history:
            #     messages.append(msg)
            # Define the parameters for the chat completion request
            chat_completion_kwargs = {
                "messages": messages,
                "model": model,
                # "functions":functions,
                # "function_call": function_call,
            }
            # Make the chat completion request and parse the response
            LOG.info(pprint.pformat(chat_completion_kwargs))
            chat_response = await chat_completion_request(**chat_completion_kwargs)

            LOG.info(pprint.pformat(chat_response))
            if (chat_response["choices"][0]["message"].get("content")):
                content = json.loads(chat_response["choices"][0]["message"]["content"])

                if content.get("thoughts"):
                    self.chat_history.append({"role":"assistant" , "content" : str(content["thoughts"])})

                    await self.db.add_chat_message(task.task_id , "assistant" , str(content["thoughts"]))
                    output = str(content["thoughts"])
            # if (chat_response["choices"][0]["message"].get("function_call")):
                if content.get("ability"):
                    ability = content["ability"]
                    # ability["arguments"] = json.loads(ability["arguments"])
                    output = await self.abilities.run_ability(
                        task.task_id, ability["name"], **ability["arguments"]
                    )

                    function_kwargs = {
                        "name": ability['name'],
                        # "args": str(ability["arguments"]),
                        "output": output,
                    }

                    # Then, load the task prompt with the designated parameters
                    function_prompt = self.prompt_engine.load_prompt("function-output", **function_kwargs)
                    if output:
                        # self.chat_history.append({"role":"assistant" , "content" : function_prompt})
                        # self.previous_actions.append(function_prompt)

                        await self.db.add_previous_action(task.task_id ,function_prompt )

                    # LOG.info(pprint.pformat(previous_actions))
                    if ability['name'].lower()  == "finish":
                        self.is_last_step = True


                    LOG.info(pprint.pformat(ability))
                if content.get("is_last_step") and self.str2bool(content.get("is_last_step")):
                    self.is_last_step = True
                if content.get("updated_plan") :
                    self.plan = content.get("updated_plan")


                LOG.info(pprint.pformat(output))


        except json.JSONDecodeError as e:
            # Handle JSON decoding errors
            output = f"{e}"
            LOG.error(f"Unable to decode chat response: {chat_response}")

            # self.chat_history.append({"role":"system" , "content" : f"error {e}"})
            await self.db.add_chat_message(task.task_id , "system" ,  f"error {e}")
            
        except Exception as e:
            # Handle other exceptions
            output = f"{type(e).__name__} {e}"
            LOG.error(f"Unable to generate chat response: {type(e).__name__} {e}")
            # self.chat_history.append({"role":"system" , "content" : f"error {e}"})
            await self.db.add_chat_message(task.task_id , "system" ,  f"error {e}")
        return output

    async def plan_gpt(self , task ):

        plan_model = os.getenv('PLANNER_MODEL', "gpt-3.5-turbo")
        self.prompt_engine = PromptEngine("gpt-3.5-turbo" , self.debug)
        system_prompt = self.prompt_engine.load_prompt("system-format-plan-2")


        # Specifying the task parameters
        task_kwargs = {
            "task": task.input,
            # "abilities": self.abilities.list_non_planning_abilities_names(),
            "abilities": self.abilities.list_non_planning_abilities_name_description(),
        
        }

        # Then, load the task prompt with the designated parameters
        task_prompt = self.prompt_engine.load_prompt("user-format-plan", **task_kwargs)
        #messages list:
        messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": task_prompt}
                ]
      

        try:
            # for msg in self.chat_history:
            #     messages.append(msg)
            messages.extend(await self.db.get_chat_history(task.task_id))
            # Define the parameters for the chat completion request
            chat_completion_kwargs = {
                "messages": messages,
                "model": plan_model,
            }
            # Make the chat completion request and parse the response
            LOG.info(pprint.pformat(chat_completion_kwargs))
            chat_response = await chat_completion_request(**chat_completion_kwargs)

            LOG.info(pprint.pformat(chat_response))
            output = ""
            if (chat_response["choices"][0]["message"].get("content")):
                output = chat_response["choices"][0]["message"]["content"]
                # output = json.loads(chat_response["choices"][0]["message"]["content"])

                # output = self.orgnize_plan(output)
                # self.chat_history.append({"role":"assistant" , "content" : output})
                
                LOG.info(pprint.pformat(output))


        except json.JSONDecodeError as e:
            # Handle JSON decoding errors
            output = f"{e}"
            LOG.error(f"Unable to decode chat response: {chat_response}")
            
        except Exception as e:
            # Handle other exceptions
            if (type(e).__name__ == KeyError):
                output = f"{e}"
            else:
                output = f"{type(e).__name__} {e}"
            LOG.error(f"Unable to generate chat response: {output}")

        return output

    def orgnize_plan(self , thoughts):
        output = ""

        output += f"thoughts: {thoughts['thoughts']}"
        output += f"reasoning: {thoughts['reasoning']}"
        output += f"plan: {thoughts['plan']}"
        output += f"criticism: {thoughts['criticism']}"

        return output