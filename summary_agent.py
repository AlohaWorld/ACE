import yaml
from typing import TypedDict,List
from langchain_core.prompts import ChatPromptTemplate
from termcolor import colored
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage
from rich.markdown import Markdown
from rich.console import Console

def create_summary_graph(model,memory=None):
    # 定义状态类型
    class KnowledgeState(TypedDict):
        messages: List[BaseMessage]
        source_file_path: str
        knowledge_framework: str

    # 上传知识文件
    def upload_knowledge_file(state:KnowledgeState):
        print(colored("请输入您的知识文件路径,要求文件格式为YAML格式:","blue"))
        source_file_path=input()
        state["source_file_path"]=source_file_path
        return state

    def dict_to_string(d,indent=0):
        result=""
        for key,value in d.items():
            result+="  "*indent
            if isinstance(value,dict):
                result+=f"{key}:\n{dict_to_string(value,indent+1)}"
            else:
                result+=f"{key}:{value}\n"
        return result

    # 加载知识文件
    def load_knowledge_file(state:KnowledgeState):
        """加载YAML格式的知识文件"""
        try:
            with open(state["source_file_path"],'r',encoding='utf-8') as f:
                knowledge=yaml.safe_load(f)
                state["knowledge_framework"]=dict_to_string(knowledge)
            return state
        except Exception as e:
            state["knowledge_framework"]="Error!"
            return state

    # 知识分析节点
    def knowledge_analysis(state: KnowledgeState):
        """分析知识结构并生成建议"""
        # 定义知识分析提示模板        
        knowledge_prompt = ChatPromptTemplate.from_messages([
                ("system", "{knowledge_analysis_prompt}"),
                ("human", "这是我提供的知识结构:\n{knowledge_content}\n\n")
            ])
        
        with open("prompts.yaml",'r',encoding='utf-8') as f:
            knowledge_analysis_prompt=yaml.safe_load(f)["knowledge_analysis_prompt"]

        # 生成分析结果
        messages = knowledge_prompt.format_messages(
            knowledge_analysis_prompt=knowledge_analysis_prompt,
            knowledge_content=state["knowledge_framework"]
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

        return state

    def is_file_legal(state:KnowledgeState):
        if state["knowledge_framework"]=="Error!":
            print(colored("您提供的知识文件格式不正确,请重新输入","red"))
            return "Illegal"
        return "Legal"

    def is_update(state:KnowledgeState):
        print(colored(f"当前为您梳理的知识结构如下:",'yellow'))
        print(f"{state['knowledge_framework']}")
        print(colored("您还要对当前知识结构进行修改吗?输入Y(是)或N(否):",'blue'))
        update_flag=input()
        if update_flag=="Y":
            return "Update"
        else:
            return "Not Update"
        
    def update(state:KnowledgeState):
        print(colored("请输入您更新后的知识文件路径,要求文件格式为YAML格式:","blue"))
        file_path=input()
        knowledge_framework=""
        try:
            with open(file_path,'r',encoding='utf-8') as f:
                knowledge=yaml.safe_load(f)
                knowledge_framework=dict_to_string(knowledge)
        except Exception as e:
            knowledge_framework="Error!"
        while knowledge_framework=="Error!":
            print(colored("您提供的知识文件格式不正确,请重新输入","red"))
            file_path=input()
            try:
                with open(file_path,'r',encoding='utf-8') as f:
                    knowledge=yaml.safe_load(f)
                    knowledge_framework=dict_to_string(knowledge)
            except Exception as e:
                knowledge_framework="Error!"
        state["knowledge_framework"]=knowledge_framework
        print(colored("更新后的知识结构如下:",'yellow'))
        print(f"{knowledge_framework}")
        return state
    

    knowledge_graph = StateGraph(KnowledgeState)
    knowledge_graph.add_node("upload_knowledge_file", upload_knowledge_file)
    knowledge_graph.add_node("load_knowledge_file", load_knowledge_file)
    knowledge_graph.add_node("knowledge_analysis", knowledge_analysis)
    knowledge_graph.add_node("update", update)
    knowledge_graph.set_entry_point("upload_knowledge_file")
    knowledge_graph.add_edge("upload_knowledge_file","load_knowledge_file")
    knowledge_graph.add_conditional_edges("load_knowledge_file",
                                        is_file_legal,
                                        {"Illegal":"upload_knowledge_file",
                                        "Legal":"knowledge_analysis"})
    knowledge_graph.add_conditional_edges("knowledge_analysis",
                                        is_update,
                                        {"Update":"update",
                                        "Not Update":END})
    knowledge_graph.add_edge("update",END)
    return knowledge_graph.compile(checkpointer=memory)

