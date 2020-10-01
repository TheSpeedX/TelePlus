import json
import os
from quart import Quart, render_template, request, jsonify, make_response,redirect,url_for,session
from TelegramClient import ClientStore,TelegramClient
from datetime import datetime

app = Quart(__name__)

SETTINGS = json.load(open("settings.json"))

client_store = ClientStore()

for config in json.load(open(SETTINGS.get("config_path"))):
    client_store.add(TelegramClient(**config))

def save_config():
    with open(SETTINGS.get("config_path"),"w") as config_file:
        json.dump(client_store.toconfig(),config_file,indent=4)

def build_phone_path(phone):
    return os.path.join("data","phone",phone+".json")

def build_group_path(group):
    return os.path.join("data","phone",group+".json")


@app.before_first_request
async def before_first_request_func():
    session["config"]=client_store.toconfig()
    if session["config"]:
        session["current"] = session.get("config")[0]
        session["phone"]= json.load(open(build_phone_path(session["current"]["phone"])))

@app.route('/')
async def home():
    # print("CONFIG: ",client_store.toconfig())
    print("Home Request: ",client_store)
    if len(session["config"])==0:
        return await render_template("default.html",type="guest",info=session["phone"])
    else:
        if session["phone"].get("status"):
            return await render_template("default.html",type="active",info=session["phone"])
        else:
            return await render_template("default.html",type="inactive",info=session["phone"])
    

@app.route('/adduser',methods=["GET","POST"])
async def login():
    if request.method=="GET":
        return await render_template("login.html")
    else:
        data=await request.get_json()
        # print("DATA: ",data)
        if client_store.get(phone=data["phone"]):
            return {"success":False,"ask_code":False,"message":"Account Already Exists"}
        new_client = TelegramClient(data["api_id"],data["api_hash"],data["phone"])
        print("NEW Session: ",new_client)
        if data.get("code"):
            flag=await new_client.auth(code=data["code"],phone_code=session["phone_code_hash"])
        else:
            flag=await new_client.auth()
        if flag==True:
            with open(build_phone_path(new_client.phone),"w") as acc_config:
                json.dump(dict(status=False,attached_name="",count=0,total=0,current_user="",group="",timestamp=datetime.now().timestamp()),acc_config,indent=4)
            client_store.add(new_client)
            session["config"]=client_store.toconfig()
            await change_number(data["api_id"])
            save_config()
            return {"success":True}
        elif flag==None:
            return {"success":False,"ask_code":False,"message":"Invalid API ID/API HASH "}
        else:
            session["phone_code_hash"]=flag.phone_code_hash
            return {"success":False,"ask_code":True,"message":"Enter Code"}

@app.route('/logout')
async def logout():
    client_store.pop(client_store.get_index(api_id=session["current"]["api_id"]))
    session["config"]=client_store.toconfig()
    save_config()
    if session["config"]:
        session["current"] = session.get("config")[0]
        session["phone"]= json.load(open(build_phone_path(session["current"]["phone"])))
    return redirect("/")
    
    
@app.route('/change/<api_id>')
async def change_number(api_id):
    session["current"] = client_store.get(api_id=api_id).todict()
    session["phone"]= json.load(open(build_phone_path(session["current"]["phone"])))
    return session["current"]

if __name__ == '__main__':
    app.secret_key = "MySecretKey1234"
    app.run(host="0.0.0.0",port=SETTINGS.get("port",5000),debug=True)