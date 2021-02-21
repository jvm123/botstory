"""
(C) 2021 Julian von Mendel <prog@derjulian.net>

app.py
====================================
This is the main program for the Flask chatbot server
"""

import sys
import logging
import uuid
import time

import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property # has to follow directly after import werkzeug
from flask import Flask, session, render_template, make_response #, request
from flask_restx import Resource, Api #, fields

from example.demochatbot import DemoChatBot

logging.basicConfig(level=logging.CRITICAL)

SESSION_TIMEOUT = 7200 # Remove a user session after 2h of inactivity
chatbots = {}
lastactivity = {}

# Flask web interface
def create_app():
    app = Flask(__name__,
            static_url_path='/static',
            static_folder='www_static',
            template_folder='templates')
    app.secret_key = 'e6shg,.?)yysffSE/%fyaydgsgtu575b'

    @app.route("/")
    def index():
        # Load additional data for HTML template from bot storylines
        chatbot = DemoChatBot()
        data = chatbot.get_template_data()

        # Show bot UI
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template('home.html', \
                            **data), 200, headers)


    api = Api(app = app,
            version = "1.0",
            title = "Chatbot server",
            description = "Provide a chatbot interface",
            doc = "/doc")

    name_space_static = api.namespace('static', description='Static files')
    name_space_bot = api.namespace('chatbot', description='Chatbot server')

    # Static files
    @name_space_static.route('/<path:path>')
    class Static(Resource):
        def get(self, path):
            return send_from_directory('www_static', path)

    # Bot queries
    @name_space_bot.route('/ping')
    class Ping(Resource):
        @api.doc(responses = { 200: 'OK', 400: 'Invalid Argument',
                              500: 'System Error' },
                              params = { })

        def get(self):
            # Session management: Unknown user pinging is meaningless
            if 'uid' not in session:
                return False
            lastactivity[str(session['uid'])] = int(time.time())

    @name_space_bot.route('/bot/<string:query>')
    class Query(Resource):
        @api.doc(responses = { 200: 'OK', 400: 'Invalid Argument',
                              500: 'System Error' },
                              params = { 'query': 'Your request string' })

        def get(self, query):
            try:
                # Session management
                if 'uid' not in session:
                    session['uid'] = uuid.uuid4()
                lastactivity[str(session['uid'])] = int(time.time())
                cleanup_sessions()

                if str(session['uid']) not in chatbots:
                    chatbots[str(session['uid'])] = \
                            DemoChatBot()
                    new_session = True
                else:
                    new_session = False

                # Chat response
                print(session['uid'])
                response = chatbots[str(session['uid'])].process_query(query)
                buttons = chatbots[str(session['uid'])].get_buttons_for_last_response()

                print ({ 'query': query, 'botresponse': response, 'buttons': buttons })
                return { 'response': response, 'buttons': buttons, 'new_session': new_session }
            except KeyError as exception:
                name_space_bot.abort(500, exception.__doc__, status = "Could not retrieve information", statusCode = "500")
            #        except Exception as e:
            #            name_space_bot.abort(400, e.__doc__, status = "Could not save information", statusCode = "400")

            # Bot training
            # @name_space_bot.route('/train')
            # class Train(Resource):
            #     def get(self):
            #         return {'success': chatbot.train()}

    def cleanup_sessions():
        """
        Delete inactive sessions
        """

        now = int(time.time())

        for uid in dict(lastactivity):
            diff = max(0, now - lastactivity[uid])
            print("Last activity of {}: {} -- {} sec ago".format(uid, lastactivity[uid], diff))

            if diff < SESSION_TIMEOUT:
                continue

            print("Cleaning up session {}.".format(uid))
            del lastactivity[uid]
            if uid in chatbots:
                del chatbots[uid]

    return app

if __name__ == '__main__': # start up Flask server
    PORT = 8080
    if len(sys.argv) == 3 and sys.argv[1] == "--port" and sys.argv[2].isnumeric():
        PORT = int(sys.argv[2])
    elif len(sys.argv) != 1:
        print("usage: {} [--port PORT]".format(sys.argv[0]))
        sys.exit(0)

    flask_app = create_app()
    print("URL map:\n{}".format(flask_app.url_map))
    flask_app.run(debug=True, port=PORT, host="0.0.0.0")
