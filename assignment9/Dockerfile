FROM python:3

ADD assignment9.py /
ADD requirements.txt /
ADD wsgi.py /

RUN pip3 install -r requirements.txt

CMD ["gunicorn", "--workers", "3", "--bind", "0.0.0.0:8080", "wsgi:app"]