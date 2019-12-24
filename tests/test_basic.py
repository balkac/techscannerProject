import unittest
from app import app

#UNIT TESTS--------------------

## TESTS MUST BE RUN ONE BY ONE !!!! ALL PASSED

class BasicTests(unittest.TestCase):

    ############################
    #### setup and teardown ####
    ############################

    # executed prior to each test
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['DEBUG'] = False

        self.app = app.test_client()
        self.assertEqual(app.debug, False)

    # executed after each test
    def tearDown(self):
        pass

    ###############
    #### tests ####
    ###############

    ### ADD FAV ###
    def test_main_page(self):   #1 #go to index page
        response = self.app.get('/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_login_page(self):   #2 # go to login page
        response = self.app.get('/login',follow_redirects=True)
        self.assertEqual(response.status_code,200)

    def test_attributes_page(self):  #3 #go to selectingAttribute page
        response = self.app.get('/selectingAttribute',follow_redirects=True)
        self.assertEqual(response.status_code,200)


    def test_login(self):             #4  #login with register registering account
        response=self.login("admin","12345")
        self.assertEqual(response.status_code, 200)

    def test_login2(self):            #5  #login with not registering account
        response =self.login("sss","123")
        self.assertEqual(response.status_code, 404)

    def test_login3(self):          #6 login without typing any user name
        response= self.login("","123")
        self.assertEqual(response.status_code,404)

    def test_login4(self):
        response= self.login("admin","") #7 login without typing password
        self.assertEqual(response.status_code, 404)

    def test_login5(self):
        response=self.login("admin","4565") #8  login with wrong password
        self.assertEqual(response.status_code,404)

    def test_register(self):    #9  #register new user
        response = self.register("elon","musk","elonmusk@tesla.com","elonmusk","1234")
        self.assertEqual(response.status_code,200)

    def test_register2(self):  #10 register new user
        response = self.register("furkan","balkaç","furkanbalkac@gmail.com","furkan","21312ffğ")
        self.assertEqual(response.status_code, 200)

    def test_search(self):  #11 searcing asus on texbox  #7
        response = self.search("asus")
        self.assertEqual(response.status_code,200)

    def test_search2(self): #12 searcing turkish char   #6
        response = self.search('ş')
        self.assertEqual(response.status_code,404)

    def test_search3(self):  #13 searcing lenovo on texbox  #8
        response = self.search("lenovo")
        self.assertEqual(response.status_code, 200)

    def test_search4(self): #14 searcing dell
        response = self.search("dell")
        self.assertEqual(response.status_code, 200)

    def test_search5(self): #15 searcing hp 4gb
        response = self.search("hp 4gb")
        self.assertEqual(response.status_code, 200)

    def test_search6(self):  #16 searcing apple on texbox   #9
        response = self.search("apple")
        self.assertEqual(response.status_code,200)

    def test_selectatt(self):   #17 correct search attributes  #10
        response = self.selectatt("apple","i5","8gb","ssd","0","10000")
        self.assertEqual(response.status_code,200)

    def test_selectatt2(self):  #18 correct search attributes2
        response = self.selectatt("dell", "i5", "4gb", "ssd", "0", "5000")
        self.assertEqual(response.status_code, 200)

    def test_selectatt3(self):  #19 correct search attributes
        response = self.selectatt("msi", "i7", "8gb", "hdd", "6000", "7000")
        self.assertEqual(response.status_code, 200)

    def test_selectatt4(self):  #20 min > max attributes
        response = self.selectatt("apple", "i3", "8gb", "ssd", "10000", "0")
        self.assertEqual(response.status_code, 404)

    def test_selectatt5(self): #21 min>max attributes
        response = self.selectatt("dell", "i5", "8gb", "ssd", "500", "5")
        self.assertEqual(response.status_code, 404)

    ########################
    #### helper methods ####
    ########################
    def login(self, username, password):
        return self.app.post(
            '/login',
            data=dict(username=username, password=password),
            follow_redirects=True
        )

    def register(self,name,surname,email,username,password):
        return self.app.post(
            '/register',
            data=dict(name=name, surname=surname,email=email, username=username,password=password),
            follow_redirects= True
        )

    def search(self,searchtext):
        return self.app.post(
            '/',
            data=dict(search=searchtext),
            follow_redirects=True
        )

    def selectatt(self,brand,cpu,ram,storagemedia,minprice,maxprice):
        return self.app.post(
            '/selectingAttribute',
            data=dict(brand=brand,cpu=cpu,ram=ram,storagemedia=storagemedia,minprice=minprice,maxprice=maxprice),
            follow_redirects=True
        )



if __name__ == '__main__':
    unittest.main()
