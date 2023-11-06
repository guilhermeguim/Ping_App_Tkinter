import os
import time
import datetime
from time import sleep
import time
import configparser
import tkinter as tk
import tkcalendar
import threading
from pythonping import ping
from tkinter import ttk
import concurrent.futures
import csv
import gc
import pathlib
import pandas as pd
import matplotlib.pyplot as plt


class App:
    def __init__(self):
        self.flask_process = None
        self.starting = 0
        
        self.current_path = pathlib.Path().resolve()
        self.config_path = f'{self.current_path}\Database'
        self.log_path = f'{self.current_path}\Logs'
        
        self.size_list = self.get_parameters_list_size()
        self.parameters, self.results, self.names = self.get_parameters_from_config_file()
        self.status = 'Running'
        self.scan_time = 0
        
        print(self.parameters)
        print(self.results)
        print(self.names)
        
        self.time_out = int(self.parameters.get('timeout'))
        self.wait_time = int(self.parameters.get('speed'))
        
        self.root = tk.Tk()
        
        self.create_gui()
        self.lbl_value = self.create_content()
        
        self.table = self.start_table(self.size_list)
        
        threading.Thread(target=self.ping_cycle, daemon=True).start()
        
        self.root.mainloop()

    def create_gui(self):

        self.root.title("PING TEST")
        self.root.configure(background='#053266')
        
        w = 900 # width for the Tk root
        h = 600 # height for the Tk root
        # get screen width and height
        ws = self.root.winfo_screenwidth() # width of the screen
        hs = self.root.winfo_screenheight() # height of the screen
        # calculate x and y coordinates for the Tk root window
        x = (ws/2) - (w/2)
        y = (hs/2) - (h/2)
        # set the dimensions of the screen 
        # and where it is placed
        self.root.geometry('%dx%d+%d+%d' % (w, h, x, y))
        self.root.resizable(True,True)
        
        title_text = tk.Label(text="PING TEST", bg='#053266', fg='#ffffff',font=("Arial", 20,'bold'))
        title_text.place(relx = 0.02, rely = 0.005, relwidth = 0.96, relheight = 0.07)
        self.root.update()
    
    def create_content(self):
        
        start_button = tk.Button(text='START', command=self.start_scan)
        start_button.place(relx=0.02,rely=0.08, relwidth = 0.15, relheight = 0.05)
        
        stop_button = tk.Button(text='STOP',command=self.stop_scan)
        stop_button.place(relx=0.18,rely=0.08, relwidth = 0.15, relheight = 0.05)
        
        label = 'Status: Starting' + '   |   Update Rate: ' + str(self.wait_time) + 'ms' + '   |   Scan Time: - ms'
        
        lbl_value = tk.Label(text=label,bg='white',height=50, width=50)
        lbl_value.place(relx=0,rely=0.97, relwidth = 0.4, relheight = 0.03)
        
        plotting_label = tk.Label(text='Graph Plotter',bg='#053266',fg='#ffffff',font=("Arial", 17,'bold'))
        plotting_label.place(relx=0.02,rely=0.82+0.08,relwidth = 0.18, relheight = 0.05)
        
        name_label = tk.Label(text='Select Name',bg='#053266',fg='#ffffff',height=50, width=50)
        name_label.place(relx=0.22,rely=0.87,relwidth = 0.08, relheight = 0.04)
        
        data_label = tk.Label(text='Select Date',bg='#053266',fg='#ffffff',height=50, width=50)
        data_label.place(relx=0.36,rely=0.87,relwidth = 0.1, relheight = 0.04)
        
        hour_label = tk.Label(text='Select Hour',bg='#053266',fg='#ffffff',height=50, width=50)
        hour_label.place(relx=0.49,rely=0.87,relwidth = 0.07, relheight = 0.04)
        
        parameter_label = tk.Label(text='Select Parameter',bg='#053266',fg='#ffffff',height=50, width=50)
        parameter_label.place(relx=0.61,rely=0.87,relwidth = 0.10, relheight = 0.04)
        
        name_list = self.names
        selected_name = tk.StringVar()
        selected_name.set(name_list[0])
        name_cb = ttk.Combobox(self.root, textvariable=selected_name)
        name_cb['values'] = name_list
        name_cb.place(relx=0.22 ,rely=0.91,relwidth = 0.15, relheight = 0.04)
        
        date_select =  tkcalendar.DateEntry(self.root)
        date_select.place(relx=0.38,rely=0.91, relwidth = 0.10, relheight = 0.04)
        
        hour_list = ['ALL_DAY',0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
        selected_hour =  tk.StringVar()
        selected_hour.set(hour_list[0])
        hour = ttk.Combobox(self.root, textvariable=selected_hour)
        hour['values'] = hour_list
        hour.place(relx=0.49,rely=0.91, relwidth = 0.11, relheight = 0.04)
        
        type_list = ['STATUS','LATENCY']
        selected_type =  tk.StringVar()
        selected_type.set(type_list[0])
        type_cb = ttk.Combobox(self.root, textvariable=selected_type)
        type_cb['values'] = type_list
        type_cb.place(relx=0.61 ,rely=0.91,relwidth = 0.12, relheight = 0.04)

        l_btn = tk.Button(self.root,text ="PLOT", command = lambda: self.plot_graph(selected_name.get(),date_select.get_date(),selected_hour.get(),selected_type.get()))
        l_btn.place(relx=0.74,rely=0.91,relwidth = 0.05, relheight = 0.04)
        
        return lbl_value

    def tableStyle(self):
        style = ttk.Style()

        style.theme_use('vista')
        
        style.element_create("Custom.Treeheading.border", "from", "default")
        style.layout("Custom.Treeview.Heading", [
            ("Custom.Treeheading.cell", {'sticky': 'nswe'}),
            ("Custom.Treeheading.border", {'sticky':'nswe', 'children': [
                ("Custom.Treeheading.padding", {'sticky':'nswe', 'children': [
                    ("Custom.Treeheading.image", {'side':'right', 'sticky':''}),
                    ("Custom.Treeheading.text", {'sticky':'we'})
                ]})
            ]}),
        ])
        style.configure("Custom.Treeview.Heading",
            background="white", foreground="black", relief="flat")
        style.map("Custom.Treeview.Heading",
            relief=[('active','groove'),('pressed','sunken')])
        
        style.configure('Treeview', rowheight=30)
        
        style.map("Treeview", background=[('selected', 'invalid', 'blue'),], foreground=[('selected', 'invalid', 'black')])

    def start_table(self,size):
        
        self.tableStyle()
        
        self.root.update()
        
        columns =      ('ID', 'NAME', 'IP_ADRESS','STATUS','LATENCY','LAST_LOSS')
        size_columns = (5,       100,       100,       35,   50,    100)

        tree = ttk.Treeview(self.root, columns=columns, show='headings', style="Custom.Treeview")
        tree.place(relx=0.02,rely=0.15,relwidth=0.96,relheight=0.7)
        
        tree.tag_configure('oddrow', background='#ACACAC')
        tree.tag_configure('evenrow', background='#e6e6e6')
        tree.tag_configure('mkred', background='red')
        
        for n in range(len(columns)):
            tree.heading(columns[n], text=columns[n])
            tree.column(columns[n],  width=size_columns[n], anchor=tk.CENTER)

        # generate sample data
        values = []
        for n in range(1, size):
            values.append(['-','-','-','-','-','-'])

        n = 0
        for value in values:
            n = n + 1
            if n%2 == 0:
                tree.insert('',tk.END, values=value, tags = ('oddrow',))
            else:
                tree.insert('',tk.END, values=value, tags = ('evenrow',))
            
        def item_selected(event):
            pass
                
        for i in tree.selection():
            tree.selection_remove(i)
                
        tree.bind('<<TreeviewSelect>>', item_selected)
        # add a scrollbar
        scrollbar = tk.Scrollbar(tree, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side ='right', fill ='y')
        
        return tree
    
    def ping_address(self, item):
        if self.status == 'Running':
            hostname = item.get('ip')
            time_out = self.time_out/1000
            status = 1
            
            pingstatus = ping(hostname,count=1,timeout=time_out)
            time = pingstatus.rtt_avg_ms
            
            current_datetime = datetime.datetime.now()
            formatted_datetime = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            formatted_date = current_datetime.strftime("%Y-%m-%d")
            
            if 'Request timed out' in str(pingstatus):
                status = 0
                time = 0
                
                item['last_loss'] = formatted_datetime
            else:
                status = 1
                time = pingstatus.rtt_avg_ms
            
            result = [status,time]
            
            item['result'] = result
            
            self.csv_log(item,formatted_date,formatted_datetime)
            
            return item

    def ping_cycle(self):
        
        with concurrent.futures.ThreadPoolExecutor() as executor:  #ThreadPoolExecutor faz operações concorrentes
            while True:
                if self.status == 'Running':
                    start_time = time.time()
                    
                    print("----------------------------")
                    futures = {executor.submit(self.ping_address, item): item for item in self.results}
                    for future in concurrent.futures.as_completed(futures):
                        try:
                            result = future.result()
                        except Exception as exc:
                            print(f'generated an exception: {exc}')
                        else:
                            print(f'Ping result : {result}')
                            
                    self.update_screen()
                    sleep(self.wait_time/1000)
                    end_time = time.time()
                    self.scan_time = (end_time - start_time)*1000
            
    def update_screen(self):
        i = 0
        for result in self.results:
            id_ = i + 1
            name = result.get('name')
            ip = result.get('ip')
            status = result.get('result')[0]
            if status == 1:
                status = "ON"
            elif status == 0:
                status = "OFF"
            latency = result.get('result')[1]
            last_loss = result.get('last_loss')
            result_list = [id_, name, ip,status,latency,last_loss]
            
            if status == 'OFF':
                self.table.item(self.table.get_children()[i],text="blub", values=result_list,tags = ('mkred',))
            else:
                if i%2 == 0:
                    self.table.item(self.table.get_children()[i],text="blub", values=result_list, tags = ('oddrow',))
                else:
                    self.table.item(self.table.get_children()[i],text="blub", values=result_list, tags = ('evenrow',))
            self.table.update_idletasks()
            i = i + 1
            
        label = f'Status: {str(self.status)}   |   Update Rate: {str(self.wait_time)} ms   |   Scan Time: {str(int(self.scan_time))} ms'
        if self.status == 'Running':
            self.lbl_value.config(text=label, bg="#4c9900")
        elif self.status == 'Stopped':
            self.lbl_value.config(text=label, bg="#cc0000")
        
    def get_parameters_list_size(self):
        config_path = f'{self.current_path}\config.ini'
        
        self.parameters = configparser.ConfigParser()
        self.parameters.read(config_path)

        size = len(self.parameters.sections())
        return size
    
    def get_parameters_from_config_file(self):
        
        config_path = f'{self.current_path}\config.ini'
        
        self.parameters = configparser.ConfigParser()
        self.parameters.read(config_path)

        main_parameters = dict(self.parameters.items(self.parameters.sections()[0]))
        
        sections = self.parameters.sections()[1:]
        section_content = []
        names = []
        
        for section_name in sections:
            # Obtenha os valores da seção atual como um dicionário
            section_values = dict(self.parameters.items(section_name))
            names.append(section_values['name'])
            section_values['result'] = []
            section_values['last_loss'] = '-'
            section_content.append(section_values)
            
        return main_parameters,section_content,names
        
    def stop_scan(self):
        self.status = 'Stopped'
        self.update_screen()
        
    def start_scan(self):
        self.status = 'Running'
        self.update_screen()
        
    def csv_log(self,data,formatted_date,formatted_datetime):
        file_name = f'data_{formatted_date}.csv'
        file_path = f'{self.config_path}\{file_name}'
        
        name = data['name']
        ip = data['ip']
        status = data['result'][0]            
        latency = data['result'][1]
        datetime = formatted_datetime

        with open(file_path, mode='a', newline='') as file:
            columns = ['name', 'ip', 'status', 'latency', 'datetime']
            writer = csv.DictWriter(file, fieldnames=columns)
            
            if file.tell() == 0:
                writer.writeheader()

            name = data['name']
            ip = data['ip']
            status = data['result'][0]            
            latency = data['result'][1]
            datetime = formatted_datetime
            data_dict = {'name':name,'ip':ip,'status':status,'latency':latency,'datetime':datetime}
            print(data_dict)
            writer.writerow(data_dict)
            
        if status == 0:
            log_name = f'log_{formatted_date}.csv'
            log_path = f'{self.log_path}\{log_name}'
            with open(log_path, mode='a', newline='') as file:
                columns = ['name', 'ip', 'status', 'latency', 'datetime']
                writer = csv.DictWriter(file, fieldnames=columns)
                
                if file.tell() == 0:
                    writer.writeheader()

                name = data['name']
                ip = data['ip']
                status = data['result'][0]            
                latency = data['result'][1]
                datetime = formatted_datetime
                data_dict = {'name':name,'ip':ip,'status':status,'latency':latency,'datetime':datetime}
                print(data_dict)
                writer.writerow(data_dict)
                
    def plot_graph(self, selected_name, selected_date, selected_hour, selected_type):
        print(selected_name, selected_date, selected_hour, selected_type)
        file_name = f'data_{selected_date}.csv'
        file_path = f'{self.config_path}\{file_name}'
        
        if not os.path.exists(file_path):
            print(f"File not found for {selected_date}.")
            return
        
        df = pd.read_csv(file_path)
        
        filtered_df = df[df['name'] == selected_name]
        if selected_hour != 'ALL_DAY':
            selected_hour = int(selected_hour)
            filtered_df['datetime'] = pd.to_datetime(filtered_df['datetime'])
            filtered_df = filtered_df[filtered_df['datetime'].dt.hour == selected_hour]
            
        filtered_df['datetime'] = pd.to_datetime(filtered_df['datetime']).dt.strftime('%H:%M:%S')
        print(filtered_df)

        if selected_type == 'STATUS':
            y_column = 'status'
        elif selected_type == 'LATENCY':
            y_column = 'latency'
        else:
            raise ValueError("'type' may be 'STATUS' or 'LATENCY'.")

        filtered_df['datetime'] = pd.to_datetime(filtered_df['datetime'])

        fig = plt.figure(figsize=(12, 6))
        plt.plot(filtered_df['datetime'], filtered_df[y_column], marker='o', linestyle='-',markersize=3)
        plt.title(f'Graph of {selected_type} for {selected_name} on {selected_date}')
        plt.xlabel('Time')
        plt.ylabel(type)
        plt.grid(True)
        plt.tight_layout()
        plt.show()
        plt.clear()
        plt.close(fig)
        gc.collect()
        
if __name__ == "__main__":
    app = App()