import sqlite3
DB="database/chatbot.db"

def init_db():
    con=sqlite3.connect(DB)
    cur=con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS chats(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_message TEXT,
        bot_reply TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    con.commit();con.close()

def save_chat(user,bot):
    con=sqlite3.connect(DB)
    cur=con.cursor()
    cur.execute("INSERT INTO chats(user_message,bot_reply) VALUES(?,?)",(user,bot))
    con.commit();con.close()
