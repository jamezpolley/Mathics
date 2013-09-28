import sys
import subprocess
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import ui
from selenium.common.exceptions import WebDriverException

if sys.version_info[:2] == (2, 7):
    import unittest
else:
    import unittest2 as unittest

server = None

def setUpModule():
    global server
    server = subprocess.Popen(
        ['python2', 'mathics/server.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE)


def tearDownModule():
    global server
    server.terminate()


class FrontendTest():

    def setUp(self):
        browser_name = self.__class__.__name__
        self.driver = getattr(webdriver, browser_name[:-4])()
        self.driver.get("http://localhost:8000")
        self.wait = ui.WebDriverWait(self.driver, 10)

    def tearDown(self):
        self.driver.quit()

    def test_basic(self):
        driver = self.driver

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

    def test_doc_links(self):
        driver = self.driver
        wait = self.wait

        doclink = wait.until(lambda d: d.find_element_by_id("doclink"))
        self.assertEqual(doclink.text, "Documentation")
        doclink.click()

        doc = wait.until(lambda d: d.find_element_by_id("docContent"))
        self.assertTrue(doc.is_displayed())
        self.assertTrue(
            doc.text.startswith("Documentation\nManual\nIntroduction\n"))

        doc.find_element_by_partial_link_text("Introduction").click()
        doc = wait.until(lambda d: d.find_element_by_id("docContent"))
        self.assertEqual(
            wait.until(lambda d: doc.find_element_by_tag_name("h1")).text,
            "Introduction")

        doc.find_element_by_partial_link_text("Installation").click()
        doc = wait.until(lambda d: d.find_element_by_id("docContent"))
        self.assertEqual(
            wait.until(lambda d: doc.find_element_by_tag_name("h1")).text,
            "Installation")

        doc.find_element_by_partial_link_text("Overview").click()
        doc = wait.until(lambda d: d.find_element_by_id("docContent"))
        self.assertEqual(
            wait.until(lambda d: doc.find_element_by_tag_name("h1")).text,
            "Documentation")

        doclink.click()
        doc = wait.until(lambda d: d.find_element_by_id("docContent"))
        self.assertFalse(doc.is_displayed())

    def test_doc_search(self):
        driver = self.driver
        wait = self.wait

        search = wait.until(lambda d: d.find_element_by_id("search"))
        self.assertEqual(search.text, "")
        search.send_keys("Plus")
        doc = wait.until(lambda d: d.find_element_by_id("docContent"))
        self.assertEquals(doc.find_element_by_tag_name('h1').text, 'Plus (+)')

    def test_keyboard_commands(self):
        driver = self.driver
        wait = self.wait
        body = wait.until(lambda d: d.find_element_by_tag_name("body"))

        # Ctrl-D
        body.send_keys(Keys.CONTROL + "D")
        docsearch = driver.switch_to_active_element()
        docsearch.send_keys("D")
        wait.until(lambda d: d.find_element_by_id("docContent").is_displayed())
        doc = driver.find_element_by_id('docContent')
        self.assertEqual(
            doc.find_element_by_tag_name("h1").text, "D")

        # Ctrl-C
        body.send_keys(Keys.CONTROL + "C")
        wait.until(lambda d: (
            d.switch_to_active_element().tag_name == "textarea"))

        # Ctrl-O
        popup = driver.find_element_by_id("open")
        self.assertFalse(popup.is_displayed())
        body.send_keys(Keys.CONTROL + "O")
        wait.until(lambda d: popup.is_displayed())
        popup.find_element_by_class_name("cancel").click()
        wait.until(lambda d: not popup.is_displayed())

        # Ctrl-S
        popup = driver.find_element_by_id("save")
        self.assertFalse(popup.is_displayed())
        body.send_keys(Keys.CONTROL + "S")
        wait.until(lambda d: popup.is_displayed())
        popup.find_element_by_class_name("cancel").click()
        wait.until(lambda d: not popup.is_displayed())

    def test_query(self):
        driver = self.driver
        wait = self.wait

        def do_request(input):
            q= driver.find_elements_by_class_name('query')[-1]

            # Evaluate the query
            request = q.find_element_by_tag_name('textarea')
            request.send_keys(input)
            request.send_keys(Keys.SHIFT + Keys.RETURN)

            # Wait for the response
            return wait.until(lambda d: q.find_element_by_class_name("out"))

        self.assertEquals(
            do_request('1+1').text, '2')
        self.assertEquals(
            do_request('x/y').text, 'x\ny')


def has_driver(driver):
    try:
        driver().quit()
    except WebDriverException:
        return False
    else:
        return True

# Tests fail under chrome webdriver - can't focus on correct element
# @unittest.skipUnless(has_driver(webdriver.Chrome), "no Chrome")
# class ChromeTest(FrontendTest, unittest.TestCase):
#     pass


@unittest.skipUnless(has_driver(webdriver.Firefox), "no Firefox")
class FirefoxTest(FrontendTest, unittest.TestCase):
    pass


@unittest.skipUnless(has_driver(webdriver.Ie), "no Ie")
class IeTest(FrontendTest, unittest.TestCase):
    pass


if __name__ == "__main__":
    unittest.main()
