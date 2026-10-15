"""PSRS application package and Flask application factory."""
from flask import Flask, jsonify, render_template

from config import Config
from psrs.services.logging_config import configure_logging


def create_app(config_class=Config):
    configure_logging()
    application = Flask(__name__, template_folder="templates", static_folder="static")
    application.config.from_object(config_class)

    @application.get("/")
    def index():
        return render_template("index.html", project_name="PSRS")

    @application.get("/health")
    def health():
        return jsonify({"status": "ok", "project": "PSRS"})

    return application
