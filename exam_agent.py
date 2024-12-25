from typing import TypedDict,List,Dict
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from termcolor import colored
from langgraph.graph import StateGraph, END
import yaml
from rich.console import Console
from rich.markdown import Markdown

def create_exam_graph(model):
    class ExamState(TypedDict):
        messages:List[BaseMessage]
        knowledge_framework:str
        questions:List[Dict[str,str]]
        exam_content:str
    
    def generate_node(state:ExamState):
        print(colored(f"好的,接下来我将为您出一份考试试卷。该试卷总分为100分,其中选择题10分,填空题10分,判断题20分,编程题60分。",'yellow'))
        print(colored(f"根据您提供的知识框架,请问考试范围要考到具体的哪一章节呢?",'blue'))

        with open("prompts.yaml",'r',encoding='utf-8') as f:
            exam_prompt=yaml.safe_load(f)["exam_prompt"].format(knowledge_framework=state["knowledge_framework"])
        
        console=Console()
        prompt=ChatPromptTemplate.from_messages([
            ("system",exam_prompt),
            ("human", "根据我提供的知识框架，针对{exam_range}之前的所有知识为我出一份考试试卷。")
        ])
        messages = prompt.format_messages(
            exam_range=input()
        )
        state["messages"].append(messages)
        with console.status("[bold green]稍等，正在为您出题...") as status:
            result=model.invoke(messages)
            state["messages"].append(result)
            state["questions"]=result.content
            with open("prompts.yaml",'r',encoding='utf-8') as f:
                exam_generate_prompt=yaml.safe_load(f)["exam_generate_prompt"]
            prompt=ChatPromptTemplate.from_messages([
                ("system",exam_generate_prompt),
                ("human","将以下内容:{exam_content}转换为考试试题的格式。")
                ])
            messages = prompt.format_messages(
                exam_content=state["questions"]
            )
            result=model.invoke(messages)
        print(colored(f"我为您出的考试题目如下:",'yellow'))
        console=Console()
        console.print(Markdown(result.content))
        state["exam_content"]=result.content
        return state
    
    def check_node(state:ExamState):

        with open("prompts.yaml",'r',encoding='utf-8') as f:
            check_exam_prompt=yaml.safe_load(f)["check_exam_prompt"].format(exam_content=state["exam_content"])
        
        prompt=ChatPromptTemplate.from_messages([
        ("system",check_exam_prompt),
        ("human", "请批改与分析我对这次考试的作答情况。我的作答如下：{answer_condition}")
    ])
        print(colored(f"请给出您对本试卷的作答:",'blue'))
        messages = prompt.format_messages(answer_condition=input())
        state["messages"].append(messages)
        # content = ""
        # result_content = ""
        # for chunk in model.stream(messages):
        #     content += chunk.content
        #     result_content += chunk.content
        #     if "\n" in chunk.content:
        #         lines = content.split("\n")
        #         content = lines[-1]  
        #         for line in lines[:-1]:  
        #             print(line)
        # if content:  
        #     print(content)
        # display(Markdown(result_content))
        console=Console()
        with console.status("[bold green]稍等，正在为您批改...") as status:
            result=model.invoke(messages)
        console=Console()
        console.print(Markdown(result.content))
        
        return state
    
    # def option_node(state:ExerciseState):
    #     return state
    
    # def options(state:ExerciseState):
    #     try:
    #         json.loads(state["questions"].strip('`json\n'))
    #     except:
    #         return "END"
    #     print(colored(f"请问您还要再做一组练习题吗?请输入Y(是)或N(否)",'blue'))
    #     option=input()
    #     if option=='Y':
    #         return "generate_node"
    #     else:
    #         return "END"
    
    # graph=StateGraph(ExerciseState)
    # graph.add_node("generate_node",generate_node)
    # graph.add_node("check_node",check_node)
    # graph.add_node("option_node",option_node)
    # graph.set_entry_point("generate_node")
    # graph.add_edge("generate_node","check_node")
    # graph.add_edge("check_node","option_node")
    # graph.add_conditional_edges(
    #     "option_node",
    #     options,
    #     {
    #         "generate_node":"generate_node",
    #         "END":END
    #     }
    # )
    # # graph.set_entry_point("generate_node")
    # # graph.add_edge("generate_node",END)
    # return graph.compile()

    graph=StateGraph(ExamState)
    graph.add_node("generate_node",generate_node)
    graph.add_node("check_node",check_node)
    graph.set_entry_point("generate_node")
    graph.add_edge("generate_node","check_node")
    graph.add_edge("check_node",END)
    return graph.compile()