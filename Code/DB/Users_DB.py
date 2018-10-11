from DB_Wrapper import DB_Wrapper
import hashlib
from uuid import uuid4
from os import remove

"""
    - wrapper for users table in the database
    - password requirement checking
    - unique username checking
    - sanitization -> should be built into db parent class
"""

class Users_DB(DB_Wrapper):
    def __init__(self, db_path):
        super().__init__(db_path)
        self.init_table()

    def init_table(self):
        self.execute_queries_from_file("DB/Create_Users_Table.sql")

    # checks if passed username is unique
    # true => unique, false => not unique
    def check_unique_username(self, username):
        query = "SELECT username FROM users WHERE username='{0}'".format(username)
        query_result = self.execute_queries(query, get_result=True)

        # if no value is returned from this query, the username is unique
        if query_result == []:
            return True
        else:
            return False

    # password must have at least one capital letter and one number
    # returns true if the passed password is acceptable
    def check_acceptable_password(self, password):
        has_number = False
        has_capital = False
        ind = 0
        pword_len = len(password)  # so it does not have to be recalculated
        while not (has_number and has_capital) and (ind < pword_len):
            unicode_num = ord(password[ind])
            # checks if the character is a capital
            if 65 <= unicode_num <= 90:
                has_capital = True
            # checks if the character is a number
            elif 48 <= unicode_num <= 57:
                has_number = True
            ind += 1
        return has_capital and has_number

    # hashes a passed password - currently returns the hex version of the hashing
    # uses sha256 hashing algorithm
    def hash_password(self, password):
        salt = uuid4().hex # random data to increase protection on password
        to_hash = salt.encode() + password.encode() # encode converts string to bytes, so it can be encoded
        return hashlib.sha256(to_hash).hexdigest() + ":" + salt

    # confirms if the passed plaintext password and the hashed password are equivalent
    def verify_password(self, password, hashed_password):
        half_hashed_password, salt = hashed_password.split(":")
        user_passed_hashed = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
        return user_passed_hashed == half_hashed_password

    # creates a new user and inserts them into the database
    # returns false if the password or username is not valid
    # returns true if successful insertion
    def create_new_user(self, username, password, type="user"):
        unique_username = self.check_unique_username(username)
        safe_username = self.sanitize_query(username)
        acceptable_password = self.check_acceptable_password(password)
        if not unique_username or not acceptable_password or not safe_username:
            return False
        hashed_password = str(self.hash_password(password))
        query = 'INSERT INTO users (username, password, type) VALUES ("{0}", "{1}", "{2}")'.format(username,
                                                                                                   hashed_password,
                                                                                                   type)
        self.execute_queries(query)
        return True

    # fetch the games won and the games played for a passed id
    def get_user_game_data(self, username):
        query = "SELECT games_won, games_played FROM users WHERE username='{0}'".format(username)
        result = self.execute_queries(query, get_result=True)
        return result

    # pass a username and password
    # returns true if the username and password is correct for a login
    def check_login(self, username, password):
        # get record from db via username
        # checkpassword from record,
        # if username does not exist or password is incorrect, return false
        query = "SELECT username, password FROM users WHERE username='{0}'".format(username)
        result = self.execute_queries(query, get_result=True)
        if result == []:
            return False
        result = result[0]
        hased_pw = result[1]
        return (self.verify_password(password, hased_pw))

    # pass in username and password and get back the user type
    def get_user_type(self, username, password):
        if self.check_login(username, password) == False:
            return False
        q = """
            SELECT type
            FROM users
            WHERE username='{0}'
            """.format(username)
        res = self.execute_queries(q, get_result=True)
        return res[0][0]

if __name__ == "__main__":
    u_name = "SwaggyShaggy999"
    p_word = "Adlfkjgklf3"

    u_db_wrapper = Users_DB("test_db.sqlite")
    u_db_wrapper.execute_queries_from_file("Create_Users_Table")
    u_db_wrapper.execute_queries("SELECT * FROM users WHERE username='SwaggyShaggy99'")
    print("acceptable pword", u_db_wrapper.check_acceptable_password(p_word))
    print("insertion", u_db_wrapper.create_new_user(u_name, p_word))
    print("unique uname after insertion", u_db_wrapper.check_unique_username(u_name))
    u_db_wrapper.display_all_records("users")
    print(u_db_wrapper.check_login(u_name, p_word))
    print(u_db_wrapper.get_user_type(u_name, p_word))
   # remove("blackjack.sqlite")
