from flask import Flask, render_template, Response, jsonify
from people_counter import Camera

app = Flask(__name__)


def gen(camera):
    """Video streaming generator function."""
    while True:
        frame = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/')
def test_feed():
    return render_template('video.html')


@app.route('/video_feed', methods=['GET'])
def video_feed():
    """Video streaming route. Put this in the src attribute of an img tag."""
    return Response(gen(Camera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/crowd-data', methods=['GET'])
def crowd_data():
    status = Camera.get_crowd_count()

    return jsonify(
        crowd_count=status[0],
        crowd_status=status[1],
        train_status=status[2]
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0')
