'''
    Módulo para normalizar los datos obtenidos del scrape realizado en 'scraper.py'.

    Estructura de datos:
        apartment_data = {
            'precio': '',
            'comuna': '',
            'superficie_total': '',
            'superficie_util': '',
            'dormitorios': '',
            'antiguedad': '',
            'banos': '',
            'gastos_comunes': '',
            'estacionamientos': '',
            'bodegas': '',
            'ambientes': '',
            'orientacion': '',
            'admite_mascotas': '',
            'cantidad_max_habitantes': '',
            'piso': '',
            'departamentos_por_piso': '',
            'cantidad_pisos': '',
            'balcon': False,
            'terraza': False,
            'estacionamiento_visitas': False,
            'salon_multiuso': False,
            'piscina': False,
            'gimnasio': False,
            'parrilla': False,
            'jardin': False,
            'amoblado': False,
        }

    INPUT de esta función (y OUTPUT de 'scraper.py'): {
        nombre_comuna: [apartment_data_1, apartment_data_2, ... apartment_data_N],
        ...
    }
'''