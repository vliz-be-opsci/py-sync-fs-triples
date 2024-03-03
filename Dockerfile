FROM python:3.8-buster

COPY ./ /syncfstriples
WORKDIR /syncfstriples

RUN python -m pip install --upgrade pip && \
    pip install poetry && \
    make init

ENTRYPOINT ["syncfstriples"]
