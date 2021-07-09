from waitress import serve
import app
print("Waitress WSGI Server is running!")
serve(app.app, channel_timeout=4000, host='0.0.0.0', port=8080)

