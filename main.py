
import app
import json
import sys

def main():
    SETTINGS = json.load(open("settings.json"))
    if len(sys.argv)>1 and "public" in sys.argv[1]:
        from pyngrok import ngrok
        ngrok.set_auth_token(SETTINGS.get("auth_token"))
        url = ngrok.connect(SETTINGS.get("port",5000),"http")
        print("PUBLIC URL: ",url)
    app.main()

if __name__ == '__main__':
    main()
