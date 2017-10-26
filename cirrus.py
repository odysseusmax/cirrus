import datetime
import os

from flask import Flask, request, redirect
from flask.ctx import after_this_request
from flask.helpers import send_file, flash, url_for
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = '/tmp/uploads'
FORBIDDEN_EXTENSIONS = ('html', 'php')

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = str(datetime.datetime.now())
# app.config['MAX_CONTENT_LENGTH'] = 256 * 1024 ** 2


def create_dir(upload_directory):
    if not os.path.exists(upload_directory):
        try:
            os.mkdir(upload_directory)
        except Exception as e:
            app.logger.critical('Could not create an upload directory', e)
            exit(1)
    elif not os.path.isdir(upload_directory):
        app.logger.critical('Could not create an upload directory. File exists')
        exit(1)


def allowed_file(filename):
    return os.path.splitext(filename)[1].lower() not in FORBIDDEN_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            # flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            flash('File uploaded as {}'.format(filename))

    return '''
    <html>
      <head>
        <title> Upload new file</title>
      </head>
      <body>
        <h1>upload new file</h1>
        <form method=POST enctype=multipart/form-data>
          <p><input type=file name=file>
            <input type=submit value=Upload>
        </form>
      </body>
    </html>
    '''


@app.route('/uploads/<filename>')
def download_file(filename):
    filename = secure_filename(filename)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    remove_file_after = True

    @after_this_request
    def remove_file(response):
        if remove_file_after:
            try:
                os.remove(file_path)
            except Exception as ex:
                app.logger.error("Error removing file from server", ex)
        return response

    try:
        return send_file(file_path)
    except (PermissionError, IOError) as e:
        remove_file_after = False
        app.logger.error('Error while downloading a file', e)
        flash('Error while downloading {}. File does not exist'.format(filename))
        return redirect(url_for('upload_file'))


if __name__ == '__main__':
    create_dir(UPLOAD_FOLDER)
    app.run()
