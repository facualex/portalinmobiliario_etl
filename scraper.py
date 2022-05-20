from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from threading import Timer
import gc

from bs4 import BeautifulSoup

import pandas
import json
from os import path

'''
    @desc 
    @author Facundo Alexandre Buchelli
    @date 02/05/2022
'''

MAX_WEBDRIVER_WAIT = 4  # Eseprar máximo X segundos a que carguen elementos JS

ELEMENTS_TO_SCRAPE = ('Ambientes', 'Comodidades y equipamiento')

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

default_driver_options = ['--ignore-certificate-errors', '--disable-logging', 'start-maximized',
                           '--no-sandbox', '--disable-dev-shm-usage', '--disable-browser-side-navigation']

default_comunas_csv_path = '/comunas.csv'

class Scraper:
    def __init__(self, driver_options=default_driver_options, comunas_csv_relative_path=default_comunas_csv_path):
        self.apartment_links = {}
        self.apartments_data = []
        self.__init_driver(driver_options)
        self.comunas_dataframe = pandas.read_csv(path.dirname(
            path.realpath(__file__)) + comunas_csv_relative_path)

    def __del__(self):
        self.driver.quit()

    def __init_driver(self, driver_options):
        try:
            service = Service(GeckoDriverManager().install())
            options = webdriver.FirefoxOptions()

            caps = DesiredCapabilities().FIREFOX
            caps["pageLoadStrategy"] = "none"   # Do not wait for full page load

            for driver_option in driver_options:
                options.add_argument(driver_option)

            driver = webdriver.Firefox(
                service=service, options=options)

            driver.maximize_window()

            self.driver = driver
            print("DRIVER INITIALIZED")
        except Exception as e:
            print(e)

    async def start_scrape(self, write_results_to_json=False):
        try:
            comunas = self.comunas_dataframe['Comuna'].values

            # 1. Por cada comuna
            for comuna in comunas:
                print('Obteniendo URLs para la comuna %s' % (comuna))

                try:
                    base_url = "https://www.portalinmobiliario.com/arriendo/departamento/%s-metropolitana" % (
                        comuna)

                    self.driver.get(base_url)
                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, 'lxml')

                    self.__get_apartment_links(commune=comuna, soup_instance=soup)

                    # 1.1. Mientras existe un elemento <a> con title=Siguiente
                    next_page_link = soup.find('a', title='Siguiente')

                    if (next_page_link):
                        # Mientras exista una siguiente página, visitarlas y extraer las URLs pertinentes
                        while (next_page_link):
                            try:
                                self.driver.get(str(next_page_link['href']))
                                page_source = self.driver.page_source
                                soup = BeautifulSoup(page_source, 'lxml')

                                self.__get_apartment_links(
                                    commune=comuna, soup_instance=soup)

                                next_page_link = soup.find('a', title='Siguiente')
                                soup.decompose()
                                gc.collect()
                            except Exception as e:
                                print(e)
                    
                    soup.decompose()
                    gc.collect()
                except Exception as e:
                    print("Exception 1")
                    print(e)

            if (write_results_to_json):
                apartments_by_commune = open(
                    "apartments_by_commune_urls.json", "a")
                apartments_by_commune.write(json.dumps(self.apartment_links))
                apartments_by_commune.close()

            self.get_apartments_data()
        except IOError:
            print('Error')

    def __get_apartment_links(self, commune, soup_instance):
        if (soup_instance):
            apartment_list_elements = soup_instance.find_all(
                'div', class_='ui-search-result__wrapper')

            for apartment in apartment_list_elements:
                try:
                    apartment_link = apartment.find('a', class_='ui-search-link')
                    if (commune in self.apartment_links):
                        self.apartment_links[commune].append(
                            str(apartment_link['href']))
                    else:
                        self.apartment_links[commune] = [str(apartment_link['href'])]
                except Exception as e:
                    print("Exception 2")

                    print(e)
                    continue
            
            print("%s:%d" % (commune, len(self.apartment_links[commune])))

    def __parse_apartment_data(self, commune, soup_instance):
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

        def get_tab_info(element):
            if(element.text not in ELEMENTS_TO_SCRAPE):
                return

            def get_ambientes_info(ambiente):
                if (str(ambiente.text) in FEATURES_TO_VARIABLE_MAP):
                    set_apartment_property(
                        FEATURES_TO_VARIABLE_MAP[str(ambiente.text)], True, apartment_data)
                gc.collect()
            
            def get_comodity_info(comodity):
                if (str(comodity.text) in FEATURES_TO_VARIABLE_MAP):
                    set_apartment_property(
                        FEATURES_TO_VARIABLE_MAP[str(comodity.text)], True, apartment_data)
                gc.collect()


            try:
                if (element.text == ELEMENTS_TO_SCRAPE[0]): # Ambientes
                    ambientes = WebDriverWait(self.driver, MAX_WEBDRIVER_WAIT).until(
                        EC.visibility_of_any_elements_located(
                            (By.ID, "tab-content-id-ambientes"))
                    )
                    ambientes_info = ambientes[0].find_elements(
                        By.XPATH, 'div')

                    loop_stopper = LoopStopper(10) # Parar despues de 10 segundos
                    loop_stopper.run(ambientes_info, get_ambientes_info)
                elif (element.text == ELEMENTS_TO_SCRAPE[1]): # Comodidades y equipamiento
                        element.click()

                        comodities = WebDriverWait(self.driver, MAX_WEBDRIVER_WAIT).until(
                            EC.visibility_of_any_elements_located(
                                (By.ID, "tab-content-id-comodidades-y-equipamiento"))
                        )
                        comodities_info = comodities[0].find_elements(
                            By.XPATH, 'div')

                        loop_stopper = LoopStopper(10) # Parar despues de 10 segundos
                        loop_stopper.run(comodities_info, get_comodity_info)
            except Exception as e:
                print(e)

        def get_properties(row):
            property = str(row.find('th').get_text())
            value = str(row.find('td').get_text())

            # Setear las caracteristicas al diccionario del departamento. Se usa FEATURES_TO_VARIABLE_MAP
            # como diccionario traductor entre el nombre de la característica en la tabla y el nombre de la variable
            # donde se va a almacenar en el diccionario apartment_data.
            if (property in FEATURES_TO_VARIABLE_MAP):
                set_apartment_property(
                    FEATURES_TO_VARIABLE_MAP[property], value, apartment_data)

        try:
            self.driver.implicitly_wait(1)
            # Traer tablas de características del departamento
            properties_table = soup_instance.find(
                'tbody', class_='andes-table__body')

            if (properties_table):
                try:
                    # Obtener todas las filas de la tabla, es decir característica por característica
                    properties_rows = properties_table.find_all('tr')
                    price = str(soup_instance.find(
                        'span', class_='andes-money-amount__fraction').get_text())

                    # CARACETERISTICAS PRINCIPALES
                    set_apartment_property('precio', price, apartment_data)
                    set_apartment_property('comuna', commune, apartment_data)

                    loop_stopper = LoopStopper(10) # Parar despues de 10 segundos
                    loop_stopper.run(properties_rows, get_properties)

                    # Recorrer las características obtenidas de la tabla
                except Exception as e:
                    print("Exception 3")

                    print(e)
            
            soup_instance.decompose()

            additional_info_tabs = WebDriverWait(self.driver, MAX_WEBDRIVER_WAIT).until(
                EC.visibility_of_any_elements_located(
                    (By.CSS_SELECTOR, ".andes-tabs"))
            )

            if (additional_info_tabs):
                tab_buttons = additional_info_tabs[0].find_elements(
                    By.XPATH, './child::*')

                self.driver.execute_script(
                    "return arguments[0].scrollIntoView();", additional_info_tabs[0])

                loop_stopper = LoopStopper(10) # Parar despues de 10 segundos
                loop_stopper.run(tab_buttons, get_tab_info)
        except:
            print("Error parsing this page.")

        return apartment_data

    def get_apartments_data(self):
        def do_something(comuna):
            links_for_commune = self.apartment_links[comuna]

            for index, link in enumerate(links_for_commune):
                try:
                    print("%s %d/%d" % (comuna, index+1, len(links_for_commune)))
                    self.driver.get(link)
                    page_source = self.driver.page_source
                    soup = BeautifulSoup(page_source, 'lxml')

                    apartment_data = self.__parse_apartment_data(
                        commune=comuna, soup_instance=soup)

                    self.apartments_data.append(apartment_data)
                    soup.decompose()
                    gc.collect()
                except Exception as e:
                    print("Exception 4")
                    print(e)

        loop_stopper = LoopStopper(10) # Parar despues de 10 segundos
        loop_stopper.run(self.apartment_links, do_something)
       
        try:
            all_apartments_data = open("all_apartments_data.json", "a")
            all_apartments_data.write(json.dumps(self.apartments_data))
            all_apartments_data.close()
        except Exception as e:
            print("Exception 5")

            print(e)

def set_apartment_property(property, value, apartment_properties_dict):
    if (property in apartment_properties_dict):
        apartment_properties_dict[str(property)] = str(value)

class LoopStopper: 
    def __init__(self, seconds): 
        self._loop_stop = False 
        self._seconds = seconds 
    
    def __del__(self):
        if (self.timer):
            self.timer.cancel()

    def _stop_loop(self): 
        self._loop_stop = True 
    
    def get_index(self):
        return self.index

    def run( self, generator_expression, task): 
        """ Execute a task a number of times based on the generator_expression""" 
        t = Timer(self._seconds, self._stop_loop) 
        self.timer = t

        t.start() 

        for i in generator_expression: 
            task(i) 
            if self._loop_stop: 
                break 

        t.cancel() # Cancel the timer if the loop ends ok. 