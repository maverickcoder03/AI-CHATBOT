from flask import Flask, render_template, request, jsonify
from chatbot import get_response
from database import init_db, save_chat

app=Flask(__name__)
init_db()

@app.route("/")
def home():
    return render_template("index.html")

@app.post("/chat")
def chat():
    data=request.get_json()
    msg=data.get("message","").strip()
    reply=get_response(msg)
    save_chat(msg,reply)
    return jsonify({"reply":reply})

if __name__=="__main__":
    app.run(debug=True)
