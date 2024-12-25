from termcolor import colored
import sqlite3
from langgraph.graph import END,Graph

def create_user_admin_graph():

    def user_admin(place_holder):
    # 创建/连接数据库
        conn = sqlite3.connect('study_agent_info.db')
        cursor = conn.cursor()

        print(colored('''亲爱的同学你好！我是你的智能学习小助手，很高兴能陪伴你一起学习和进步。
        我可以为你详细讲解知识点、提供针对性的练习题，并对你的答案给出专业的评判和建议。
        请问你的姓名和学号是什么呢？''', "yellow"))

        print(colored("请输入您的姓名：", "blue"))
        user_name=input()
        print(colored("请输入您的学号：", "blue"))
        user_id=input()


        cursor.execute('SELECT * FROM users WHERE stuID= ? AND stuName= ?', (user_id,user_name))
        user_info = cursor.fetchall()

        if user_info:
            print(colored(f"{user_name}同学,你好!欢迎回来继续学习", "yellow"))
            cursor.close()
            conn.close()
            return {"message_history":user_info[0][4] if user_info[0][4] else [],
                    "knowledge_framework":user_info[0][5] if user_info[0][5] else "",
                    "stuID":user_id,
                    "learn_process":user_info[0][6] if user_info[0][6] else "尚未学习任何知识点"}

        else:
            cursor.execute("INSERT INTO users (stuName, stuID) VALUES (?, ?)", 
                        (user_name, user_id))
            conn.commit()
            print(colored(f"{user_name}同学,你好,欢迎你!在接下来的一段时间内,我会陪伴你一起学习,一起进步!",
                        "yellow"))
            cursor.close()
            conn.close()
            return {"message_history":[],
                    "knowledge_framework":"",
                    "stuID":user_id,
                    "learn_process":"尚未学习任何知识点"}
    
    graph=Graph()
    graph.add_node("user_admin",user_admin)
    graph.add_edge("user_admin",END)
    graph.set_entry_point("user_admin")
    return graph.compile()

