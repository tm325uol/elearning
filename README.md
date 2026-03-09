Setup and Execution Instructions

Development Environment

Operating System: Developed and tested on macOS Tahoe 26.3
Python Version: Python 3.10
Database: SQLite3
Docker: for running a standalone Redis server container

Package Dependencies

The application relies on the following core packages (as defined in requirements.txt):

Django 4.2.27 – main framework for the web application.
Django REST Framework 3.16.1 – used for building REST APIs.
factory_boy 3.3.3 – used for generating test data.
drf-spectacular 0.29.0 – used for Swagger, ReDoc, and API schema generation.
Pillow 12.1.0 – used for image uploads such as profile photos.
channels 4.3.2 – used for real-time features with WebSockets.
channels-redis 4.3.0 – used as the channel layer backend for Channels.
daphne 4.2.1 – ASGI server for running Django with WebSocket support.

Installation and Setup Guide

Follow these steps to unzip, set up, and run the application locally.

1. Extract the application package
unzip elearning_project.zip
cd elearning_project

2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

3. Change to the project root directory
cd elearning

4. Install the required packages
pip install -r requirements.txt

5.  Start Redis server
It must be installed and running locally because the project uses Django Channels for real-time chat and notifications.
Example with Docker container on macOS:

docker run -p 6379:6379 -it redis:latest

6. Reset and Initialize the Database
bash db_reset.sh

7. Generate sample data
The project includes a custom management command located at elearning/apps/courses/management/commands/generate_sample_data.py that uses factory_boy to populate the database with sample data records.

python manage.py generate_sample_data

8. Running the Application
To run the application with WebSocket support enabled, use the standard runserver command, which is handled by Daphne in this project:

python manage.py runserver

Then open the application in your browser at:

http://127.0.0.1:8000
