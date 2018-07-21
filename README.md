#Plataforma de Indexación de Imágenes Radiológicas



##Descripción
Es una aplicación que permite la indexación de la metadata básica de los estudios radiológicos guardados en PACS descentralizados, permitiendo seguir el origen y flujo de los diversos estudios, así como facilitar su centralización y visualización. Provee servicios REST para el registro de los datos, así como la consulta de atenciones por DOC_ID y/o nombre del paciente, la misma que es entregada en formato json.


##Arquitectura

###Núcleo
* Python 2.7 o superior
* MongoDB 3.0 o superior

###Dependencias de Python
* Tornado Web Server 4.5 o superior
* PyMongo 3.5 o superior
* Requests 2.18.4 o superior


##Base de Datos
El motor de persistencia empleado para este micro servicio es MongoDB, por lo tanto las estructuras de datos son no relacionales.  El diseño de la aplicación permite mejorar la estructura de datos cambiando simplemente el formato de entrada (revisar Formato JSON para Insert), la misma que es recibida por el indexador y enviada directamente al motor MongoDB (sin modificar su contenido).
Adicionalmente, para proveer una búsqueda rápida de datos, el indexador define a su inicio los índices que debe emplear la base de datos, los mismos que son definidos en **config.json**.


##Estructura de la aplicación (árbol de archivos)
```
imaging_heading -> Directorio Raiz
    server.py -> Servicio
    requirements.txt -> Archivo dependencias Python
    README.md -> Este documento (Guia uso / desarrollador)
    config.json -> Archivo de configuración
    static -> Directorio de archivos estáticos
    templates -> Directorio de plantillas html según URL
    tests -> Directorio con pruebas de la aplicación
        get_data.py -> Prueba funcional de conexión con server
        test.json -> Archivo json ejemplo con metadata de estudio
    extras -> Directorio con archivos adicionales importantes
        imaging.service -> servicio listo para copiar en /etc/systemd/system
    dicom_heading.log -> Log generado automáticamente por el servicio, no es versionable
```


##Instalación

###Copiar / clonar el directorio en /srv
```
git clone https://alfonsodg@bitbucket.org/controlradiologico/dicom_heading.git
```

###Verificar que se tenga instalado la arquitectura base (python y mongodb)

###Instalar ENV
```
virtualenv venv
```

###Activar ENV
```
source venv/bin/activate
```

###Instalar requerimientos de la aplicación contenidos en requirements.txt
```
pip install -r requirements.txt
```
###Modificar config.json a discreción o dejarlo tal como está para instalación por defecto

###Ejecutar server.py
```
python server.py
```

###Comprobar el acceso al servicio, por ejemplo
```
http://localhost:8899/** (cambiar el localhost por el ip correspondiente)
```


##Inicio Automático
Se ha incluído un servicio en extras/dicom_heading.service:

    /etc/systemd/system/dicom_heading.service   
```
[Unit]
Description = Imaging Service
After = network.target

[Service]
WorkingDirectory = /srv/imaging_heading
ExecStart = /srv/imaging_heading/server.py

[Install]
WantedBy = multi-user.target
```
Una vez creado el archivo activar el servicio de inmediato y al inicio
```
systemctl start lis.service
systemctl enable lis.service
```


##Peticiones Webservices

###Método Post
* /api/v1/register
>Inserta data json de atención (el formato ejemplo está contenido dentro de tests/test.json o revisar titulo **Formato JSON para INSERT (POST)**)

###Método Get
* /api/v1/patient_name/(NOMBRE)
>Busca y devuelve atenciones por nombre o parte del nombre

* /api/v1/patient_id/(DOC_ID)
>Busca y devuelve atenciones por DOC_ID

###Peticiones Estándares
Estas peticiones HTTP sirven como ejemplo funcional de los webservices y su integración con aplicaciones externas

* / o /index
>Página principal del servidor, para fines solo de validación de funcionamiento del servicio

* /patient_studies
>URL que muestra los estudios de un determinado paciente y permite su apertura con el visualizador **oviyam2**, requiere los parámetros **patient_id** y **X-Api-Key**, ejemplo:

    http://localhost:8899/patient_studies?patient_id=3705779-7&X-Api-Key=5954032458e83fc75abf23afd1c01ce3

* /patient_studies_alternate
>URL que muestra los estudios de un determinado paciente y permite su apertura con el visualizador **dwv**, requiere los parámetros **patient_id** y **X-Api-Key**, ejemplo:

    http://localhost:8899/patient_studies_alternate?patient_id=3705779-7&X-Api-Key=5954032458e83fc75abf23afd1c01ce3


##Seguridad
Para poder llamar a las peticiones se requiere que en la cabecera se incluya **X-Api-Key** con la llave proporcionada por el área pertinente.  Las llaves de seguridad deben ser escritas dentro del archivo **config.json**
```
{'X-Api-Key' : '5954032458e83fc75abf23afd1c01ce3'}
```


##Tests
No olvidar que en la cabecera se debe agregar **X-Api-Key** con la llave correspondiente

###Consultas (URLs)

* http://localhost:8899/api/v1/patient_id/26267267-K
* http://localhost:8899/api/v1/patient_name/PEREZ

###Insertar Registros
```
curl -d "@test.json" -H "Content-Type: application/json" -X POST http://localhost:8899/api/v1/register
```


##Estructura de Datos

###Formato JSON para INSERT (POST)
```
    {
      "patient_pk":"Clave primaria de paciente en tabla patient en pacsdb",
      "patient_id":"RUT de paciente",
      "patient_name":"Nombre de paciente",
      "study_pk":"Clave primaria de estudio en tabla study en pacsdb",
      "study_iuid":"Código único de estudio SUID",
      "study_datetime":"Fecha y hora de estudio",
      "study_description":"Descripción de la prueba",
      "study_modality":"Modalidad",
      "study_series":"Número de series",
      "study_instances":"Número de instancias",
      "center":"Código de PACS (centro médico) origen"
    }
```


##Configuración
Está contenido dentro del archivo **config.json**
```
    {
      "database": {  -> Información BD mongo
        "host": "IP o nombre del servidor",
        "port": "Puerto",
        "user": "Nombre de usuario",
        "password": "Clave de usuario",
        "name": "Nombre de las base de datos"
      },
      "indexes": {  -> Indices a crear según estructura JSON)
        "patient_id": true,
        "study_suid": true,
        "patient_name": true
      },
      "application": {  -> Puerto de la aplicación
        "port": 8899
      },
      "keys": [  -> Llaves de autentificación
        "5954032458e83fc75abf23afd1c01ce1",
        "5954032458e83fc75abf23afd1c01ce2"
      ],
      "viewer": "http://IP_ADDRESS:PORT/oviyam2/viewer.html?studyUID=",  -> Visor por defecto
      "viewer_alternate": "http://IP_ADDRESS:PORT/dwv/viewers/mobile/index.html?type=manifest&input=%2Fweasis-pacs-connector%2Fmanifest%3FstudyUID%3D",  -> Visor alternativo
      "login": "http://IP_ADDRESS:PORT/oviyam2",  -> URL visor principal
      "j_security": "http://IP_ADDRESS:PORT/oviyam2/j_security_check",  --> URL autentificador
      "log_file_base": "dicom_heading.log"  --> Nombre base de log
    }
```

##Licencia
Este software es entregado bajo licencia GPL v3, excepto en las librerías que no sean compatibles con esta licencia.  Revisar el archivo **gplv3.md
** para los detalles y alcances del mismo
