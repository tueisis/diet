from tkinter import*
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime as d
import numpy as np
from scipy import stats


def date_to_tuple(date):
    t = (date.year,date.month,date.day,date.hour,date.minute,date.second)
    return t

def tuple_to_date(t):
    date = d(t[0],t[1],t[2],t[3],t[4],t[5])
    return date

def look_for(path,default=[]):
    try:
        with open(path) as f:
            obj = f.read()
            f.close()
    except:
        print('nothing found at',path)
        obj=default
        return default
    return eval(obj)

def store_data(path,data):
    with open(path, 'w') as g:
        g.write(str(data))
        g.close()
    return

def comp_cal_eaten(eaten):
    tte=look_for('tingstoeat.txt')
    portions=look_for('portions.txt')
    nvalues = look_for('nvalues.txt', dict())
    calories = 0
    for i in eaten:
        if i[0] in tte:
            calories += nvalues[i[0]]['cal/hg']*i[1]
        elif i[0] in portions:
            calories += nvalues[i[0]]['cal']*i[1]
        else:
            top = Toplevel()
            top.title('do not know '+i[0])
            add_label = Label(top, text = 'to add to list', font = ('Helvetica', 12))
            add_label.grid(row=0,column=0)
            var=IntVar()
            Radiobutton(top, text='edible', variable=var, value=0).grid(row = 1, column = 0)
            Radiobutton(top, text='portion', variable=var, value=1).grid(row = 2, column = 0)
            cal_entry = Entry(top, font=('Helvetica', 20))
            cal_entry.grid(row=1, column=1)
            def get_cal():
                nonlocal calories
                cal_of_i = eval(cal_entry.get())
                calories += cal_of_i*i[1]
                top.destroy()
                return cal_of_i
            def the_add_func():
                nonlocal calories
                if var.get()==0:
                    tte.append(i[0])
                    tte.sort()
                    store_data('tingstoeat.txt',tte)
                    nvalues[i[0]] = {'cal/hg':eval(cal_entry.get())}
                    store_data('nvalues.txt', nvalues)
                    cal_of_i = get_cal()
                elif var.get()==1:
                    portions.append(i[0])
                    portions.sort()
                    store_data('portions.txt',portions)
                    nvalues[i[0]] = {'cal':eval(cal_entry.get())}
                    store_data('nvalues.txt', nvalues)
                    cal_of_i = get_cal()
                return
            add_button = Button(top, text='add to list', command = the_add_func)
            add_button.grid(row = 3, column = 0)
            once_label = Label(top, text = 'to just add calories', font = ('Helvetica', 12))
            once_label.grid(row=0,column=1)
            once_button = Button(top, text='add calories', command = get_cal)
            once_button.grid(row = 2, column = 1)

    return calories

def scheda_1():
    # Creazione del grafico
    # ...
    def record_weight():
        '''funzione che registra su un file la data e il peso input'''
        w_today = [date_to_tuple(d.now()),eval(w_entry.get())]

        weights = look_for('wrecord.txt')

        weights.append(w_today)

        with open('wrecord.txt', 'w') as g:
            g.write(str(weights))
            g.close()
        return
    
    def record_nrg():
        '''funzione che registra su un file la data e le calorie mangiate input'''
        nrg = look_for('nrgrecord.txt')

        nrg.append([date_to_tuple(d.now()),eval(nrg_entry.get())])

        with open('nrgrecord.txt', 'w') as g:
            g.write(str(nrg))
            g.close()
        return

    def get_w():
        dates = []
        w = []
        wrec = look_for('wrecord.txt')
        for i in wrec:
            date=d(i[0][0],i[0][1],i[0][2],i[0][3]) -d(wrec[0][0][0],wrec[0][0][1],wrec[0][0][2],wrec[0][0][3])
            dates.append(date.total_seconds()/(3600*24))
            w.append(i[1])
        add_plot(np.array(dates),np.array(w))
        return np.array(dates),np.array(w)
    
    def add_plot(x, y):
        fig = plt.Figure(figsize = (4, 4))
        splot = fig.add_subplot(111)
        splot.plot(y)
        canvas = FigureCanvasTkAgg(fig, master = root)  
        canvas.draw()
        canvas.get_tk_widget().grid(column=2)
        return
    
    for widg in root.winfo_children():
        widg.grid_forget()
    
    w_button = Button(root, text = 'record weight today', command = record_weight)
    w_button.grid(row=2,column=0)

    nrg_lable = Label(root, text='eaten calories today', font=('Helvetica', 15))
    nrg_lable.grid(row = 0, column = 1)

    nrg_entry = Entry(root, font=('Helvetica', 20))
    nrg_entry.grid(row=1, column=1)
    nrg_entry.insert(0,calories)
    
    w_lable = Label(root, text='weight today', font=('Helvetica', 15))
    w_lable.grid(row = 0, column = 0)

    w_entry = Entry(root, font=('Helvetica', 20))
    w_entry.grid(row=1, column=0)
    # Creazione del bottone
    button_1 = Button(root, text="Vai alla scheda 2", command=scheda_2)
    button_1.grid(row=3, column=3)
    
    nrg_button = Button(root, text = 'record calories today', command = record_nrg)
    nrg_button.grid(row=2,column=1)
    
    eaten_lists[-1][1] = eaten_list
    store_data('eaten_lists.txt',eaten_lists)
    
    gra = get_w()
    s = stats.linregress(gra[0],gra[1])
    s_label = Label(root, text=
                    str(" A = %.2f" % s[1])+'('+str("%.2f" % s.intercept_stderr)+') B = ' + 
                    str(" B = %.3f" % s[0])+'('+str("%.3f" % s.stderr)+')' , font=('Helvetica', 15))
    s_label.grid(row = 3, column = 0)
    
    nrgs = look_for('nrgrecord.txt')
    nrgs = [i[1] for i in nrgs]
    balance = s[0]*8000
    print(balance)
    fab_label = Label(root, text = 'mean eaten ' + str('%.2f' % np.mean(nrgs))+
                      ' \n balance '+ str("%.3f" % balance), font=('Helvetica', 15))
    fab_label.grid(row = 4, column = 0)

# Funzione per la seconda scheda
def scheda_2():
    # Creazione della lista
    # ...
    for widg in root.winfo_children():
        widg.grid_forget()
    # Creazione del bottone
    food_lable = Label(root, text='name of food ', font=('Helvetica', 15))
    food_lable.grid(row = 0, column = 0)

    food_entry = Entry(root, font=('Helvetica', 14))
    food_entry.grid(row=1, column=0)

    listed = Listbox(root, width = 40)
    listed.grid(row=2, column=0)

    def check(e):
        typed = the_entry.get()
        options.delete(0,END)
        if typed == '':
            for i in the_list:
                options.insert(END,i)
        else:
            for i in the_list:
                if typed.lower() in i.lower(): options.insert(END,i)
        return

    def fillout(e):
        the_entry.delete(0,END)
        the_entry.insert(0,options.get(ACTIVE))
        return

    food_entry.bind('<KeyRelease>', check)
    listed.bind('<<ListboxSelect>>', fillout)

    q_label = Label(root, text = 'eaten quantity', font = ('Helvetica, 15'))
    q_label.grid(row=0, column=1)

    q_entry = Entry(root, font=('Helvetica', 14))
    q_entry.grid(row=1, column=1)
    button_2 = Button(root, text="Torna alla scheda 1", command=scheda_1)
    button_2.grid(row=3, column=3)
    
    input_list = Listbox(root, width = 30)
    input_list.grid(row=2, column=2)

    def partial_cal(e):
        f = food_entry.get()
        q = q_entry.get()
        if q == '': q=0
        else: q=eval(q)
        if f in nvalues:
            if f in tte:
                cal = nvalues[f]['cal/hg']*q
            elif f in portions:
                cal = nvalues[f]['cal']*q
            message = 'adding '+str(cal)+' to calories'
            if root.grid_slaves(row=2, column=1)==[]:
                Label(root, text=message, font=('Helvetica', 15)).grid(row=2,column=1)
            else:
                root.grid_slaves(row=2, column=1)[0].grid_forget()
                Label(root, text=message, font=('Helvetica', 15)).grid(row=2,column=1)
            
        return

    q_entry.bind('<KeyRelease>', partial_cal)
    
    def add_to_eaten():
        #basically this takes a list of food and quantities and add to if the food and quantity you input
        global calories

        food = food_entry.get()
        quantity = q_entry.get()
        eaten_list.append([food,eval(quantity)])
        to_insert = quantity+' of '+food
        calories = comp_cal_eaten(eaten_list)
        input_list.delete(0,END)
        input_list.insert(END,'you ate today')
        for i in eaten_list:
            input_list.insert(END,str(i[1])+' of '+str(i[0]))
        input_list.insert(END,'so in total were eaten '+str(calories)+' kcal')
        return


    tte=look_for('tingstoeat.txt')
    portions=look_for('portions.txt')
    nvalues = look_for('nvalues.txt', dict())
    the_list=tte+portions
    the_entry=food_entry
    options=listed
    for i in the_list:
        options.insert(END,i)

    input_list.insert(END,'you ate today')
    for i in eaten_list:
        input_list.insert(END,str(i[1])+' of '+str(i[0]))
    if eaten_list==[]:
        input_list.insert(END,'nothing :(')
    else:
        input_list.insert(END,'so in total were eaten '+str(calories)+' kcal')

    the_button = Button(root, text='add', command = add_to_eaten)
    the_button.grid(row=1, column=2)



if __name__ == "__main__":
    # Creazione della finestra principale
    root = Tk()
    
    date_today = d.now()
    
    eaten_lists=look_for('eaten_lists.txt',[[(date_today.year,date_today.month,date_today.day),[]]])

    if (date_today.year,date_today.month,date_today.day) == eaten_lists[-1][0]:
        eaten_list = eaten_lists[-1][1]
    else:
        eaten_list = []
        eaten_lists.append([(date_today.year,date_today.month,date_today.day),[]])

    calories = comp_cal_eaten(eaten_list)

    # Impostazione del layout
    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)

    # Visualizzazione della prima scheda
    scheda_1()

    # Avvio del mainloop
    root.mainloop()
