TEST_SET = [
    # === LUCES INDIVIDUALES (encender/apagar) ===
    {"id": 1,  "cmd": "enciende la luz del salon 7",         "accion": "encender", "disp": ["luz salon 7"]},
    {"id": 2,  "cmd": "apaga la luz del salon 7",            "accion": "apagar",   "disp": ["luz salon 7"]},
    {"id": 3,  "cmd": "enciende la luz de la cocina",        "accion": "encender", "disp": ["luz cocina"]},
    {"id": 4,  "cmd": "apaga la luz de la cocina",           "accion": "apagar",   "disp": ["luz cocina"]},
    {"id": 5,  "cmd": "enciende la luz del bano 5",          "accion": "encender", "disp": ["luz bano 5"]},
    {"id": 6,  "cmd": "enciende la luz del aula 18",         "accion": "encender", "disp": ["luz aula 18"]},
    {"id": 7,  "cmd": "apaga la luz del dormitorio 12",      "accion": "apagar",   "disp": ["luz dormitorio 12"]},
    {"id": 8,  "cmd": "enciende la entrada 1",               "accion": "encender", "disp": ["luz entrada 1"]},
    {"id": 9,  "cmd": "apaga la entrada 9",                  "accion": "apagar",   "disp": ["luz entrada 9"]},
    {"id": 10, "cmd": "enciende el salon 3",                 "accion": "encender", "disp": ["luz salon 3"]},
    {"id": 11, "cmd": "apaga la luz salon 11",               "accion": "apagar",   "disp": ["luz salon 11"]},
    {"id": 12, "cmd": "enciende luz salon 8",                "accion": "encender", "disp": ["luz salon 8"]},
    {"id": 13, "cmd": "apaga dormitorio 13",                 "accion": "apagar",   "disp": ["luz dormitorio 13"]},
    {"id": 14, "cmd": "enciende la del dormitorio 14",       "accion": "encender", "disp": ["luz dormitorio 14"]},

    # === GRUPOS DE LUCES ===
    {"id": 20, "cmd": "enciende todas las luces del salon",  "accion": "encender", "disp": ["luces salon"]},
    {"id": 21, "cmd": "apaga las luces del salon",           "accion": "apagar",   "disp": ["luces salon"]},
    {"id": 22, "cmd": "enciende las luces del dormitorio",   "accion": "encender", "disp": ["luces dormitorio"]},
    {"id": 23, "cmd": "apaga las luces de los dormitorios",  "accion": "apagar",   "disp": ["luces dormitorio"]},
    {"id": 24, "cmd": "enciende todas las luces de la casa", "accion": "encender", "disp": ["todas las luces de la casa"]},
    {"id": 25, "cmd": "apaga todo",                          "accion": "apagar",   "disp": ["todas las luces de la casa"]},

    # === REGULACIÓN ===
    {"id": 30, "cmd": "regula la luz del salon 3 al 50",     "accion": "regular",  "disp": ["luz salon 3"],  "valor": 50},
    {"id": 31, "cmd": "pon la luz del salon 8 al 75",        "accion": "regular",  "disp": ["luz salon 8"],  "valor": 75},
    {"id": 32, "cmd": "regula aula 18 al 30",                "accion": "regular",  "disp": ["luz aula 18"],  "valor": 30},
    {"id": 33, "cmd": "baja la intensidad del salon 3 al 20","accion": "regular",  "disp": ["luz salon 3"],  "valor": 20},
    {"id": 34, "cmd": "sube la luz del salon 11 al 80",      "accion": "regular",  "disp": ["luz salon 11"], "valor": 80},

    # === PERSIANAS ===
    {"id": 40, "cmd": "sube la persiana de la cocina",       "accion": "subir",    "disp": ["persiana cocina"]},
    {"id": 41, "cmd": "baja la persiana de la cocina",       "accion": "bajar",    "disp": ["persiana cocina"]},
    {"id": 42, "cmd": "sube la persiana del bano",           "accion": "subir",    "disp": ["persiana bano"]},
    {"id": 43, "cmd": "baja la persiana del dormitorio",     "accion": "bajar",    "disp": ["persiana dormitorio"]},
    {"id": 44, "cmd": "sube el estor del salon",             "accion": "subir",    "disp": ["estor salon"]},
    {"id": 45, "cmd": "baja el estor del salon",             "accion": "bajar",    "disp": ["estor salon"]},
    {"id": 46, "cmd": "sube el estor del aula",              "accion": "subir",    "disp": ["estor aula"]},
    {"id": 47, "cmd": "baja el estor del dormitorio",        "accion": "bajar",    "disp": ["estor dormitorio"]},

    # === PERSIANAS CON POSICIÓN ===
    {"id": 50, "cmd": "sube la persiana de la cocina al 50", "accion": "regular",  "disp": ["persiana cocina"], "valor": 50},
    {"id": 51, "cmd": "pon la persiana del bano al 30",      "accion": "regular",  "disp": ["persiana bano"],   "valor": 30},
    {"id": 52, "cmd": "baja el estor del salon al 70",       "accion": "regular",  "disp": ["estor salon"],     "valor": 70},

    # === TODAS LAS PERSIANAS ===
    {"id": 55, "cmd": "sube todas las persianas",            "accion": "subir",    "disp": ["todas las persianas"]},
    {"id": 56, "cmd": "baja todas las persianas",            "accion": "bajar",    "disp": ["todas las persianas"]},

    # === CONSULTAS ===
    {"id": 60, "cmd": "que temperatura hace en el salon",    "accion": "consultar","disp": ["temperatura actual salon"]},
    {"id": 61, "cmd": "cual es la temperatura exterior",     "accion": "consultar","disp": ["temperatura exterior"]},
    {"id": 62, "cmd": "dime la temperatura del salon",       "accion": "consultar","disp": ["temperatura actual salon"]},
    {"id": 63, "cmd": "cuanto marca el sensor de salon",     "accion": "consultar","disp": ["temperatura actual salon"]},

    # === ÓRDENES DOBLES CON "y" ===
    {"id": 70, "cmd": "enciende la luz del salon 7 y apaga la cocina",
     "accion": "compuesta",
     "sub": [
         {"accion": "encender", "disp": ["luz salon 7"]},
         {"accion": "apagar",   "disp": ["luz cocina"]}
     ]},
    {"id": 71, "cmd": "enciende el salon 3 y sube la persiana de la cocina",
     "accion": "compuesta",
     "sub": [
         {"accion": "encender", "disp": ["luz salon 3"]},
         {"accion": "subir",    "disp": ["persiana cocina"]}
     ]},
    {"id": 72, "cmd": "apaga las luces del salon y baja las persianas",
     "accion": "compuesta",
     "sub": [
         {"accion": "apagar", "disp": ["luces salon"]},
         {"accion": "bajar",  "disp": ["todas las persianas"]}
     ]},

    # === VARIANTES DE LENGUAJE ===
    {"id": 80, "cmd": "prende la luz del salon 7",           "accion": "encender", "disp": ["luz salon 7"]},
    {"id": 81, "cmd": "apaga la del salon 7",                "accion": "apagar",   "disp": ["luz salon 7"]},
    {"id": 82, "cmd": "pon la luz de la cocina",             "accion": "encender", "disp": ["luz cocina"]},
    {"id": 83, "cmd": "saca la luz de la cocina",            "accion": "apagar",   "disp": ["luz cocina"]},
    {"id": 84, "cmd": "cierra las persianas de la cocina",   "accion": "bajar",    "disp": ["persiana cocina"]},
    {"id": 85, "cmd": "abre las persianas de la cocina",     "accion": "subir",    "disp": ["persiana cocina"]},
    {"id": 86, "cmd": "levanta las persianas",               "accion": "subir",    "disp": ["todas las persianas"]},
    {"id": 87, "cmd": "extiende los estores",                "accion": "bajar",    "disp": ["todas las persianas"]},

    # === TYPOS Y ERRORES COMUNES ===
    {"id": 90, "cmd": "enciende la perciana de la cocina",   "accion": "subir",    "disp": ["persiana cocina"]},
    {"id": 91, "cmd": "apaga la luz del salón",              "accion": "apagar",   "disp": ["luces salon"]},
    {"id": 92, "cmd": "sube la persiana del cuarto",         "accion": "subir",    "disp": ["persiana dormitorio"]},
    {"id": 93, "cmd": "enciende las luces del baño",         "accion": "encender", "disp": ["luz bano 5", "luz bano 6"]},

    # === ESCENAS / CORTOCIRCUITOS ===
    {"id": 95, "cmd": "hola",                                "accion": "encender", "disp": ["luces salon"]},
    {"id": 96, "cmd": "buenos dias",                         "accion": "encender", "disp": ["luces salon"]},
    {"id": 97, "cmd": "apaga todo al salir",                 "accion": "apagar",   "disp": ["todas las luces de la casa"]},

    # === SIN SENTIDO (debe rechazar o no hacer nada domótico) ===
    {"id": 100, "cmd": "cual es el sentido de la vida",      "accion": None},
    {"id": 101, "cmd": "cuentame un chiste",                 "accion": None},
    {"id": 102, "cmd": "quien es el presidente del gobierno", "accion": None},
    {"id": 103, "cmd": "pizza",                              "accion": None},
]
