.PHONY: help install setup test clean data docs

help:
	@echo "Comandos disponibles:"
	@echo "  make install     Instalar dependencias"
	@echo "  make setup       Configurar entorno"
	@echo "  make test        Ejecutar pruebas"
	@echo "  make clean       Limpiar archivos temporales"
	@echo "  make data        Descargar datos de ejemplo"
	@echo "  make docs        Generar documentación"

install:
	pip install -r requirements.txt
	pip install -e .

setup:
	mkdir -p Datos/crudos Datos/procesados Resultados
	cp .env.example .env
	@echo "Por favor, edita el archivo .env con tus configuraciones"

test:
	pytest Codigo/tests/ -v

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/ dist/ *.egg-info
	rm -rf Resultados/intermedios/*

data:
	@echo "Descargando datos de ejemplo..."
	# Comandos para descargar datos irán aquí

docs:
	cd Documentacion && make html
	@echo "Documentación generada en Documentacion/_build/html"
