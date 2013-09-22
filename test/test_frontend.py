import unittest
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException


class FrontendTest():

    def setUp(self):
        self.server = subprocess.Popen(
            ['python2', 'mathics/server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        time.sleep(1)

        browser_name = self.__class__.__name__
        self.driver = getattr(webdriver, browser_name[:-4])()

    def tearDown(self):
        self.driver.close()
        self.server.terminate()

    def test_basic(self):
        driver = self.driver
        driver.get("http://localhost:8000")
        self.assertEqual("Mathics", driver.title)

        welcome = driver.find_element_by_id('welcome')
        self.assertEqual(
            welcome.text,
            "Welcome to Mathics!\n"
            "Mathics is a general-purpose computer algebra system.\n"
            "Enter queries and submit them by pressing Shift + Return. "
            "See the gallery for some neat examples or the documentation "
            "for a full list of supported functions. "
            "Mathics uses MathJax to display beautiful math.\n"
            "Visit mathics.org for further information about the project.")

    def test_documentation(self):
        driver = self.driver
        driver.get("http://localhost:8000")

        search = driver.find_element_by_id('search')
        for key in "Plus":
            search.send_keys(key)
            time.sleep(0.01)

        time.sleep(0.5)
        doc = driver.find_element_by_id('docContent')
        self.assertEquals(doc.find_element_by_tag_name('h1').text, 'Plus (+)')

    def test_query(self):
        driver = self.driver
        driver.get("http://localhost:8000")

        def do_request(input, wait=0.5):
            query = driver.find_elements_by_class_name('query')[-1]

            # Evaluate the query
            request = query.find_element_by_tag_name('textarea')
            request.send_keys(input)
            request.send_keys(Keys.SHIFT + Keys.RETURN)

            # Wait for the response
            time.sleep(wait)

            return query.find_element_by_class_name('out')

        self.assertEquals(
            do_request('1+1').text, '2')
        self.assertEquals(
            do_request('x/y').text, 'x\ny')


def has_driver(driver):
    try:
        driver().close()
    except WebDriverException:
        return False
    else:
        return True


@unittest.skipUnless(has_driver(webdriver.Firefox), "no Firefox")
class FirefoxTest(FrontendTest, unittest.TestCase):
    pass


@unittest.skipUnless(has_driver(webdriver.Chrome), "no Chrome")
class ChromeTest(FrontendTest, unittest.TestCase):
    pass


@unittest.skipUnless(has_driver(webdriver.Ie), "no Ie")
class IeTest(FrontendTest, unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
