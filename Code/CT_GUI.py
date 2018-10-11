from GUI import Window
import tkinter as tk
from Comparison_Tool import Comparison_Tool
import sys,os
sys.path.append(os.path.realpath("../DB"))
from Users_DB import Users_DB

"""
    - gui for comparison tool
    - defines the classes for different windows in the GUI
"""

# main menu class - window with buttons to traverse the gui
class Init_Win(Window):
    def __init__(self, parent, user_type="user", root=None):
        self.ID = "Main_Menu"
        self.ct = Comparison_Tool()
        self.user_type = user_type
        self.root = root
        super().__init__(parent)

    def build_widgets(self, fr):
        self.title = tk.Label(fr, text="Comparison Tool")
        self.title.grid(row=0, column=0)

        self.iso_comp_btn = tk.Button(fr, text="Isolated Comparison",
                                      command=lambda: self.open_win("iso_comp"))
        self.iso_comp_btn.grid(row=1, column=0)

        self.rel_comp_btn = tk.Button(fr, text="Relational Comparison",
                                      command=lambda: self.open_win("rel_comp"))
        #self.rel_comp_btn.grid(row=2, column=0)

        self.gen_stat_btn = tk.Button(fr, text="General Statistics",
                                      command=lambda: self.open_win("gen_stat"))
        self.gen_stat_btn.grid(row=3, column=0)

        if self.user_type == "admin":
            self.data_win_btn = tk.Button(fr, text="Gen Data",
                                  command=lambda: self.open_win("get_data"))
            self.data_win_btn.grid(row=4, column=0)

            self.update_nn_btn = tk.Button(fr, text="Update NN", command=self.update_nn)
            self.update_nn_btn.grid(row=5, column=0)

            self.nn_update_result_lbl = tk.Label(fr)

        self.back_btn = tk.Button(fr, text="Back", command=self.back)
        self.back_btn.grid(row=7, column=0)

    # hides the main menu and runs the next window
    def open_win(self, win_to_open):
        self.hide()
        if win_to_open == "iso_comp":
            self.isolated_comp = Iso_Win(ct=self.ct, root=self, parent=tk.Toplevel(), user_type=self.user_type)
        elif win_to_open == "rel_comp":
            self.rel_comp = Rel_Win(ct=self.ct, root=self, parent=tk.Toplevel(), user_type=self.user_type)
        elif win_to_open == "gen_stat":
            self.gen_win = Gen_Win(ct=self.ct, root=self, parent=tk.Toplevel())
        elif win_to_open == "get_data":
            self.data_win = Data_Win(ct=self.ct, root=self, parent=tk.Toplevel())

    # command for updating the nn
    # ADD TO NEA WU
    def update_nn(self):
        no_games = self.ct.update_nn()
        self.nn_update_result_lbl.grid(row=7, column=0)

        if no_games >= 50:
            update_txt = "Trained nn with {0} games".format(no_games)
        else:
            update_txt = "Need at least 50 new games to train nn"
        self.nn_update_result_lbl.config(text=update_txt)

    # goes back to login screen
    def back(self):
        self.root.show()
        self.destroy()

# isolated user comparison
# enter user name and get data about them, in isolation
class Iso_Win(Window):
    def __init__(self, ct, root, parent, user_type="user"):
        super().__init__(parent)
        self.ID = "iso_comp"
        self.ct = ct
        self.root = root
        self.default_text = True
        self.user_type = user_type

    def build_widgets(self, fr):
        self.title = tk.Label(fr, text="Isolated Comparison")
        self.title.grid(row=0, column=0)

        self.un_entry = tk.Entry(fr)
        self.un_entry.insert(0, "Enter Username here")
        self.un_entry.bind("<Button-1>", self.clear_default)
        self.un_entry.grid(row=1, column=0)

        self.build_wr = tk.Button(fr, text="Output Winrates",
                                  command=lambda: self.open_command(self.un_entry.get(), "wr"))
        self.build_wr.grid(row=2, column=0)

        self.build_ar = tk.Button(fr, text="Output Aggression",
                                  command=lambda: self.open_command(self.un_entry.get(), "ar"))
        self.build_ar.grid(row=3, column=0)

        self.back_btn = tk.Button(fr, text="Back", command=self.back)
        self.back_btn.grid(row=4, column=0)

        self.res_label = tk.Label(fr, text="")
        self.res_label.grid(row=5,column=0)

    def open_command(self, id, type):
        agent_names = [Comparison_Tool.ID_NN, Comparison_Tool.ID_CC_AI, Comparison_Tool.ID_SIMPLE, Comparison_Tool.ID_RAND_AI]
        valid_id = self.ct.db_wrapper.check_valid_id(id)
        if not valid_id or (self.user_type != "admin" and id in agent_names):
            self.res_label.config(text="User not Found")
            return False
        self.res_label.config(text="User Found")
        if type == "wr":
            self.ct.output_player_wr(id)
        elif type == "ar":
            self.ct.output_aggression_over_time(id)

    # method for clearing the entry box if default text is inside
    def clear_default(self, *args):
        if self.default_text:
            self.default_text = False
            self.un_entry.delete(0, "end")

    def back(self):
        self.root.show()
        self.destroy()

# get realtional data about two users
# currently has no implementation
class Rel_Win(Window):
    def __init__(self, ct, root, parent, user_type="user"):
        super().__init__(parent)
        self.ID = "rel_comp"
        self.ct = ct
        self.root = root
        self.user_type = user_type

        self.default_text_1 = True
        self.default_text_2 = True

    def build_widgets(self, fr):
        self.title = tk.Label(fr, text="Relational Comparison")
        self.title.grid(row=0, column=0)

        self.un1_entry = tk.Entry(fr)
        self.un1_entry.insert(0, "Enter Username 1 here")
        self.un1_entry.bind("<Button-1>", lambda *args: self.clear_default(1))
        self.un1_entry.grid(row=1, column=0)

        self.un2_entry = tk.Entry(fr)
        self.un2_entry.insert(0, "Enter Username 2 here")
        self.un2_entry.bind("<Button-1>", lambda *args: self.clear_default(2))
        self.un2_entry.grid(row=2, column=0)

        self.realtions_btn = tk.Button(fr, text="Relations") # implement the command for this
        self.realtions_btn.grid(row=3, column=0)

        self.back_btn = tk.Button(fr, text="Back", command=self.back)
        self.back_btn.grid(row=4, column=0)

        self.res_label = tk.Label(fr, text="")
        self.res_label.grid(row=5, column=0)

    def clear_default(self, entry_id, *args):
        if entry_id == 1 and self.default_text_1:
            self.default_text_1 = False
            self.un1_entry.delete(0, "end")
        elif entry_id == 2 and self.default_text_2:
            self.default_text_2 = False
            self.un2_entry.delete(0, "end")

    def back(self):
        self.root.show()
        self.destroy()

# window for general data about all users
class Gen_Win(Window):
    def __init__(self, ct, root, parent, geometry="400x400"):
        super().__init__(parent, geometry)
        self.ID = "gen_stat"
        self.ct = ct
        self.root = root

        self.output_map = {
            "hit_dist" : self.ct.output_hit_dist,
            "stand_dist" : self.ct.output_stand_dist,
            "stand_win" : self.ct.output_stand_vs_wr,
            "hit_bust" : self.ct.output_hit_vs_br,
            "aggr_win" : self.ct.output_aggression_win_relation,
            "aggr_map" : self.ct.output_aggression_scale,
            "winM_stand" : self.ct.output_win_margin_at_stand_vs_winrate
        }

    def build_widgets(self, fr):
        self.title = tk.Label(fr, text="General Stats")
        self.title.grid(row=0, column=0)

        self.stand_dist_btn = tk.Button(fr, text="Stand Value Distribution",
                                        command=lambda: self.display_dist_cmd("stand_dist"))
        self.stand_dist_btn.grid(row=1, column=0)

        self.hit_dist_btn = tk.Button(fr, text="Hit Value Distribution",
                                      command=lambda: self.display_dist_cmd("hit_dist"))
        self.hit_dist_btn.grid(row=2, column=0)

        self.stand_vs_wr_btn = tk.Button(fr, text="Win Rate Against Stand Value",
                                         command=lambda: self.display_dist_cmd("stand_win"))
        self.stand_vs_wr_btn.grid(row=3, column=0)

        self.hit_vs_bust_btn = tk.Button(fr, text="Bust Rate Against Hit Value",
                                         command=lambda: self.display_dist_cmd("hit_bust"))
        self.hit_vs_bust_btn.grid(row=4, column=0)

        self.aggr_vs_wr_btn = tk.Button(fr, text="Aggression Rating Vs Win Rate",
                                        command=lambda: self.display_dist_cmd("aggr_win"))
        self.aggr_vs_wr_btn.grid(row=5, column=0)

        # ADD THIS TO WU
        self.aggr_map_btn = tk.Button(fr, text="Aggression Rating Map",
                                      command=lambda: self.display_dist_cmd("aggr_map"))
        self.aggr_map_btn.grid(row=6, column=0)

        # ADD THIS TO WU
        self.win_margin_btn = tk.Button(fr, text="Win Margin at Stand Distribution",
                                        command=lambda: self.display_dist_cmd("winM_stand"))
        self.win_margin_btn.grid(row=7, column=0)

        self.back_btn = tk.Button(fr, text="Back", command=self.back)
        self.back_btn.grid(row=8, column=0)


    def display_dist_cmd(self, dist_type):
        if dist_type in self.output_map:
            self.output_map[dist_type]()

    def back(self):
        self.root.show()
        self.destroy()

# window for generating new data
class Data_Win(Window):
    def __init__(self, ct, root, parent, geometry="400x400"):
        super().__init__(parent, geometry)
        self.ID = "get_data"
        self.ct = ct
        self.root = root

        self.default_text = True

    def build_widgets(self, fr):
        self.title_lbl = tk.Label(fr, text="Get Data")
        self.title_lbl.grid(row=0, column=0)

        self.no_games_ent = tk.Entry(fr)
        self.no_games_ent.insert(0, "Enter num of games to play here")
        self.no_games_ent.bind("<Button-1>", self.clear_default)
        self.no_games_ent.grid(row=1, column=0)

        self.instr_lbl = tk.Label(fr, text="Tick the AI you want to use in your sample")
        self.instr_lbl.grid(row=2, column=0)

        self.nn_var = tk.IntVar()
        self.nn_check = tk.Checkbutton(fr, text="nn", variable=self.nn_var)
        self.nn_check.grid(row=3, column=0)

        self.cc_ai_var = tk.IntVar()
        self.cc_ai_check = tk.Checkbutton(fr, text="cc ai", variable=self.cc_ai_var)
        self.cc_ai_check.grid(row=4, column=0)

        self.simple_var = tk.IntVar()
        self.simple_check = tk.Checkbutton(fr, text="simple", variable=self.simple_var)
        self.simple_check.grid(row=5, column=0)

        self.rand_var = tk.IntVar()
        self.rand_check = tk.Checkbutton(fr, text="rand ai", variable=self.rand_var)
        self.rand_check.grid(row=6, column=0)

        self.begin_btn = tk.Button(fr, text="Begin", command=self.begin_sample)
        self.begin_btn.grid(row=7, column=0)

        self.back_btn = tk.Button(fr, text="Back", command=self.back)
        self.back_btn.grid(row=8, column=0)

        self.res_lbl = tk.Label(fr, text="")
        self.res_lbl.grid(row=9, column=0)

    def begin_sample(self):
        agents_playing = []
        checkboxes = [self.nn_var, self.cc_ai_var, self.simple_var, self.rand_var]
        names = [self.ct.ID_NN, self.ct.ID_CC_AI, self.ct.ID_SIMPLE, self.ct.ID_RAND_AI]

        # check checkbox state, if checked append to list of agent ids who are playing
        for i in range(len(checkboxes)):
            cbox_state = checkboxes[i].get()
            name = names[i]
            if cbox_state:
                agents_playing.append(name)
        if agents_playing == []:
            self.res_lbl.config(text="Please select at least one ai to play")
            return False

        no_games = self.no_games_ent.get()
        try:
            no_games = int(no_games)
        except:
            self.res_lbl.config(text="Please enter a valid number of games")
            return False

        if no_games < 50 or no_games > 1000:
            self.res_lbl.config(text="Please enter a valid number of games")
            return False

        self.res_lbl.config(text="Commencing testing for {0} games".format(str(no_games)))
        game_ids = self.ct.get_data(agents_playing, no_games=no_games, data_get="ids")

        first = game_ids[0]
        last = game_ids[-1]
        self.res_lbl.config(text="Data pushed: first_game={0}, last_game={1}".format(first, last))
        return True

    def clear_default(self, *args):
        if self.default_text:
            self.default_text = False
            self.no_games_ent.delete(0, "end")

    def back(self):
        self.root.show()
        self.destroy()

# Window for logging in
# allows the user to login or signup#
# TODO REMOVE THE AUTO FILL FOR ADMIN
# sample admin: admin, Pw1
# sample user: mr_aqa, Pw2
class Login_Win(Window):
    def __init__(self, parent=None, geometry="400x400"):
        super().__init__(tk.Tk(), geometry)
        self.ID = "Login"
        self.db_wrapper = Users_DB("DB/Blackjack.sqlite")
        self.uname_default = True
        self.pword_default = True


    def build_widgets(self, fr):
        self.title_lbl = tk.Label(fr, text="Login")
        self.title_lbl.grid(row=0, column=0)

        self.un_ent = tk.Entry(fr)
        self.un_ent.insert(0, "username") # todo CHANGE THIS
        self.un_ent.bind("<Button-1>", lambda *args: self.clear_default("un"))
        self.un_ent.grid(row=1, column=0)

        self.pw_ent = tk.Entry(fr, show="*")
        self.pw_ent.insert(0, "Password") # TODO CHANGE THIS
        self.pw_ent.bind("<Button-1>", lambda *args: self.clear_default("pw"))
        self.pw_ent.grid(row=2, column=0)

        self.login_btn = tk.Button(fr, text="Login", command=lambda: self.login(self.un_ent.get(), self.pw_ent.get()))
        self.login_btn.grid(row=3, column=0)

        self.signup_btn = tk.Button(fr, text="Sign up", command=lambda: self.sign_up(self.un_ent.get(), self.pw_ent.get()))
        self.signup_btn.grid(row=4, column=0)

        self.res_lbl = tk.Label(fr, text="")
        self.res_lbl.grid(row=5, column=0)

    def clear_default(self, type, *args):
        if self.uname_default and type == "un":
            self.uname_default = False
            self.un_ent.delete(0, "end")
        elif self.pword_default and type == "pw":
            self.pword_default = False
            self.pw_ent.delete(0, "end")

    def login(self, username, password):
        valid_login = self.db_wrapper.check_login(username, password)
        if not valid_login:
            self.res_lbl.config(text="Invalid Login")
            return False
        self.res_lbl.config(text="Login Successful!")
        user_type = self.db_wrapper.get_user_type(username, password)
        self.open_win(user_type)
        return True

    # creates a new user
    # todo create specific error message if signup not successful - ie pw or uname error
    # only creates users - cannot create admins
    def sign_up(self, username, password):
        result = self.db_wrapper.create_new_user(username, password, type="user")
        result_text = ""
        if result == False:
            if self.db_wrapper.sanitize_query(username) == False:
                result_text = "No sql attacks or special characters"
            else:
                result_text = "Signup Unsuccessful"
        else:
            result_text = "Signup Successful!"
        self.res_lbl.config(text=result_text)


    def open_win(self, user_type):
        self.hide()
        self.menu = Init_Win(tk.Toplevel(), user_type, root=self)


if __name__ == "__main__":
    log_win = Login_Win()
    log_win.db_wrapper.create_new_user("admin", "Pw1", type="admin")
   # print(log_win.db_wrapper.create_new_user("mr_aqa", "Pw2"))
    log_win.run()

    #g = Init_Win(tk.Tk())
    #g.run()
    #g.ct.update_nn()
