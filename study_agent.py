from typing import TypedDict,List
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from termcolor import colored
from langgraph.graph import StateGraph, END
from rich.markdown import Markdown
from rich.console import Console
import yaml

def create_study_graph(model):
    class StudyState(TypedDict):
        messages:List[BaseMessage]
        knowledge_framework:str
        learn_process:str

    def review_node(state:StudyState):
        with open("prompts.yaml",'r',encoding='utf-8') as f:
            review_prompt=yaml.safe_load(f)["review_prompt"]
        
        prompt=ChatPromptTemplate.from_messages([
            ("system",review_prompt),
            ("human", "我目前的学习进度：{learn_process}。请你为我复习所学习过的知识点。")
        ]) 

        messages = prompt.format_messages(
            learn_process=state["learn_process"],
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
        console.print(Markdown(result_content))

    def learn_node(state:StudyState):
        
        with open("prompts.yaml",'r',encoding='utf-8') as f:
            study_prompt=yaml.safe_load(f)["study_prompt"].format(knowledge_framework=state["knowledge_framework"])

        with open("prompts.yaml",'r',encoding='utf-8') as f:
            next_section_prompt=yaml.safe_load(f)["next_section_prompt"].format(knowledge_framework=state["knowledge_framework"])
        
        prompt=ChatPromptTemplate.from_messages([
            ("system",study_prompt),
            ("human", "我目前的学习进度：{learn_process}。请你为我讲解下一个知识点。")
        ])

        messages = prompt.format_messages(
            learn_process=state["learn_process"],
        )
        state["messages"].append(messages)
        # result=model.invoke(messages)
        # print(result.content)
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
        console.print(Markdown(result_content))

        prompt=ChatPromptTemplate.from_messages([
            ("system", next_section_prompt),
            ("human", "{current_process}在知识框架中的下一章节是什么？")
        ])
        messages=prompt.format_messages(
            current_process=state["learn_process"]
        )
        result=model.invoke(messages)
        state["learn_process"]=result.content
        return state
    
    def answer_questions(state:StudyState):

        with open("prompts.yaml",'r',encoding='utf-8') as f:
            study_answer_prompt=yaml.safe_load(f)["study_answer_prompt"].format(knowledge_framework=state["knowledge_framework"])

        prompt=ChatPromptTemplate.from_messages([
            ("system",study_answer_prompt),
            ("human","{question}")
        ])
        print(colored("您的问题是什么？","blue"))
        user_input=input()
        messages=prompt.format_messages(
        question=user_input
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
        console=Console()
        console.print(Markdown(result_content))
        return state

    def study_router(state:StudyState):
        print(colored("针对以上的讲解内容,你是否有疑问?请输入Y(是)或N(否):","blue"))
        user_input=input()
        if user_input=="Y":
            return "answer questions" 
        else:
            return "no question"
        
    def router_node(state:StudyState):
        return state
    
    def router(state:StudyState):
        if state["learn_process"]=="已经学习完了所有的知识点":
            return "__END__"
        else:
            print(colored(f"您还要继续学习下一个知识点吗?输入Y(是)或N(否):","blue"))
            user_input=input()
            if user_input=="Y":
                return "continue learn"
            else:
                return "__END__"
    
    graph=StateGraph(StudyState)
    graph.add_node("review_node",review_node)
    graph.add_node("learn_node",learn_node)
    graph.add_node("answer_node",answer_questions)
    graph.add_node("router_node",router_node)
    graph.add_edge("review_node","learn_node")
    graph.add_conditional_edges(
        "learn_node",
        study_router,
        {
            "answer questions":"answer_node",
            "no question":"router_node"
        }
    )
    graph.add_conditional_edges(
        "router_node",
        router,
        {
            "continue learn":"learn_node",
            "__END__":END
        }
    )
    graph.add_edge("answer_node","router_node")
    graph.set_entry_point("review_node")
    return graph.compile()

