from waitress import serve
import app
print("Waitress WSGI Server is running!")
serve(app.application, channel_timeout=4000, host='0.0.0.0', port=8080, threads=6)

