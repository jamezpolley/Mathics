import sys
import time
import subprocess
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException

if sys.version_info[:2] == (2, 7):
    import unittest
else:
    import unittest2 as unittest


class FrontendTest():

    def setUp(self):
        self.server = subprocess.Popen(
            ['python2', 'mathics/server.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        time.sleep(1)

        browser_name = self.__class__.__name__
        self.driver = getattr(webdriver, browser_name[:-4])()
        self.driver.get("http://localhost:8000")
        time.sleep(1)

    def tearDown(self):
        self.driver.quit()
        self.server.terminate()

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

        doclink = driver.find_element_by_id("doclink")
        self.assertEqual(doclink.text, "Documentation")
        doclink.click()
        time.sleep(0.1)

        doc = driver.find_element_by_id('docContent')
        self.assertTrue(doc.is_displayed())
        self.assertTrue(
            doc.text.startswith("Documentation\nManual\nIntroduction\n"))

        doc.find_element_by_partial_link_text("Introduction").click()
        time.sleep(0.1)
        doc = driver.find_element_by_id('docContent')
        self.assertEqual(
            doc.find_element_by_tag_name("h1").text, "Introduction")
        self.assertTrue(
            doc.find_element_by_tag_name("p").text.startswith("Mathics"))

        doc.find_element_by_partial_link_text("Installation").click()
        time.sleep(0.1)
        doc = driver.find_element_by_id('docContent')
        self.assertEqual(
            doc.find_element_by_tag_name("h1").text, "Installation")

        doc.find_element_by_partial_link_text("Overview").click()
        time.sleep(0.1)
        doc = driver.find_element_by_id('docContent')
        self.assertEqual(
            doc.find_element_by_tag_name("h1").text, "Documentation")
        doclink.click()
        time.sleep(0.1)
        doc = driver.find_element_by_id('docContent')
        self.assertFalse(doc.is_displayed())

    def test_doc_search(self):
        driver = self.driver
        search = driver.find_element_by_id('search')
        self.assertEqual(search.text, "")

        for key in "Plus":
            search.send_keys(key)
            time.sleep(0.2)

        doc = driver.find_element_by_id('docContent')
        self.assertEquals(doc.find_element_by_tag_name('h1').text, 'Plus (+)')

    def test_keyboard_commands(self):
        driver = self.driver
        body = driver.find_element_by_tag_name("body")

        # Ctrl-D
        body.send_keys(Keys.CONTROL + "D")
        docsearch = driver.switch_to_active_element()
        docsearch.send_keys("D")
        time.sleep(0.5)
        doc = driver.find_element_by_id('docContent')
        self.assertTrue(doc.is_displayed())
        self.assertEqual(
            doc.find_element_by_tag_name("h1").text, "D")

        # Ctrl-C
        body.send_keys(Keys.CONTROL + "C")
        time.sleep(0.5)
        self.assertTrue(doc.is_displayed())
        focus = driver.switch_to_active_element()
        self.assertEqual(focus.tag_name, "textarea")
        self.assertEqual(focus.text, "")

        # Ctrl-O
        popup = driver.find_element_by_id("open")
        self.assertFalse(popup.is_displayed())
        body.send_keys(Keys.CONTROL + "O")
        time.sleep(0.5)
        self.assertTrue(popup.is_displayed())
        popup.find_element_by_class_name("cancel").click()
        time.sleep(0.5)
        self.assertFalse(popup.is_displayed())

        # Ctrl-S
        popup = driver.find_element_by_id("save")
        self.assertFalse(popup.is_displayed())
        body.send_keys(Keys.CONTROL + "S")
        time.sleep(0.5)
        self.assertTrue(popup.is_displayed())
        popup.find_element_by_class_name("cancel").click()
        time.sleep(0.5)
        self.assertFalse(popup.is_displayed())

    def test_query(self):
        driver = self.driver

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
