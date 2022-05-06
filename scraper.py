from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

import pandas
import json
from os import path

FEATURES_TO_VARIABLE_MAP = {
    'Superficie total': 'superficie_total',
    'Superficie útil': 'superficie_util',
    'Dormitorios': 'dormitorios',
    'Antigüedad': 'antiguedad',
    'Baños': 'banos',
    'Gastos comunes': 'gastos_comunes',
    'Estacionamientos': 'estacionamientos',
    'Bodegas': 'bodegas',
    'Ambientes': 'ambientes',
    'Orientación': 'orientacion',
    'Admite mascotas': 'admite_mascotas',
    'Cantidad máxima de habitantes': 'cantidad_max_habitantes',
    'Número de piso de la unidad': 'piso',
    'Departamentos por piso': 'departamentos_por_piso',
    'Cantidad de pisos':  'cantidad_pisos',
    'Balcón':  'balcon',
    'Terraza': 'terraza',
    'Estacionamiento de visitas': 'estacionamiento_visitas',
    'Salón de usos múltiples': 'salon_multiuso',
    'Piscina': 'piscina',
    'Gimnasio': 'gimnasio',
    'Parrilla': 'parrilla',
    'Jardín': 'jardin',
    'Amoblado': 'amoblado',
}

'''
    @desc 
    @author Facundo Alexandre Buchelli
    @date 02/05/2022
'''

default_driver_options = ['--ignore-certificate-errors', '--incognito', '--headless']
default_comunas_csv_path = '/comunas.csv'

class Scraper:
    def __init__(self, driver_options = default_driver_options, comunas_csv_relative_path = default_comunas_csv_path):
      self.apartment_links = {}
      self.apartments_data = {}
      self.__init_driver(driver_options)
      self.comunas_dataframe = pandas.read_csv(path.dirname(path.realpath(__file__)) + comunas_csv_relative_path)

    def __init_driver(self, driver_options):
      service = Service(ChromeDriverManager().install())
      options = webdriver.ChromeOptions()

      for driver_option in driver_options:
          options.add_argument(driver_option) 

      driver = webdriver.Chrome(service=service, options=options)
      self.driver = driver

    async def start_scrape(self, write_results_to_json = False):
        try:
            comunas = self.comunas_dataframe['Comuna'].values

            # 1. Por cada comuna
            for comuna in comunas:
                if(comuna == 'el-bosque'):
                    base_url = "https://www.portalinmobiliario.com/arriendo/departamento/%s-metropolitana" % (comuna)

                    self.driver.get(base_url)
                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, 'lxml')

                    self.__get_apartment_links(commune=comuna, soup_instance=soup)

                    # 1.1. Mientras existe un elemento <a> con title=Siguiente
                    next_page_link = soup.find('a', title='Siguiente')

                    if (next_page_link):
                        # Mientras exista una siguiente página, visitarlas y extraer las URLs pertinentes
                        while (next_page_link):
                            self.driver.get(next_page_link['href'])
                            page_source = self.driver.page_source
                            soup = BeautifulSoup(page_source, 'lxml')

                            self.__get_apartment_links(commune=comuna, soup_instance=soup)

                            next_page_link = soup.find('a', title='Siguiente')
                    

            if (write_results_to_json):
                apartments_by_commune = open("apartments_by_commune_urls.json","a")
                apartments_by_commune.write(json.dumps(self.apartment_links))
                apartments_by_commune.close()

            self.get_apartments_data()
        except IOError:
            print('Error')

    def __get_apartment_links(self, commune, soup_instance):
        apartment_list_elements = soup_instance.find_all('div', class_='ui-search-result__wrapper')

        for apartment in apartment_list_elements:
            apartment_link = apartment.find('a', class_='ui-search-link')

            if (commune in self.apartment_links): 
                self.apartment_links[commune].append(apartment_link['href'])
            else:
                self.apartment_links[commune] = [apartment_link['href']]
    
    def __parse_apartment_data(self, soup_instance):
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

        # Traer tablas de características del departamento
        properties_table = soup_instance.find('tbody', class_='andes-table__body')

        # Obtener todas las filas de la tabla, es decir característica por característica
        properties_rows = properties_table.find_all('tr');

        # Recorrer las características obtenidas de la tabla
        for properties_row in properties_rows:
            property = properties_row.find('th').get_text();
            value = properties_row.find('td').get_text();

            # Setear las caracteristicas al diccionario del departamento. Se usa FEATURES_TO_VARIABLE_MAP
            # como diccionario traductor entre el nombre de la característica en la tabla y el nombre de la variable
            # donde se va a almacenar en el diccionario apartment_data.
            set_apartment_property(FEATURES_TO_VARIABLE_MAP[property], value, apartment_data)
        
        price = soup_instance.find('span', class_='andes-money-amount__fraction').get_text()

        # CARACETERISTICAS PRINCIPALES
        set_apartment_property('precio', price, apartment_data)
        set_apartment_property('comuna', 'el-bosque', apartment_data)

        print(apartment_data)


        return apartment_data

    def get_apartments_data(self):
        print(self.apartment_links)
        for comuna in self.apartment_links:
            for apartment_link in self.apartment_links[comuna]:
                self.driver.get(apartment_link)
                page_source = self.driver.page_source
                soup = BeautifulSoup(page_source, 'lxml')

                self.__parse_apartment_data(soup_instance=soup)


def set_apartment_property(property, value, apartment_properties_dict):
    if (value and property in apartment_properties_dict):
        apartment_properties_dict[property] = value