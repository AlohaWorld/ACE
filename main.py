from user_admin_agent import create_user_admin_graph
from summary_agent import create_summary_graph
from typing import TypedDict,List
from langgraph.graph import StateGraph, END
from summary_agent import create_summary_graph
import os
import yaml
from langchain_community.chat_models import QianfanChatEndpoint
import sqlite3
from termcolor import colored
from langchain_core.prompts import ChatPromptTemplate
from study_agent import create_study_graph
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import BaseMessage,SystemMessage,HumanMessage,AIMessage
from exercise_agent import create_exercise_graph
from exam_agent import create_exam_graph
from dotenv import load_dotenv

# os.environ["QIANFAN_AK"] = "OP2OTkM9vNkKIalYD6Hy5BlY"
# os.environ["QIANFAN_SK"] = "CujrLd4CQHMaSjePxCPcgAl1h9pfivCD"

# model=QianfanChatEndpoint()

load_dotenv()
os.environ["DASHSCOPE_API_KEY"] = os.getenv("DASHSCOPE_API_KEY")
model=ChatTongyi(model_name="qwen-plus")

class State(TypedDict):
    message:List[BaseMessage]
    knowledge_framework:str
    stuID:str
    learn_process:str

def user_admin_node(state:State):
    user_admin_graph=create_user_admin_graph()
    result=user_admin_graph.invoke({})
    if result["message_history"]:
        state["message"]=eval(result["message_history"])
    else:
        state["message"]=[]
    state["knowledge_framework"]=result["knowledge_framework"]
    state["stuID"]=result["stuID"]
    state["learn_process"]=result["learn_process"]
    return state

def summary_node(state:State):
    summary_graph=create_summary_graph(model)
    summary=summary_graph.invoke({
        "messages":state["message"],
        "source_file_path":None,
        "knowledge_framework":state["knowledge_framework"],
    })
    state["message"]=summary["messages"]
    state["knowledge_framework"]=summary["knowledge_framework"]
    return state

def end_node(state:State):
    conn = sqlite3.connect('study_agent_info.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET message_history=?,knowledge_framework=?,learn_process=? WHERE stuID=?",
                   (str(state["message"]),state["knowledge_framework"],state["learn_process"],state["stuID"]))
    conn.commit()
    cursor.close()
    conn.close()

def has_message(state:State):
    if state["message"] and state["knowledge_framework"]:
        return "has message"
    else:
        print(colored("你还没有提供给我过想要学习的课程的知识框架,请给我提供知识框架,让我能够更好地帮助你","yellow"))
        return "no message"
    
def options_node(state:State):
    return state
    
def options(state:State):
    print(colored('''您接下来想做什么？是想继续学习课程的知识点,还是想要做几道练习题巩固一下对已学习过的知识点的理解,还是想要向我提问,或者是暂时退出学习呢？
                  您也可以快捷输入"1"继续学习,输入"2"做练习题,输入"3"提问,输入"4"进行考试,输入"5"退出学习。''', "blue"))
    
    with open("prompts.yaml",'r',encoding='utf-8') as f:
        option_prompt=yaml.safe_load(f)["option_prompt"]

    user_input=input()
    prompt=ChatPromptTemplate.from_messages([
            ("system", option_prompt),
            ("human", "{user_input}")
        ])
    messages=prompt.format_messages(
        user_input=user_input
    )
    result=model.invoke(messages).content
    if result=="1":
        return "continue learning"
    elif result=="2":
        return "do exercises"
    elif result=="3":
        return "ask questions"
    elif result=="4":
        return "exam"
    elif result=="5":
        return "__END__"
    
def answer_questions(state:State):

    with open("prompts.yaml",'r',encoding='utf-8') as f:
        study_prompt=yaml.safe_load(f)["study_prompt"].format(knowledge_framework=state["knowledge_framework"])

    prompt=ChatPromptTemplate.from_messages([
        ("system",study_prompt),
        ("human","{question}",)
    ])
    print(colored("您的问题是什么？","blue"))
    user_input=input()
    messages=prompt.format_messages(
    question=user_input,
    )
    result=model.invoke(messages)
    print(result.content)
    state["message"].append(result)
    return state

def study_node(state:State):
    study_graph=create_study_graph(model)
    result=study_graph.invoke({
        "messages":state["message"],
        "learn_process":state["learn_process"],
        "knowledge_framework":state["knowledge_framework"],
    })
    state["message"]=result["messages"]
    state["learn_process"]=result["learn_process"]
    return state

def exercise_node(state:State):
    exercise_graph=create_exercise_graph(model)
    result=exercise_graph.invoke({
        "messages":state["message"],
        "learn_process":state["learn_process"],
        "knowledge_framework":state["knowledge_framework"],
        "questions":[]
    })
    return state

def exam_node(state:State):
    exam_graph=create_exam_graph(model)
    result=exam_graph.invoke({
        "messages":state["message"],
        "knowledge_framework":state["knowledge_framework"],
        "questions":[],
        "exam_content":""
    })
    return state

graph=StateGraph(State)
graph.add_node("user_admin",user_admin_node)
graph.add_node("summary",summary_node)
graph.add_node("study_node",study_node)
graph.add_node("option_node",options_node)
graph.add_node("exercise_node",exercise_node)
graph.add_node("exam_node",exam_node)
graph.set_entry_point("user_admin")
graph.add_node("end_node",end_node)
graph.add_node("answer_node",answer_questions)
graph.add_edge("summary","option_node")
graph.add_conditional_edges(
    "user_admin",
    has_message,
    {
        "has message":"option_node",
        "no message":"summary"
    }
)
graph.add_conditional_edges(
    "option_node",
    options,
    {
        "continue learning":"study_node",
        "do exercises":"exercise_node",
        "ask questions":"answer_node",
        "exam":"exam_node",
        "__END__":"end_node"
    }
)
graph.add_edge("study_node","option_node")
graph.add_edge("answer_node","option_node")
graph.add_edge("exercise_node","option_node")
graph.add_edge("exam_node","option_node")
graph.add_edge("end_node",END)
app=graph.compile()

app.invoke({"message":None,"knowledge_framework":None,"stuID":None})

