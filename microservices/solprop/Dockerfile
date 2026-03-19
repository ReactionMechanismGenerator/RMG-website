FROM continuumio/miniconda3:latest

WORKDIR /app

RUN conda create -n solprop conda-forge::python=3.7 fhvermei::solprop_ml "conda-forge::scipy<1.11" && \
    conda install -n solprop rmg::descriptastorus && \
    conda install -n solprop conda-forge::fastapi conda-forge::uvicorn conda-forge::pydantic conda-forge::requests && \
    conda clean -a -y

COPY server.py .

EXPOSE 8081

CMD ["conda", "run", "--no-capture-output", "-n", "solprop", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8081"]
