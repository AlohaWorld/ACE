from typing import TypedDict,List,Dict
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from termcolor import colored
from langgraph.graph import StateGraph, END
import json
import yaml
from rich.console import Console
from rich.markdown import Markdown

def create_exercise_graph(model):
    class ExerciseState(TypedDict):
        messages:List[BaseMessage]
        knowledge_framework:str
        learn_process:str
        questions:List[Dict[str,str]]
    
    def generate_node(state:ExerciseState):
        print(colored(f"好的,接下来我将为您出一系列的练习题,您可以进行作答,我会为您进行批改。每4道题为一组。",'yellow'))
        # print(colored(f"请问您需要针对哪部分的知识点进行练习呢?",'blue'))

        with open("prompts.yaml",'r',encoding='utf-8') as f:
            exercise_prompt=yaml.safe_load(f)["exercise_prompt"].format(knowledge_framework=state["knowledge_framework"],
                                                                        history_questions=state["questions"])
        
        console=Console()
        prompt=ChatPromptTemplate.from_messages([
            ("system",exercise_prompt),
            # ("human", "我想要练习的知识点：{learn_point}。请你为我生成一些作业与练习题目。")
            ("human", "我当前的学习进度是{learn_process},请你为我生成一些作业与练习题目。")
        ])
        messages = prompt.format_messages(
            learn_process=state["learn_process"]
        )
        state["messages"].append(messages)
        with console.status("[bold green]稍等，正在为您出题...") as status:
            result=model.invoke(messages)
        state["messages"].append(result)
        state["questions"]=result.content
        try:
            json.loads(state["questions"].strip('`json\n'))
        except:
            print(state["questions"])
        return state
    
    def check_node(state:ExerciseState):
        try:
            questions=json.loads(state["questions"].strip('`json\n'))
        except:
            return state
        for i in range(len(questions)):
            print(colored(f"当前为第{i+1}题:",'yellow'))
            print(colored(f"题目为：{questions[i]['content']}",'yellow'))
            print(colored(f"请问您的作答是什么？",'blue'))
            answer=input()
            with open("prompts.yaml",'r',encoding='utf-8') as f:
                check_prompt=yaml.safe_load(f)["check_prompt"].format(question=questions[i]["content"],
                                                                      knowledge_framework=state["knowledge_framework"])
            prompt=ChatPromptTemplate.from_messages([
                ("system",check_prompt),
                ("human", "对于这道题目，我的作答是：{answer}。请为我批改。")
            ])
            messages = prompt.format_messages(
                answer=answer,
            )
            state["messages"].append(messages)
            content = ""
            result_content = ""
            for chunk in model.stream(messages):
                content += chunk.content
                result_content += chunk.content
                if "\n" in chunk.content:
                    lines = content.split("\n")
                    content = lines[-1]  
                    for line in lines[:-1]:  
                        print(line)
            if content:  
                print(content)
            # display(Markdown(result_content))
            console=Console()
            markdown=Markdown(result_content)
            console.print(markdown)
            questions[i]["answer"]=answer

        with open("prompts.yaml",'r',encoding='utf-8') as f:
            evaluate_answer_prompt=yaml.safe_load(f)["evaluate_answer_prompt"]
        
        prompt=ChatPromptTemplate.from_messages([
        ("system",evaluate_answer_prompt),
        ("human", "请评估与分析我对这些题目的作答情况。题目以及我的作答情况如下：{answer_condition}")
    ])
        messages = prompt.format_messages(answer_condition=questions)
        state["messages"].append(messages)
        content = ""
        result_content = ""
        for chunk in model.stream(messages):
            content += chunk.content
            result_content += chunk.content
            if "\n" in chunk.content:
                lines = content.split("\n")
                content = lines[-1]  
                for line in lines[:-1]:  
                    print(line)
        if content:  
            print(content)
        # display(Markdown(result_content))
        console.print(Markdown(result_content))
        
        return state
    
    def option_node(state:ExerciseState):
        return state
    
    def options(state:ExerciseState):
        try:
            json.loads(state["questions"].strip('`json\n'))
        except:
            return "END"
        print(colored(f"请问您还要再做一组练习题吗?请输入Y(是)或N(否)",'blue'))
        option=input()
        if option=='Y':
            return "generate_node"
        else:
            return "END"
    
    graph=StateGraph(ExerciseState)
    graph.add_node("generate_node",generate_node)
    graph.add_node("check_node",check_node)
    graph.add_node("option_node",option_node)
    graph.set_entry_point("generate_node")
    graph.add_edge("generate_node","check_node")
    graph.add_edge("check_node","option_node")
    graph.add_conditional_edges(
        "option_node",
        options,
        {
            "generate_node":"generate_node",
            "END":END
        }
    )
    # graph.add_edge("check_node",END)
    # graph.add_edge("generate_node",END)
    return graph.compile()