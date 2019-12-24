import time
import unittest
from selenium import webdriver

# Invoke a new Chrome Instance
ff_driver = webdriver.Chrome()
#ff_driver = webdriver.Firefox()
#ff_driver = webdriver.Edge()

# Blocking wait of 30 seconds in order to locate the element
ff_driver.implicitly_wait(1)
ff_driver.maximize_window()
# Open the required page
ff_driver.get("http://127.0.0.1:5000/")
# Sleep for 10 seconds in order to see the results
time.sleep(1)
# Close the Browser instance
ff_driver.close()


