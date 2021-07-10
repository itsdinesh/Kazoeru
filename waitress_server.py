from waitress import serve
import app2
print("Waitress WSGI Server is running!")
serve(app2.app, channel_timeout=4000, host='0.0.0.0', port=8080)

